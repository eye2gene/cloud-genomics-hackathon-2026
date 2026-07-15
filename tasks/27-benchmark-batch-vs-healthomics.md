## Summary

Run the **same `nf-core/sarek` workload on AWS HealthOmics** and compare it head-to-head with this AWS Batch platform: cost, runtime, setup complexity, scalability, and when to choose each. This is the hackathon's **service-comparison** outcome.

**Difficulty:** hard · **Effort:** large

## Background

The hackathon explicitly asks teams to run the same workloads on **AWS Batch and AWS HealthOmics** and document the trade-offs. This repo is the Batch side; HealthOmics is a managed genomics service that runs Nextflow/WDL workflows without you managing compute environments, queues, or launch templates at all — you import the workflow, point it at S3, and it provisions/bills per run.

The comparison is the deliverable, not a winner: HealthOmics trades control and (often) raw cost for drastically less infrastructure to build and maintain — which matters a lot for the bioinformatician audience this playbook targets.

> Scope note: HealthOmics has its own workflow packaging (container/ECR requirements, `omics` run inputs) and quotas. Treat this as a parallel deployment path, not a change to the Batch stack.

## What to do

- [ ] Package/import sarek as a HealthOmics-ready workflow (container + parameter template) and run it on the same dataset(s) used for the Batch benchmarks.
- [ ] Run at ≥2 matched scale points and record runtime + cost in the **same** `benchmarks/results.csv` schema (add a `service` = `batch` | `healthomics` dimension).
- [ ] Capture the qualitative axes: setup/onboarding effort, operational burden, observability, quota/scaling limits, reproducibility.
- [ ] Write a "when to use Batch vs HealthOmics" section for the playbook, backed by the numbers.

## Implementation pointers

- **New, parallel to the Batch stack** — HealthOmics work doesn't modify `lib/`; it's a separate run path (CLI/console/IaC for `omics` resources). Keep shared inputs in the same S3 layout so the workloads are truly identical.
- **Results** — extend `benchmarks/results.template.csv` with a `service` column so Batch and HealthOmics rows sit side by side; reuse the cost method from `07-cost-allocation-tags.md` / Cost Explorer.
- Align the sarek revision, reference genome, and sample set with `25-benchmark-scale-runs.md` so only the *service* differs.

## Acceptance criteria

- Sarek runs end-to-end on HealthOmics on the same data as the Batch runs.
- Runtime + cost recorded for both services at ≥2 matched scales.
- A written Batch-vs-HealthOmics trade-off comparison (cost, complexity, scalability, control) lands in the playbook/README.

## References

- [AWS HealthOmics](https://docs.aws.amazon.com/omics/latest/dev/what-is-healthomics.html) · [HealthOmics workflows (Nextflow/WDL)](https://docs.aws.amazon.com/omics/latest/dev/workflows.html)
- [nf-core/sarek](https://nf-co.re/sarek)
- Related: `25-benchmark-scale-runs.md`, `26-benchmark-sentieon-vs-gatk.md`, `07-cost-allocation-tags.md`
