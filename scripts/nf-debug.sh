#!/usr/bin/env bash
#
# nf-debug.sh — debugging helper for the Nextflow-on-AWS-Batch stack.
#
# Wraps the common AWS CLI incantations you need when a run misbehaves: compute
# environment / queue health, job logs, compute-instance inspection over SSM, and
# the image-build logs. See DEBUGGING.md for the "why" behind each command.
#
# Config (env vars, with defaults):
#   NF_NAMESPACE   Batch namespace                 (default: cdk-nfbatch-eu-west-2)
#   AWS_REGION     region                          (default: eu-west-2)
#   AWS_PROFILE    profile, if you use one         (respected if set)
#
# Usage:
#   scripts/nf-debug.sh status                 CE + queue health (the first thing to check)
#   scripts/nf-debug.sh jobs [ondemand|spot]   recent jobs on a queue (default: both)
#   scripts/nf-debug.sh job   <job-id>         one job's status + failure reason
#   scripts/nf-debug.sh logs  <job-id>         a job's CloudWatch logs (head or child)
#   scripts/nf-debug.sh instances              compute instances + ECS registration
#   scripts/nf-debug.sh bootstrap-logs <i-id>  a node's cloud-init/ecs logs from CloudWatch
#   scripts/nf-debug.sh ssm   <instance-id>    interactive shell on a node (Session Manager)
#   scripts/nf-debug.sh diag  <instance-id>    run canned bootstrap/ECS diagnostics over SSM
#   scripts/nf-debug.sh build-logs             latest head-node image build (CodeBuild)
#
# No `set -e`: this is a diagnostic tool that makes many "may-not-exist" AWS calls and should
# keep going (and print what it can) rather than abort on the first missing resource.
set -uo pipefail

NS="${NF_NAMESPACE:-cdk-nfbatch-eu-west-2}"
export AWS_REGION="${AWS_REGION:-eu-west-2}"
export AWS_DEFAULT_REGION="$AWS_REGION"

OD_QUEUE="OnDemand-${NS}"
SPOT_QUEUE="Spot-${NS}"
JOB_LOG_GROUP="/aws/batch/job"
INSTANCE_LOG_GROUP="/aws/ecs/container-instance/${NS}"
BUILD_PROJECT="nextflow-image-build-${NS}"

aws() { command aws --output "${AWS_OUTPUT:-json}" "$@"; }
hr()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
die() { echo "error: $*" >&2; exit 1; }

# Resolve the compute-environment ARN a queue currently points at (version-agnostic:
# the CE name carries a -vN suffix that changes on forced replacements).
ce_for_queue() {
  aws batch describe-job-queues --job-queues "$1" \
    --query 'jobQueues[0].computeEnvironmentOrder[0].computeEnvironment' --output text 2>/dev/null
}
ecs_cluster_for_ce() {
  aws batch describe-compute-environments --compute-environments "$1" \
    --query 'computeEnvironments[0].ecsClusterArn' --output text 2>/dev/null
}

cmd_status() {
  hr "Job queues ($NS)"
  AWS_OUTPUT=table aws batch describe-job-queues --job-queues "$OD_QUEUE" "$SPOT_QUEUE" \
    --query 'jobQueues[].{Queue:jobQueueName,State:state,Status:status,CE:computeEnvironmentOrder[0].computeEnvironment}' 2>/dev/null \
    || echo "queues not found — is NF_NAMESPACE correct? ($NS)"
  for q in "$OD_QUEUE" "$SPOT_QUEUE"; do
    local ce; ce="$(ce_for_queue "$q")"
    if [ -z "$ce" ] || [ "$ce" = "None" ]; then continue; fi
    hr "Compute env behind $q"
    AWS_OUTPUT=table aws batch describe-compute-environments --compute-environments "$ce" \
      --query 'computeEnvironments[].{Name:computeEnvironmentName,State:state,Status:status,Min:computeResources.minvCpus,Desired:computeResources.desiredvCpus,Max:computeResources.maxvCpus}'
    # statusReason is where INVALID CEs explain themselves — print it in full.
    local reason; reason="$(aws batch describe-compute-environments --compute-environments "$ce" \
      --query 'computeEnvironments[0].statusReason' --output text)"
    echo "  statusReason: $reason"
    local cluster; cluster="$(ecs_cluster_for_ce "$ce")"
    local reg; reg="$(aws ecs describe-clusters --clusters "$cluster" \
      --query 'clusters[0].registeredContainerInstancesCount' --output text 2>/dev/null)"
    echo "  ECS registered container instances: ${reg:-?}   (0 with pending jobs ⇒ nodes aren't joining ECS)"
  done
}

cmd_jobs() {
  local which="${1:-both}" queues=()
  case "$which" in
    ondemand|od) queues=("$OD_QUEUE") ;;
    spot)        queues=("$SPOT_QUEUE") ;;
    both|*)      queues=("$OD_QUEUE" "$SPOT_QUEUE") ;;
  esac
  for q in "${queues[@]}"; do
    hr "Jobs on $q"
    for st in SUBMITTED PENDING RUNNABLE STARTING RUNNING SUCCEEDED FAILED; do
      local n; n="$(aws batch list-jobs --job-queue "$q" --job-status "$st" \
        --query 'length(jobSummaryList)' --output text 2>/dev/null || echo 0)"
      [ "${n:-0}" -gt 0 ] && printf '  %-10s %s\n' "$st" "$n"
    done
    AWS_OUTPUT=table aws batch list-jobs --job-queue "$q" --job-status RUNNING \
      --query 'jobSummaryList[0:10].{Name:jobName,Id:jobId,Status:status}' 2>/dev/null || true
  done
}

cmd_job() {
  [ $# -ge 1 ] || die "usage: job <job-id>"
  AWS_OUTPUT=json aws batch describe-jobs --jobs "$1" \
    --query 'jobs[].{Status:status,StatusReason:statusReason,ExitCode:container.exitCode,ContainerReason:container.reason,Queue:jobQueue,LogStream:container.logStreamName,Started:startedAt,Stopped:stoppedAt}'
}

cmd_logs() {
  [ $# -ge 1 ] || die "usage: logs <job-id>"
  local ls; ls="$(aws batch describe-jobs --jobs "$1" \
    --query 'jobs[0].container.logStreamName' --output text 2>/dev/null)"
  [ -n "$ls" ] && [ "$ls" != "None" ] || die "no log stream for job $1 (has it started yet?)"
  echo "log group : $JOB_LOG_GROUP"
  echo "log stream: $ls"; hr "events"
  aws logs get-log-events --log-group-name "$JOB_LOG_GROUP" --log-stream-name "$ls" \
    --query 'events[].message' --output text | tr '\t' '\n'
}

cmd_instances() {
  for q in "$OD_QUEUE" "$SPOT_QUEUE"; do
    local ce cluster; ce="$(ce_for_queue "$q")"
    if [ -z "$ce" ] || [ "$ce" = "None" ]; then continue; fi
    cluster="$(ecs_cluster_for_ce "$ce")"
    hr "$q — ECS cluster $(basename "$cluster")"
    local arns; arns="$(aws ecs list-container-instances --cluster "$cluster" \
      --query 'containerInstanceArns' --output text 2>/dev/null || true)"
    if [ -n "$arns" ] && [ "$arns" != "None" ]; then
      AWS_OUTPUT=table aws ecs describe-container-instances --cluster "$cluster" --container-instances $arns \
        --query 'containerInstances[].{Ec2:ec2InstanceId,Status:status,Running:runningTasksCount,AgentConnected:agentConnected}'
    else
      echo "  no registered container instances"
    fi
  done
  hr "EC2 instances tagged for this stack (any state, last hour)"
  AWS_OUTPUT=table aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=${NS}-compute-instance" \
    --query 'Reservations[].Instances[].{Id:InstanceId,State:State.Name,Type:InstanceType,Launched:LaunchTime}' 2>/dev/null \
    || echo "  none"
}

cmd_bootstrap_logs() {
  [ $# -ge 1 ] || die "usage: bootstrap-logs <instance-id>"
  local id="$1"
  # The CloudWatch agent names each stream with the full path, not just <id>/<file>.
  echo "CloudWatch group: $INSTANCE_LOG_GROUP  (streams: $INSTANCE_LOG_GROUP/$id/<file>)"
  for f in cloud-init-output.log ecs-agent.log ecs-init.log cloud-init.log; do
    hr "$f"
    aws logs get-log-events --log-group-name "$INSTANCE_LOG_GROUP" \
      --log-stream-name "${INSTANCE_LOG_GROUP}/${id}/${f}" --query 'events[-40:].message' --output text 2>/dev/null | tr '\t' '\n' \
      || echo "  (no stream for ${id}/${f} — instance may still be booting, or logs not shipped yet)"
  done
}

cmd_ssm() {
  [ $# -ge 1 ] || die "usage: ssm <instance-id>   (needs the Session Manager plugin)"
  echo "Starting Session Manager shell on $1 ..."
  exec command aws ssm start-session --target "$1" --region "$AWS_REGION"
}

cmd_diag() {
  [ $# -ge 1 ] || die "usage: diag <instance-id>"
  local id="$1"
  echo "Running bootstrap/ECS diagnostics on $id over SSM ..."
  local cid
  cid="$(aws ssm send-command --instance-ids "$id" --document-name "AWS-RunShellScript" \
    --timeout-seconds 60 \
    --parameters 'commands=[
      "echo ===CLOUD-INIT===", "cloud-init status --long 2>&1 | head -6",
      "echo ===ECS-SERVICE===", "systemctl is-active ecs; systemctl is-enabled ecs",
      "echo ===ECS-CONFIG===", "cat /etc/ecs/ecs.config 2>&1",
      "echo ===ECS-AGENT===", "curl -s --max-time 5 http://localhost:51678/v1/metadata 2>&1 || echo NO_AGENT_RESPONSE",
      "echo ===STUCK-SYSTEMD-JOBS===", "systemctl list-jobs --no-pager 2>&1",
      "echo ===RUNCMD-STILL-RUNNING?===", "pgrep -af cloud-init 2>/dev/null | head; tail -n 6 /var/log/cloud-init-output.log 2>&1"
    ]' --query 'Command.CommandId' --output text)"
  # poll for completion
  local st=""
  for _ in $(seq 1 12); do
    st="$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$id" \
      --query 'Status' --output text 2>/dev/null || true)"
    [ "$st" = "Success" ] || [ "$st" = "Failed" ] || [ "$st" = "TimedOut" ] && break
    sleep 5
  done
  hr "diagnostics ($st)"
  aws ssm get-command-invocation --command-id "$cid" --instance-id "$id" \
    --query 'StandardOutputContent' --output text 2>&1
}

cmd_build_logs() {
  hr "Latest image build ($BUILD_PROJECT)"
  local bid; bid="$(aws codebuild list-builds-for-project --project-name "$BUILD_PROJECT" \
    --query 'ids[0]' --output text 2>/dev/null)"
  [ -n "$bid" ] && [ "$bid" != "None" ] || die "no builds for $BUILD_PROJECT"
  AWS_OUTPUT=json aws codebuild batch-get-builds --ids "$bid" \
    --query 'builds[].{Status:buildStatus,Phase:currentPhase,Start:startTime,Log:logs.deepLink}'
  local grp strm
  grp="$(aws codebuild batch-get-builds --ids "$bid" --query 'builds[0].logs.groupName' --output text)"
  strm="$(aws codebuild batch-get-builds --ids "$bid" --query 'builds[0].logs.streamName' --output text)"
  [ -n "$grp" ] && [ "$grp" != "None" ] && { hr "log tail"; \
    aws logs get-log-events --log-group-name "$grp" --log-stream-name "$strm" \
      --query 'events[-40:].message' --output text 2>/dev/null | tr '\t' '\n'; }
}

main() {
  local cmd="${1:-help}"; shift || true
  case "$cmd" in
    status)          cmd_status "$@" ;;
    jobs)            cmd_jobs "$@" ;;
    job)             cmd_job "$@" ;;
    logs)            cmd_logs "$@" ;;
    instances)       cmd_instances "$@" ;;
    bootstrap-logs)  cmd_bootstrap_logs "$@" ;;
    ssm)             cmd_ssm "$@" ;;
    diag)            cmd_diag "$@" ;;
    build-logs)      cmd_build_logs "$@" ;;
    help|-h|--help)  sed -n '2,32p' "$0" ;;
    *)               echo "unknown command: $cmd"; sed -n '2,32p' "$0"; exit 1 ;;
  esac
}
main "$@"
