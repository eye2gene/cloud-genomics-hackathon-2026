# Batch Squared

The Nextflow head node itself runs as a Batch job. It submits child jobs for each pipeline task. Fully cloud-native - no laptop or EC2 instance needed after submission.

## How It Works

```
[You]                   →  submit head job to Batch (one command)
[AWS Batch - Head]      →  Nextflow container orchestrates the pipeline
[AWS Batch - Workers]   →  each task runs as a child Batch job
[S3 Bucket]             →  stores work directory + results

```

1. You submit a single Batch job (the head node)
2. The head node container runs Nextflow
3. Nextflow submits each pipeline task as a child Batch job
4. Workers run on Spot instances (cheap, auto-scaling)
5. Head node runs on On-Demand (reliable, stays up for the full pipeline)
6. Everything scales to zero when done

## When to Use

- Automated/scheduled pipeline runs (event-driven)
- No persistent infrastructure needed between runs
- Production workloads
- Want fully ephemeral execution

## Building Blocks

Full infrastructure deployed as a single CDK stack:

| Building Block | What it does |
| --- | --- |
| **VPC** | Private networking for compute instances |
| **S3 bucket** | Work directory, reference data, results |
| **IAM roles** | Instance role, job role, service role |
| **Batch compute environments** | On-Demand (head) + Spot (workers) |
| **Batch job queues** | Separate queues for head and workers |
| **Launch template** | Instance configuration (scratch volumes, ECS tuning) |
| **ECR repository** | Stores the Nextflow head node container image |
| **CodeBuild** | Builds the head node container on deploy |
| **Nextflow job definition** | Defines the head node Batch job |

## Structure

```
batch-squared/
├── README.md               ← this file
├── FULL-GUIDE.md           ← detailed deployment and usage guide
├── infrastructure/
│   ├── python/             ← Python CDK
│   └── typescript/         ← TypeScript CDK
└── scripts/                ← submit job, check status, teardown

```

## How to Deploy

### Option 1: Infrastructure as Code

This pattern has working CDK infrastructure in two languages:

- **Python:** `infrastructure/python/` (deploy with `cdk deploy`)
- **TypeScript:** `infrastructure/typescript/` (deploy with `bunx aws-cdk deploy`)

See the FULL-GUIDE.md for detailed deployment instructions.

### Option 2: Generate with AI

> "Generate CDK to deploy Nextflow on AWS Batch using the Batch Squared pattern. The head node runs as a Batch job on On-Demand, workers run on Spot. I need: VPC, S3, IAM roles, two Batch compute environments (on-demand + spot), two job queues, a launch template, ECR repository, CodeBuild for the head container, and a Nextflow job definition. Deploy should produce a working stack I can submit pipelines to."

## Validate

```bash
# Submit a pipeline run (head node job)
aws batch submit-job \
  --job-name test-hello \
  --job-queue <head-queue-name> \
  --job-definition <nextflow-job-definition> \
  --container-overrides '{"command": ["hello-world"]}'

```

## Limitations

- More complex to set up than laptop or EC2 head patterns
- Debugging is harder (head node logs are in CloudWatch, not your terminal)
- Head node container needs to be built and pushed to ECR

## Public References

- [Nextflow AWS Batch docs](https://www.nextflow.io/docs/latest/aws.html)
- [AWS Batch job dependencies](https://docs.aws.amazon.com/batch/latest/userguide/job_dependencies.html)

