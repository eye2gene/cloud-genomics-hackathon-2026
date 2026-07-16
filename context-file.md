# Cloud Genomics Hackathon: Context for AI Tools

Paste this into Kiro (or any AI coding assistant) so it understands what you're working on.

## What This Is

A hackathon building a community playbook for running bioinformatics pipelines on AWS. Mixed-experience group (some new to AWS, some advanced). We're working in sandbox accounts with Nextflow, AWS Batch, and AWS HealthOmics.

## The Repo

```
cloud-genomics-hackathon-2026/
├── README.md                           # Event overview, how to get started
├── playbook/                           # The playbook we're building
│   ├── ways-to-run/                    # Chapter: execution patterns
│   │   ├── patterns/
│   │   │   ├── laptop-to-batch/        # Simplest: Nextflow on laptop → Batch
│   │   │   ├── ec2-head-to-batch/      # Persistent head node on EC2
│   │   │   ├── batch-squared/          # Head node as Batch job (CDK available)
│   │   │   └── health-omics/           # Fully managed service
│   │   ├── decision-framework/         # Which pattern to use
│   │   └── comparison-matrix.md        # Pattern comparison (placeholder)
│   ├── benchmarking/                   # Chapter: performance and cost data
│   │   ├── results/                    # Benchmark results (CSV template)
│   │   ├── methodology/               # How to run and document a benchmark
│   │   ├── sample-sheets/             # Input samplesheets (1000 Genomes, PGP-UK)
│   │   ├── configs/                   # Nextflow configs for different setups
│   │   └── scripts/                   # Benchmark execution scripts
│   ├── operations/                     # Chapter: monitoring, cost, troubleshooting
│   │   ├── dashboards/                # CloudWatch dashboard configs
│   │   ├── scripts/                   # Monitoring/cost scripts
│   │   └── runbooks/                  # Operational runbooks
│   ├── bring-your-own/                 # Chapter: migrating pipelines to AWS
│   │   ├── examples/                  # Example migrated pipelines
│   │   └── configs/                   # Batch executor configs
│   └── reference/                      # Shared reference docs
│       ├── TROUBLESHOOTING.md          # Common Batch + Nextflow issues
│       ├── AMI-STRATEGY.md             # Custom vs dynamic AMI decision
│       ├── STORAGE-BENCHMARK.md        # Previous storage benchmark results
│       ├── DEBUGGING.md                # How to triage failures
│       └── IMPROVEMENTS.md             # Backlog of ideas

```

## The 4 Goals

### 1. Ways to Run

Deploy and document different execution patterns. Start with laptop to Batch (simplest). Explore EC2 head, Batch squared, HealthOmics. Create getting-started guides and compare approaches.

### 2. Benchmarking

Systematic performance testing. Storage options (S3, S3 Mountpoint, EFS, FSx), scaling (1/5/10/50/100 genomes), variant callers (GATK vs Sentieon), compute (Spot vs On-Demand). Record results in the CSV template.

### 3. Operations

Monitoring, cost tracking, alerting, troubleshooting. CloudWatch dashboards, cost allocation tags, log analysis, operational runbooks.

### 4. Bring Your Own Pipeline

Adapt an existing pipeline for AWS Batch. Remove hard-coded paths, configure containers for ECR, handle reference data. Document the migration process.

## Architecture (Batch Squared pattern - reference implementation)

A CDK stack deploys:

- **VPC** with private subnets + NAT gateway + S3 VPC endpoint
- **S3 bucket** for work directory, reference data, and results
- **IAM roles** (instance role, job role, service role)
- **Batch compute environments** (On-Demand for head node, Spot for workers)
- **Batch job queues** (separate for head and workers)
- **Launch template** with scratch EBS volume (gp3, 1000 MB/s throughput)
- **ECR repository** for the Nextflow head node container
- **CodeBuild** to build the head container on deploy
- **Nextflow job definition** for submitting pipeline runs

Workers scale to zero when idle. Head runs On-Demand for reliability. Workers run on Spot for cost.

## Key Technical Details

- **Region:** eu-west-2
- **Nextflow executor:** awsbatch
- **Container images:** Pulled from public registries (nf-core, biocontainers) or ECR
- **Work directory:** `s3://<bucket>/work`
- **Reference data:** Available via AWS Open Data Registry (MCP server available for Kiro)
- **Retry strategy:** 3 retries for transient failures (spot interruptions, container timeouts)
- **Instance types:** `optimal` (Batch selects best fit)

## Common Issues

- Job stuck in RUNNABLE: Check compute environment status, IAM permissions, subnet internet access
- Container timeout: Large images + shared scratch volume causes contention
- No space on device: Multiple tasks staging large files concurrently (bump EBS throughput)
- Spot interruptions: Retry strategy handles automatically; use On-Demand queue for critical tasks
- Exit code 255: Known Nextflow bug with shared /tmp directory (retry resolves)

## Public References

- Nextflow AWS Batch: [https://www.nextflow.io/docs/latest/aws.html](https://www.nextflow.io/docs/latest/aws.html)
- nf-core AWS config: [https://nf-co.re/docs/usage/tutorials/nextflow_on_aws_batch](https://nf-co.re/docs/usage/tutorials/nextflow_on_aws_batch)
- AWS Batch docs: [https://docs.aws.amazon.com/batch/](https://docs.aws.amazon.com/batch/)
- AWS HealthOmics: [https://docs.aws.amazon.com/omics/](https://docs.aws.amazon.com/omics/)
- AWS Open Data MCP: [https://aws.amazon.com/blogs/opensource/introducing-mcp-server-for-registry-of-open-data-on-aws/](https://aws.amazon.com/blogs/opensource/introducing-mcp-server-for-registry-of-open-data-on-aws/)

## How to Use This File

Tell your AI tool what you're working on:

- "I'm working on the Benchmarking chapter. I need to set up FSx for Lustre for a storage benchmark."
- "I'm trying to deploy the laptop-to-batch pattern. Generate CDK for S3, IAM, Batch compute environment, and job queue."
- "My Batch job is stuck in RUNNABLE. Help me debug."
- "Generate a 10-sample samplesheet using 1000 Genomes data from AWS Open Data."

