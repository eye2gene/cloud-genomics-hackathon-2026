# Bring Your Own Pipeline

This chapter is for people who already have a pipeline and want to run it on AWS. Document the migration process: what worked, what broke, what you had to change.

## The Process

1. Get a basic pipeline running first (see `../ways-to-run/`)
2. Try your own pipeline
3. Document what you had to change
4. Share the gotchas so others don't hit the same problems

## Common Migration Tasks

- Adapting container definitions for AWS Batch
- Configuring resource requests (memory, CPUs) for Batch and HealthOmics
- Handling data staging (local paths to S3 paths)
- Dealing with pipeline-specific dependencies
- Adjusting retry strategies for cloud failures

## Things to Document

For each pipeline you migrate, capture:
- Pipeline name and source (nf-core, custom, etc.)
- What config changes were needed
- What broke and how you fixed it
- Performance compared to local/HPC execution
- Any AWS-specific gotchas

## Example Pipelines

| Pipeline | Status | Notes |
|----------|--------|-------|
| nf-core/rnaseq | [not started] | |
| nf-core/sarek | [not started] | |
| [Your pipeline] | | |

## Useful References

- [Nextflow AWS Batch executor docs](https://www.nextflow.io/docs/latest/aws.html)
- `reference/TROUBLESHOOTING.md` - Common issues
- `../ways-to-run/` - Choose your execution pattern first

## AI Prompts

See `AI-PROMPTS.md` in this folder for ready-made prompts you can paste into your AI coding assistant (Kiro, Claude, etc.) to get started.
