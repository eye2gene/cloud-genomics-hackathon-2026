#!/bin/bash
# $1    Nextflow project. Can be an S3 URI, or git repo name.
# $2..  Additional parameters passed on to the nextflow cli

# using nextflow needs the following locations/directories provided as
# environment variables to the container
#  * NF_LOGSDIR: where caching and logging data are stored
#  * NF_WORKDIR: where intermmediate results are stored

set -e  # fail on any error

DEFAULT_AWS_CLI_PATH=/opt/aws-cli/bin/aws
AWS_CLI_PATH=${JOB_AWS_CLI_PATH:-$DEFAULT_AWS_CLI_PATH}

echo "=== ENVIRONMENT ==="
printenv

echo "=== RUN COMMAND ==="
echo "$@"

NEXTFLOW_PROJECT=$1
shift
NEXTFLOW_PARAMS="$@"
AWS_REGION="${AWS_REGION:-eu-west-2}"

# AWS Batch places multiple jobs on an instance
# To avoid file path clobbering use the JobID and JobAttempt
# to create a unique path. This is important if /opt/work
# is mapped to a filesystem external to the container
GUID="$AWS_BATCH_JOB_ID/$AWS_BATCH_JOB_ATTEMPT"

if [ "$GUID" = "/" ]; then
    GUID=`date | md5sum | cut -d " " -f 1`
fi

mkdir -p /opt/work/$GUID
cd /opt/work/$GUID

# Handle nextflow configuration
NF_CONFIG=./nextflow.config

if [ -f "$NF_CONFIG" ]; then
    echo "Found existing nextflow.config, appending AWS Batch runtime settings"
    # Append only the runtime settings that can't be in profiles
    cat << EOF >> $NF_CONFIG

// AWS Batch runtime settings (always overrides any profile settings)
workDir = "$NF_WORKDIR"
process.executor = "awsbatch"
process.containerOptions = "-u 0:0 -e LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/opt/aws-cli/bin -e MALLOC_ARENA_MAX=2 -e AWS_MAX_ATTEMPTS=5"
process.queue = "$NF_JOB_QUEUE"
aws.batch.cliPath = "$AWS_CLI_PATH"
aws.region = "$AWS_REGION"
aws.batch.maxSpotAttempts = 5
EOF
else
    echo "No existing config found, creating basic AWS Batch config"
    cat << EOF > $NF_CONFIG
workDir = "$NF_WORKDIR"
process.executor = "awsbatch"
process.containerOptions = "-u 0:0 -e LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/opt/aws-cli/bin -e MALLOC_ARENA_MAX=2 -e AWS_MAX_ATTEMPTS=5"
process.queue = "$NF_JOB_QUEUE"
aws.batch.cliPath = "$AWS_CLI_PATH"
aws.region = "$AWS_REGION"
aws.batch.maxSpotAttempts = 5
EOF
fi

if [[ "$EFS_MOUNT" != "" ]]
then
    echo aws.batch.volumes = [\"/mnt/efs\"] >> $NF_CONFIG
fi

echo "=== CONFIGURATION ==="
cat ./nextflow.config

# stage in session cache
# .nextflow directory holds all session information for the current and past runs.
# it should be `sync`'d with an s3 uri, so that runs from previous sessions can be
# resumed
echo "== Restoring Session Cache =="
aws s3 sync --no-progress $NF_LOGSDIR/.nextflow .nextflow

function preserve_session() {
    # stage out session cache
    if [ -d .nextflow ]; then
        echo "== Preserving Session Cache =="
        aws s3 sync --no-progress .nextflow $NF_LOGSDIR/.nextflow
    fi

    # .nextflow.log file has more detailed logging from the workflow run and is
    # nominally unique per run.
    #
    # when run locally, .nextflow.logs are automatically rotated
    # when syncing to S3 uniquely identify logs by the batch GUID
    if [ -f .nextflow.log ]; then
        echo "== Preserving Session Log =="
        aws s3 cp --no-progress .nextflow.log $NF_LOGSDIR/.nextflow.log.${GUID/\//.}
    fi
}

function show_log() {
    echo "=== Nextflow Log ==="
    cat ./.nextflow.log
}

function cleanup() {
    set +e
    wait $NEXTFLOW_PID
    set -e
    echo "=== Running Cleanup ==="

    show_log
    preserve_session

    echo "=== Bye! ==="
}

function cancel() {
    # AWS Batch sends a SIGTERM to a container if its job is cancelled/terminated
    # forward this signal to Nextflow so that it can cancel any pending workflow jobs

    set +e  # ignore errors here
    echo "=== !! CANCELLING WORKFLOW !! ==="
    echo "stopping nextflow pid: $NEXTFLOW_PID"
    kill -TERM "$NEXTFLOW_PID"
    echo "waiting .."
    wait $NEXTFLOW_PID
    echo "=== !! cancellation complete !! ==="
    set -e
}

trap "cancel; cleanup" TERM
trap "cleanup" EXIT

# stage workflow definition
if [[ "$NEXTFLOW_PROJECT" =~ ^s3://.* ]]; then
    echo "== Staging S3 Project =="
    aws s3 sync --no-progress --exclude 'runs/*' --exclude '.*' $NEXTFLOW_PROJECT ./project
    NEXTFLOW_PROJECT=./project
# else if the project is a git repo or a git link clone it
elif [[ "$NEXTFLOW_PROJECT" =~ ^https?://github\.com/.*\.git$ ]] || [[ "$NEXTFLOW_PROJECT" =~ ^git@ ]]; then
    echo "== Cloning Git Project =="
    git clone "$NEXTFLOW_PROJECT" ./project
    NEXTFLOW_PROJECT=./project
fi

echo "== Running Workflow =="
echo "nextflow run $NEXTFLOW_PROJECT $NEXTFLOW_PARAMS"
export NXF_ANSI_LOG=false
nextflow run $NEXTFLOW_PROJECT $NEXTFLOW_PARAMS &

NEXTFLOW_PID=$!
echo "nextflow pid: $NEXTFLOW_PID"
jobs
echo "waiting .."
wait $NEXTFLOW_PID
