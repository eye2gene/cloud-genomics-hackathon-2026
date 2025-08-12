# Debugging guide

Practical notes for when a Nextflow-on-AWS-Batch run misbehaves: where each component logs, how to
inspect the compute instances over **AWS Systems Manager (SSM)**, and fixes for the issues we've
actually hit. There's a helper script — [`scripts/nf-debug.sh`](./scripts/nf-debug.sh) — that wraps
the common commands; each section shows both the script shortcut and the raw AWS CLI it runs.

## Setup

Everything below needs working AWS credentials for the target account and the right region/namespace.

```bash
export AWS_REGION=eu-west-2                 # your region
export NF_NAMESPACE=cdk-nfbatch-eu-west-2   # your `namespace` context value
# export AWS_PROFILE=your-profile           # if you use a named profile
```

For the interactive `ssm` shell you also need the **Session Manager plugin** for the AWS CLI
([install docs](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)).
The compute-instance IAM role already includes `AmazonSSMManagedInstanceCore`, so nodes register with
SSM automatically — no SSH keys, no open inbound ports.

## The helper script

```bash
scripts/nf-debug.sh status                 # CE + queue health — check this first
scripts/nf-debug.sh jobs [ondemand|spot]   # recent jobs on a queue (default: both)
scripts/nf-debug.sh job   <job-id>         # one job's status + failure reason
scripts/nf-debug.sh logs  <job-id>         # a job's CloudWatch logs (head or child)
scripts/nf-debug.sh instances              # compute instances + ECS registration
scripts/nf-debug.sh bootstrap-logs <i-id>  # a node's cloud-init/ecs logs from CloudWatch
scripts/nf-debug.sh ssm   <instance-id>    # interactive shell on a node (Session Manager)
scripts/nf-debug.sh diag  <instance-id>    # canned bootstrap/ECS diagnostics over SSM
scripts/nf-debug.sh build-logs             # latest head-node image build (CodeBuild)
```

## Where each component logs

Names below assume `<ns>` = your `NF_NAMESPACE`.

| Component | Where it logs | How to read it |
| --- | --- | --- |
| **Head node** (Nextflow driver) | CloudWatch `/aws/batch/job`, stream `nextflow-<ns>/default/<hash>` | `nf-debug.sh logs <job-id>` |
| **Child process jobs** | CloudWatch `/aws/batch/job`, one stream per job | `nf-debug.sh logs <child-job-id>` |
| **Compute instance bootstrap** (cloud-init, ECS agent) | CloudWatch `/aws/ecs/container-instance/<ns>/<instance-id>/{cloud-init-output,ecs-agent,ecs-init,...}.log` **and** on-box via SSM | `nf-debug.sh bootstrap-logs <i-id>` or `nf-debug.sh diag <i-id>` |
| **Head-node image build** | CloudWatch `/aws/codebuild/nextflow-image-build-<ns>` | `nf-debug.sh build-logs` |
| **Image-build trigger** | CloudWatch `/aws/lambda/nextflow-image-build-trigger-<ns>` | AWS console / `aws logs tail` |
| **Compute-env / queue status** | AWS Batch control plane (not a log) | `nf-debug.sh status` |

> The bootstrap logs land in CloudWatch **only after** the CloudWatch agent starts. If a node dies
> very early (or never finishes cloud-init), CloudWatch may be empty — use `diag`/`ssm` to look on the
> box directly while it's still alive.

## First-response playbook

1. **`scripts/nf-debug.sh status`** — are both compute environments `VALID/ENABLED`? Is `ECS
   registered` non-zero when jobs are pending? A non-empty `statusReason` on an `INVALID` CE usually
   says exactly what's wrong.
2. **`scripts/nf-debug.sh job <job-id>`** — `statusReason` / `container.exitCode` tell you whether it
   was a pipeline error, a host termination, or still waiting.
3. **`scripts/nf-debug.sh logs <job-id>`** — the actual Nextflow / task output.
4. If nodes aren't registering: **`instances`**, then **`diag <instance-id>`** on a live one.

## Common issues

### Jobs stuck in `RUNNABLE` forever

The queue accepts the job but it never starts. Almost always the compute environment can't put a
usable instance into its ECS cluster.

```bash
scripts/nf-debug.sh status        # look at Status + statusReason + "ECS registered"
scripts/nf-debug.sh instances     # are instances launching? registering?
```

- **CE is `INVALID`** with *"none of the instances joined the underlying ECS Cluster"* → the launch
  template / bootstrap is preventing the ECS agent from starting (see next item). **An INVALID managed
  CE does not self-recover even after you fix the cause** — you must replace it. This repo's pattern is
  to bump the `computeEnvironmentName` suffix (`-vN`) in `lib/batch-stack.ts` and redeploy, which
  forces CloudFormation to create a fresh CE.
- **CE is `VALID` but `ECS registered = 0`** and instances are cycling (launch → ~10 min → terminate →
  relaunch) → same root cause, caught earlier. SSH in with `diag` before the node cycles.
- **Gotcha — AWS Batch caches the launch-template `$Latest` version per CE.** After you fix the launch
  template, *existing* CEs keep launching the old version until they're replaced (bump `-vN`). A newly
  created CE picks up the fix; an older one won't.

### Instances launch, run cloud-init, then never join ECS (or self-terminate)

Symptoms: `diag` shows `ecs.service` **inactive/waiting**, `cloud-final.service` **still running** for
many minutes, and no `runcmd` output. This is a **cloud-init deadlock**: a `runcmd` step is hanging, and
`ecs.service` is ordered `After=cloud-final.service`, so the ECS agent can never start.

- **Never `systemctl restart ecs` inside the launch-template `runcmd`** — it waits for the agent, which
  can't start until `cloud-final` (the thing running the restart) finishes. Set `ecs.config` values from
  cloud-init **`bootcmd`** (runs before the agent) instead.
- Check with `diag <i-id>`; look at `===STUCK-SYSTEMD-JOBS===` and `===RUNCMD-STILL-RUNNING?===`.

### Head node runs, but the pipeline fails immediately

- **`Local executor requires the use of POSIX compatible file system — offending path: s3://…`** → the
  head container isn't configured for the AWS Batch executor (it fell back to `local`). The built image's
  entrypoint must generate a `nextflow.config` with `process.executor = 'awsbatch'`. Check the head
  logs (`nf-debug.sh logs <job-id>`) and the image (`docker/nextflow-head/nextflow.aws.sh`).
- **`Expected a command, got nf-core/sarek`** → the submit command must **not** include `run`; the
  container entrypoint prepends `nextflow run`. Pass `["nf-core/sarek", ...]`, not `["run", ...]`.

### Head runs but child jobs never run (stuck on the Spot queue)

Head node is `RUNNING`, but child process jobs sit `RUNNABLE` on the Spot queue.

```bash
scripts/nf-debug.sh status        # is the Spot CE VALID? ECS registered > 0?
scripts/nf-debug.sh jobs spot
```

Usually the Spot CE has the same bootstrap problem as above, or it cached a broken launch-template
version — replace it (bump `-vN`) after confirming the launch template is good.

### Host `Client.UserInitiatedShutdown` / job fails with "Host EC2 … terminated"

The instance shut itself down (often a failed check in `runcmd`, e.g. `command -v aws || shutdown -P
now`) or Batch terminated an unhealthy node. Check `bootstrap-logs`/`diag` for how far cloud-init got.

### Image build problems (`buildNextflowImage: true`)

```bash
scripts/nf-debug.sh build-logs    # CodeBuild status + log tail
```

The build is kicked by a Lambda-backed custom resource on deploy; a content-hash property forces a
rebuild when the Dockerfile or entrypoint changes. If a code change to the image doesn't take effect,
confirm the build actually re-ran (the hash changed) and pushed a new `latest`.

## Using SSM directly

The script's `ssm`/`diag`/`bootstrap-logs` wrap these — useful to know for ad-hoc digging.

**Interactive shell on a node** (no SSH, no bastion):

```bash
aws ssm start-session --target <instance-id> --region "$AWS_REGION"
```

**Run a one-off command on a node** and read the output:

```bash
CID=$(aws ssm send-command --instance-ids <instance-id> \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["systemctl is-active ecs","cat /etc/ecs/ecs.config"]' \
  --query 'Command.CommandId' --output text)
aws ssm get-command-invocation --command-id "$CID" --instance-id <instance-id> \
  --query 'StandardOutputContent' --output text
```

**What to check on a compute instance:**

| Question | Command on the box |
| --- | --- |
| Is the ECS agent running? | `systemctl is-active ecs` (should be `active`) |
| Which cluster is it joining? | `cat /etc/ecs/ecs.config` (look for `ECS_CLUSTER=`) |
| Is the agent healthy? | `curl -s http://localhost:51678/v1/metadata` |
| Did cloud-init finish? | `cloud-init status --long` (`done` vs `running`) |
| Is something blocking startup? | `systemctl list-jobs` (look for `waiting`/`running`) |
| Where did the bootstrap stop? | `tail -n 50 /var/log/cloud-init-output.log` |

**Find a node to target:** `scripts/nf-debug.sh instances`, or the EC2 console filtered by tag
`Name = <ns>-compute-instance`.

## Resource-name quick reference

Derived from `NF_NAMESPACE` (`<ns>`) and `groupName`:

| Resource | Name |
| --- | --- |
| On-Demand queue | `OnDemand-<ns>` |
| Spot queue | `Spot-<ns>` |
| Compute environments | `ondemand-<ns>-vN` / `spot-<ns>-vN` (N bumps on forced replacement) |
| Head-node job definition | `nextflow-<ns>` |
| Head-node ECR repo | `nextflow-head-<ns>` |
| Job log group | `/aws/batch/job` |
| Instance log group | `/aws/ecs/container-instance/<ns>` |
| Image-build project | `nextflow-image-build-<ns>` |
| Work/results bucket | `<groupName>-<ns>-<account-id>` (or your `s3BucketName`) |
