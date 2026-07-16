# EC2 Head to Batch

Nextflow runs on a persistent EC2 instance instead of your laptop. More reliable for long-running pipelines. The instance stays on even if you disconnect.

## How It Works

```
[EC2 Instance]          →  nextflow run (always on)
[AWS Batch]             →  runs each task as a container
[S3 Bucket]             →  stores work directory + results

```

1. You SSH/SSM into an EC2 instance
2. Run `nextflow run hello-world --profile awsbatch` inside tmux/screen (survives disconnection)
3. Nextflow submits tasks to Batch, same as laptop pattern
4. You can disconnect and reconnect later to check progress

## When to Use

- Pipelines that run longer than your laptop battery
- Shared head node for a team
- Need to disconnect and come back later

## Building Blocks

All the Batch infrastructure (S3, IAM, Compute Environment, Job Queue) plus:

| Building Block | What it does |
| --- | --- |
| **EC2 instance** | Small instance (e.g. t3.medium) with Nextflow installed |
| **Security group** | Allows SSH or SSM access to the instance |
| **Instance profile** | Permissions to submit Batch jobs and access S3 |

## Structure

```
ec2-head-to-batch/
├── README.md               ← this file
├── infrastructure/         ← CDK/CloudFormation for full stack (Batch + EC2 head)
├── configs/                ← nextflow.config for this pattern
└── scripts/                ← setup, connect, teardown scripts

```

## How to Deploy

### Option 1: Infrastructure as Code

Deploy the full infrastructure (Batch + EC2 head node) using CDK or CloudFormation. Should work out of the box. See `infrastructure/`.

**[TODO: Tested IaC in **`infrastructure/`**]**

### Option 2: Generate with AI

> "Generate CDK to deploy the full infrastructure for running Nextflow on AWS Batch with an EC2 head node. I need: S3 bucket, IAM roles, Batch compute environment, job queue, and a small EC2 instance (t3.medium) with SSM access and Nextflow pre-installed via user data. Everything should work out of the box after deploy."

## Validate

```bash
# Connect to the instance
aws ssm start-session --target <instance-id>

# Run hello world
nextflow run hello-world --profile awsbatch

```

## Limitations

- EC2 instance costs money while running (even when idle)
- Need to manage the instance (updates, monitoring)
- Single point of failure (if instance terminates, pipeline stops)

## Public References

- [EC2 getting started](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)
- [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Nextflow AWS Batch executor](https://www.nextflow.io/docs/latest/aws.html)

