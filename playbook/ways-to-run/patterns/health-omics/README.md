# AWS HealthOmics

A fully managed service. No infrastructure to deploy or manage. You submit a workflow and AWS handles everything.

```
[You]                   →  submit workflow via API/Console
[AWS HealthOmics]       →  managed Nextflow execution
[S3 / Omics Stores]     →  input and output data

```

## When to Use

- Want zero infrastructure management
- Genomics-focused workflows
- New to AWS (gentlest starting point)
- Compliance requirements (built-in audit, encryption)

## Getting Started

You already used HealthOmics in the introductory workshop:

- [Workshop: Module 3 - Genomics with Kiro](https://catalog.us-east-1.prod.workshops.aws/workshops/a006a3c9-adad-456d-8d63-6b0a71da80d3/en-US/40-module3-genomics-with-kiro)
- [Blog: From Prompt to Pipeline](https://aws.amazon.com/blogs/industries/from-prompt-to-pipeline-ai-powered-bioinformatics-workflow-development-with-kiro-and-aws-healthomics/)

## Things to Document

- Comparison to AWS Batch (setup time, cost, observability, limitations)
- What pipeline adaptations are needed for HealthOmics
- Pricing model and cost comparison
- What you can and can't customise
- When HealthOmics is the right choice vs Batch

## Public References

- [AWS HealthOmics docs](https://docs.aws.amazon.com/omics/)
- [HealthOmics pricing](https://aws.amazon.com/omics/pricing/)

