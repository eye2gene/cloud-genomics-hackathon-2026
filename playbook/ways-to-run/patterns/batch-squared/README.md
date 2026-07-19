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
## Example Usage

1.- Deploy CDK
```
bun install
bun update aws-cdk
bun run cdk bootstrap aws://xxxxxxxxxxxxxxxxxx/eu-west-2
bun run cdk deploy
```
2.- Set tower credentials (optional)
```
TOWER_ACCESS_TOKEN=xxxxxxxxxxxxxxx
TOWER_WORKSPACE_ID=xxxxxxxxxxxxxxx
export TOWER_ACCESS_TOKEN=${TOWER_ACCESS_TOKEN}
export TOWER_WORKSPACE_ID=${TOWER_WORKSPACE_ID}
```
3.1- Run hello pipeline
```
aws batch submit-job \
  --job-name "nf-hello-$(date +%Y%m%d-%H%M%S)" \
  --job-queue "OnDemand-cdk-nfbatch-eu-west-2" \
  --job-definition "nextflow-cdk-nfbatch-eu-west-2" \
  --container-overrides "{
      \"command\": [
        \"hello\", \"-with-tower\"
        ],
      \"environment\": [
        {\"name\": \"AWS_CLI_S3_MAX_CONCURRENT_REQUESTS\", \"value\": \"4\"},
        {\"name\": \"TOWER_ACCESS_TOKEN\", \"value\": \"$TOWER_ACCESS_TOKEN\"},
        {\"name\": \"TOWER_WORKSPACE_ID\", \"value\": \"$TOWER_WORKSPACE_ID\"}
      ]
    }" \
  --region eu-west-2
```
3.2- Run Sarek test
```
aws batch submit-job \
  --job-name "sarek-test-$(date +%Y%m%d-%H%M%S)" \
  --job-queue "OnDemand-cdk-nfbatch-eu-west-2" \
  --job-definition "nextflow-cdk-nfbatch-eu-west-2" \
  --container-overrides "{
    \"command\": [
      \"nf-core/sarek\",
      \"-r\", \"3.9.0\",
      \"-profile\", \"test\",
      \"--outdir\", \"s3://cdk-new1-cdk-nfbatch-eu-west-2-984214445113/results/sarek-test\",
      \"-process.maxRetries\", \"3\",
      \"-process.errorStrategy\", \"retry\",
      \"-resume\", \"-with-tower\"
    ],
    \"environment\": [
      {\"name\": \"AWS_CLI_S3_MAX_CONCURRENT_REQUESTS\", \"value\": \"4\"},
      {\"name\": \"TOWER_ACCESS_TOKEN\", \"value\": \"$TOWER_ACCESS_TOKEN\"},
      {\"name\": \"TOWER_WORKSPACE_ID\", \"value\": \"$TOWER_WORKSPACE_ID\"},
    ]
  }" \
  --region eu-west-2
```
3.3- Run Sarek full test
```
aws batch submit-job \
  --job-name "sarek-full-test-$(date +%Y%m%d-%H%M%S)" \
  --job-queue "OnDemand-cdk-nfbatch-eu-west-2" \
  --job-definition "nextflow-cdk-nfbatch-eu-west-2" \
  --container-overrides "{
    \"command\": [
      \"nf-core/sarek\",
      \"-r\", \"3.9.0\", 
      \"-profile\", \"test_full\", 
      \"--outdir\", \"s3://cdk-new1-cdk-nfbatch-eu-west-2-984214445113/results/sarek-full-test\", 
      \"-process.maxRetries\", \"3\", 
      \"-process.errorStrategy\", \"retry\",
      \"-resume\", \"-with-tower\"
    ],
    \"environment\": [
      {\"name\": \"AWS_CLI_S3_MAX_CONCURRENT_REQUESTS\", \"value\": \"4\"},
      {\"name\": \"TOWER_ACCESS_TOKEN\", \"value\": \"$TOWER_ACCESS_TOKEN\"},
      {\"name\": \"TOWER_WORKSPACE_ID\", \"value\": \"$TOWER_WORKSPACE_ID\"},
    ]
  }" \
  --region eu-west-2
```
3.4- Run Sarek PGP S1
```
aws batch submit-job \
  --job-name "sarek-pgp1-$(date +%Y%m%d-%H%M%S)" \
  --job-queue "OnDemand-cdk-nfbatch-eu-west-2" \
  --job-definition "nextflow-cdk-nfbatch-eu-west-2" \
  --container-overrides "{
    \"command\": [
      \"nf-core/sarek\",
      \"-r\", \"3.9.0\", 
      \"--input\", \"s3://lconde-pgp-1/spreadsheet.csv\",
      \"--outdir\", \"s3://cdk-new1-cdk-nfbatch-eu-west-2-984214445113/results/sarek-pgp1\", 
      \"--genome\", \"GATK.GRCh38\",
      \"--tools\",  \"haplotypecaller",
      \"-process.maxRetries\", \"3\", 
      \"-process.errorStrategy\", \"retry\",
      \"-resume", \"-with-tower\"
    ],
    \"environment\": [
      {\"name\": \"AWS_CLI_S3_MAX_CONCURRENT_REQUESTS\", \"value\": \"4\"},
      {\"name\": \"TOWER_ACCESS_TOKEN\", \"value\": \"$TOWER_ACCESS_TOKEN\"},
      {\"name\": \"TOWER_WORKSPACE_ID\", \"value\": \"$TOWER_WORKSPACE_ID\"}
    ]
  }' \
  --region eu-west-2
```


## Limitations

- More complex to set up than laptop or EC2 head patterns
- Debugging is harder (head node logs are in CloudWatch, not your terminal)
- Head node container needs to be built and pushed to ECR

## Public References

- [Nextflow AWS Batch docs](https://www.nextflow.io/docs/latest/aws.html)
- [AWS Batch job dependencies](https://docs.aws.amazon.com/batch/latest/userguide/job_dependencies.html)

