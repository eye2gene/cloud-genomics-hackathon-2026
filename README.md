# Cloud Genomics Hackathon: Community Playbook

This is an experiment. Can a mixed group of people with different experience levels, sandbox AWS accounts, and AI tools come together and produce a reusable community playbook for running bioinformatics pipelines on the cloud? That's what we're testing.

This repo is both the hackathon and the deliverable. Your job is to fill in the gaps, resolve issues, and see if we can build something genuinely useful for the community.

## What We're Building

A community playbook covering:

- How to run pipelines on AWS (multiple patterns, from fully managed to custom infrastructure)
- Benchmarking results (storage, compute, scaling)
- Operational guidance (monitoring, cost management, troubleshooting)
- Pipeline migration advice (adapting existing pipelines for the cloud)

The `playbook/` folder is the playbook. Each subfolder is a chapter. Nothing is set in stone. The templates and structure are placeholders. Your group decides what the outputs look like.

This repo also includes a reference CDK implementation of the "Batch Squared" pattern in `playbook/ways-to-run/patterns/batch-squared/infrastructure/`. It deploys the full stack (VPC, S3, IAM, Batch, head node container). See the Ways to Run chapter for details.

## Setup

Ensure the following are available before starting:

- AWS CLI configured with sandbox account credentials
- Kiro connected to your AWS account
- Nextflow installed locally
- Docker installed
- Access to AWS Batch, S3, and related services in your sandbox

These will be walked through on the day.

## Getting Started

Once setup is complete, get the basics working:

### Kiro + AWS HealthOmics Workshop

Get familiar with Kiro and see a fully managed way of running pipelines without worrying about infrastructure. This introduces how to interact with Kiro as your AI coding assistant and shows what a managed service experience looks like.

- [Blog: From Prompt to Pipeline - AI-Powered Bioinformatics with Kiro and AWS HealthOmics](https://aws.amazon.com/blogs/industries/from-prompt-to-pipeline-ai-powered-bioinformatics-workflow-development-with-kiro-and-aws-healthomics/)
- [Workshop: Module 3 - Genomics with Kiro](https://catalog.us-east-1.prod.workshops.aws/workshops/a006a3c9-adad-456d-8d63-6b0a71da80d3/en-US/40-module3-genomics-with-kiro)

### Laptop to AWS Batch

Get a pipeline executing on AWS Batch from your laptop. This gives you a working baseline with more control over the infrastructure.

See `playbook/ways-to-run/` for building block descriptions, public references, and guidance.

## Pick a Chapter

Once you have a pipeline running on AWS, form a group and choose a chapter to contribute to:

| Chapter | What you'll do | Good for |
| --- | --- | --- |
| Ways to Run | Document and deploy different execution patterns (laptop to Batch, Batch squared, Health Omics). Create getting-started guides, compare approaches. | People who want to explore deployment options |
| Benchmarking | Run pipelines at different scales and storage configurations. Collect timing, cost, and performance data. | People who like systematic testing and data |
| Operations | Set up monitoring, cost tracking, alerting. Document operational best practices. | People interested in production readiness |
| Bring Your Own Pipeline | Adapt a real pipeline for AWS. Document the migration process, gotchas, and solutions. | People with an existing pipeline they want to run on the cloud |

## How It Works

1. Form a group around a chapter
2. Look at the GitHub issues for that chapter
3. Pick tasks or propose new ones
4. Make decisions as a group about what the outputs should look like
5. Fill in the placeholders, add your findings, update the docs
6. Your work becomes part of the playbook

Nothing is prescribed. The structure is a starting point. If it doesn't work for your group, change it.

## Using Kiro

A `context-file.md` is provided in this repo. It contains a description of the hackathon goals, the architecture, and the tools available.

**How to use it:**

1. Open Kiro
2. Paste the context file content
3. Tell Kiro what you're working on (e.g. "I need to set up EFS for a storage benchmark")
4. Kiro has full context and can generate code, configs, and docs for you

This means you don't have to explain the project from scratch every time you ask for help.

## Timeline

- **Today**: Get set up, form groups, pick a chapter, start working
- **This week**: Continue working in sandbox accounts (access for 1 week)
- **In 2 weeks**: Regroup and present your chapter findings

Continue working with your group between now and the presentation. Use the sandbox accounts and Kiro to build out your chapter.

## Reference Docs

- TROUBLESHOOTING.md - Common Batch + Nextflow issues and fixes
- AMI-STRATEGY.md - Custom vs dynamic AMI decision
- STORAGE-BENCHMARK.md - Previous storage benchmarking results
- [DEBUGGING.md](DEBUGGING.md) - How to triage pipeline failures
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Backlog of ideas to explore

