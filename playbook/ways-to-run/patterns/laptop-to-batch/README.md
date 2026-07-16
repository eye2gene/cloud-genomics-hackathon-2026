# Laptop to Batch

The simplest way to run Nextflow on AWS. Nextflow runs on your laptop and submits each pipeline task as a Batch job.

## How It Works

```
[Your Laptop]           →  nextflow run (orchestrates the pipeline)
[AWS Batch]             →  runs each task as a container on EC2
[S3 Bucket]             →  stores work directory + results

```

1. You run `nextflow run` from your laptop
2. Nextflow reads the config and connects to AWS Batch
3. For each pipeline task, Nextflow submits a Batch job
4. Batch provisions EC2 instances, pulls the container, runs the task
5. Task reads/writes data to S3
6. Nextflow collects results and moves to the next task

## Building Blocks

| Building Block | What it does | Required? |
| --- | --- | --- |
| **S3 bucket** | Work directory for Nextflow and stores pipeline results | Yes |
| **IAM instance role** | Allows EC2 instances in Batch to pull containers and access S3 | Yes |
| **IAM job role** | Allows Nextflow tasks (ECS containers) to read/write S3 | Yes |
| **Batch compute environment** | Managed pool of EC2 instances that run containers | Yes |
| **Batch job queue** | Where Nextflow submits tasks | Yes |
| **nextflow.config** | Tells Nextflow to use AWS Batch as the executor | Yes |
| **Launch template** | Custom instance configuration (scratch volumes, monitoring agents) | Optional |
| **Custom AMI** | Pre-baked instance image (faster boot, pre-pulled containers) | Optional |
| **EBS volume config** | Scratch storage for data staging (increase IOPS/throughput for large datasets) | Optional |
| **VPC / Subnets** | Network configuration (public subnets for simplicity, private for security) | Depends |

## Structure

```
laptop-to-batch/
├── README.md               ← this file
├── infrastructure/         ← CDK/CloudFormation to deploy the building blocks
├── configs/
│   └── nextflow.config     ← example Nextflow config for this pattern
└── scripts/                ← helper scripts (deploy, test, teardown)

```

## How to Deploy

Two approaches:

### Option 1: Infrastructure as Code

Deploy the building blocks using CDK or CloudFormation. See `infrastructure/` for templates.

**[TODO: Tested IaC in **`infrastructure/`**]**

### Option 2: Generate with AI

Use Kiro with the `context-file.md` to generate infrastructure:

> "Generate CDK to deploy the minimum infrastructure for running Nextflow on AWS Batch from my laptop. I need an S3 bucket, IAM roles, a Batch compute environment using default VPC public subnets, and a job queue. Keep it simple."

## Validate

Once deployed, run:

```bash
nextflow run hello-world --profile awsbatch

```

If this completes with tasks running on Batch, your infrastructure works.

## Limitations

- Your laptop must stay on for the duration of the pipeline
- Requires stable internet connection
- Not suitable for very long-running pipelines (see `../ec2-head-to-batch/` or `../batch-squared/`)

## Public References

- [Nextflow AWS Batch executor](https://www.nextflow.io/docs/latest/aws.html)
- [AWS Batch getting started](https://docs.aws.amazon.com/batch/latest/userguide/getting-started.html)

