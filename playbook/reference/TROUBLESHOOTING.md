# Troubleshooting Guide

## Spot Instance Interruptions

### Symptoms
- Multiple tasks fail simultaneously
- ASG shows: "instance was taken out of service in response to an EC2 health check indicating it has been terminated or stopped"
- Tasks were running for a few minutes before failing (not immediate failure)

### How to Confirm

**EC2 Console:**
1. Go to EC2 → Instances
2. Find the terminated instance(s)
3. Check **State transition message**: `Server.SpotInstanceTermination: Spot instance termination`

**CLI:**
```bash
# Check instance termination reason
aws ec2 describe-instances --instance-ids <INSTANCE_ID> --region eu-west-2 --query 'Reservations[].Instances[].StateReason.Message'
```

**CloudTrail:**
```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=BidEvictedEvent --region eu-west-2 --max-items 5
```

### Impact
- Tasks running on interrupted instances are killed immediately
- In-progress work is lost (staged data, partial outputs)
- Nextflow reports the tasks as FAILED

### Resolution
The retry strategy handles this automatically:
```groovy
process {
    errorStrategy = { task.attempt <= 3 ? 'retry' : 'ignore' }
    maxRetries = 3
}
```

Failed tasks are resubmitted to new instances. The pipeline continues without manual intervention.

### Prevention (if spot interruptions are too disruptive)
- Run critical/long tasks on the on-demand queue:
  ```groovy
  withName: '.*BWAMEM1_MEM.*' {
      queue = 'nf-workshop-ondemand'
  }
  ```
- Use SPOT_CAPACITY_OPTIMIZED allocation strategy (already configured) — chooses pools least likely to be interrupted
- Use `optimal` instance types (already configured) — gives Batch maximum flexibility across all instance families and generations
- AWS recommends flexibility across at least 10 instance types and multiple generations

### Monitoring Spot Pressure

**Spot Instance Advisor** (visual tool):
https://aws.amazon.com/ec2/spot/instance-advisor/

Shows interruption frequency (low/medium/high) and savings percentage per instance type per region.

**Spot price history (CLI):**
```bash
aws ec2 describe-spot-price-history \
  --instance-types m5.4xlarge c5.4xlarge r5.4xlarge m6i.4xlarge c6i.4xlarge \
  --product-descriptions "Linux/UNIX" \
  --region eu-west-2 \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --query 'SpotPriceHistory[].{Type:InstanceType,AZ:AvailabilityZone,Price:SpotPrice}' \
  --output table
```

Price spikes indicate high demand (and higher interruption risk) for that pool.

**Best practices (from AWS docs):**
- Be flexible across at least 10 instance types
- Include multiple generations (m5, m6i, m7i, not just m5)
- Use all available Availability Zones
- Use `optimal` instance type setting in Batch (lets Batch choose the best pool)
- Use `SPOT_CAPACITY_OPTIMIZED` allocation strategy (already configured)

---

## Job Stuck in RUNNABLE

### Symptoms
- Job shows RUNNABLE status for more than 5 minutes
- No instances launching in the compute environment

### How to Diagnose
```bash
# Check compute environment status
aws batch describe-compute-environments --compute-environments nf-workshop-ondemand --region eu-west-2 --query 'computeEnvironments[0].{Status:status,StatusReason:statusReason}'
```

If status is INVALID, the compute environment has a configuration problem (launch template, IAM, etc.)

### Common Causes
- Compute environment in INVALID state (check StatusReason)
- MaxvCpus reached (all capacity in use)
- No instances available for requested resource requirements
- Subnets have no internet access (NAT gateway issue)

---

## Container Creation Timeout (DockerTimeoutError)

### Symptoms
- Task fails with: `DockerTimeoutError: Could not transition to created; timed out after waiting 10m0s`
- ECS agent log shows: `dependency graph: dependency on resources not resolved`

### Cause
Multiple large containers being created simultaneously on the same instance, exhausting I/O or disk space.

### Resolution
- `ECS_CONTAINER_CREATE_TIMEOUT=10m` is already set (extends from default 4 minutes)
- `ECS_IMAGE_PULL_BEHAVIOR=prefer-cached` avoids re-checking registry for cached images
- The 1TB scratch volume with 1000 MB/s throughput reduces I/O contention
- Retry strategy handles occasional timeouts

---

## "No Space Left on Device" Errors

### Symptoms
- Task fails with: `[Errno 28] No space left on device`
- Usually during S3 data staging (downloading CRAM/BAM files)

### Cause
Multiple tasks staging large files to the same volume concurrently.

### Resolution
- `scratch = '/tmp'` in nextflow.config redirects staging to the 1TB scratch volume
- Volume configured with 1000 MB/s throughput (prevents I/O throttling)
- Check volumes: `df -h / /mnt/scratch` on the instance

### Monitoring during a run
```bash
watch -n 10 'df -h / /mnt/scratch && echo "---" && iostat -xm 1 1 | grep nvme'
```

---

## "nextflow-bin" Race Condition (Exit Code 255)

### Symptoms
- Task fails with exit code 255
- Log shows: `[Errno 17] File exists: '/tmp/nextflow-bin'`

### Cause
Known Nextflow bug (#6761). When multiple task containers share `/mnt/scratch:/tmp`, they race to create `/tmp/nextflow-bin`. The second container to attempt it gets "File exists."

### Resolution
Retry strategy catches this automatically. On retry, the directory already exists so the `aws s3 cp` either succeeds (overwrites) or is a no-op.

### Workaround
Add exit code 255 to your retry strategy:
```groovy
process {
    errorStrategy = { task.attempt <= 3 ? 'retry' : 'ignore' }
    maxRetries = 3
}
```

---

## Cloud-init Failures (Instance Unhealthy)

### Symptoms
- Instance launches but never registers with ECS
- ASG replaces instance repeatedly
- Jobs stay in RUNNABLE

### How to Diagnose
SSM into the instance (if SSM agent started) and check:
```bash
cat /var/log/cloud-init-output.log | tail -30
```

### Common Causes
- Package installation failure (package not available on AL2023)
- Non-ASCII characters in UserData (broke cloud-init on Python 2.7 / AL2)
- EBS volume device name mismatch (`/dev/nvme1n1` vs expected)
- S3 Mountpoint install failure

---

## Monitoring Commands

### Instance health
```bash
# SSM into an instance
aws ssm start-session --target <INSTANCE_ID> --region eu-west-2

# Check what's running
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}"
docker stats --no-stream

# Check disk
df -h / /mnt/scratch
du -sh /var/lib/docker/
du -sh /mnt/scratch/

# Check I/O throughput
iostat -xm 1 2 | grep nvme

# Check what containers are actually doing
for c in $(docker ps -q); do echo "=== $c ==="; docker top $c; echo; done
```

### Job progress
```bash
# Find head node job
JOB_ID=$(aws batch list-jobs --job-queue nf-workshop-ondemand --job-status RUNNING --region eu-west-2 --query 'jobSummaryList[0].jobId' --output text)

# View latest Nextflow output
LOG_STREAM=$(aws batch describe-jobs --jobs $JOB_ID --region eu-west-2 --query 'jobs[0].container.logStreamName' --output text)
aws logs get-log-events --log-group-name /aws/batch/job --log-stream-name "$LOG_STREAM" --limit 20 --region eu-west-2 --query 'events[].message' --output text
```

### NAT gateway usage (cost monitoring)
Check CloudWatch → NAT Gateway metrics → BytesInFromDestination. High values indicate cross-region S3 traffic (iGenomes not pre-synced) or container image pulls.

### VPC endpoint validation
```bash
# Confirm S3 traffic goes through endpoint (from instance)
traceroute -n -T -p 443 s3.eu-west-2.amazonaws.com
# Should show <1ms latency = VPC endpoint
# Compare with cross-region:
traceroute -n -T -p 443 s3-3-w.amazonaws.com
# Should show ~10ms = through NAT
```
