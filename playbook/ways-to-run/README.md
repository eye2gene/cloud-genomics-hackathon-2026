# Ways to Run

There are multiple ways to run Nextflow pipelines on AWS. This chapter documents them, compares them, and helps people choose the right approach.

## The Patterns

| Pattern | What it means | Complexity |
| --- | --- | --- |
| **Laptop to Batch** | Nextflow runs on your laptop, submits tasks to AWS Batch | Simplest starting point |
| **EC2 Head to Batch** | Nextflow runs on a persistent EC2 instance, submits tasks to Batch | More reliable, always-on |
| **Batch Squared** | Nextflow head node itself runs as a Batch job, submits child jobs | Fully cloud-native, ephemeral |
| **AWS HealthOmics** | Fully managed service, no infrastructure to manage | Simplest operationally |

## Where to Start

If you're new to AWS, the best starting points are **AWS HealthOmics** (no infrastructure to manage) and **Laptop to Batch** (simplest self-managed option). You'll have already used HealthOmics in the getting started workshop.

For guidance on which pattern suits your use case, see `decision-framework/which-pattern.md`.

## Laptop to Batch

The simplest self-managed approach. What you need:

- S3 bucket (work directory)
- Batch compute environment + job queue
- IAM roles (instance role + job role)
- A `nextflow.config` pointing at your queue and bucket

See `patterns/laptop-to-batch/` for building block descriptions, public references, and guidance.

## Explore Further

Once laptop to Batch works, explore:

- `patterns/ec2-head-to-batch/` - persistent head node for longer-running pipelines
- `patterns/batch-squared/` - reference CDK implementation in `patterns/batch-squared/infrastructure/` (TypeScript, deploys full stack)
- `patterns/health-omics/` - fully managed, no infra needed

## Reference

- `reference/TROUBLESHOOTING.md` - Common Batch + Nextflow issues
- `reference/AMI-STRATEGY.md` - AMI decision framework
- [Nextflow AWS docs](https://www.nextflow.io/docs/latest/aws.html)
- [AWS Batch docs](https://docs.aws.amazon.com/batch/)
- [AWS HealthOmics docs](https://docs.aws.amazon.com/omics/)

