## Summary

Run `nf-core/sarek` at the hackathon's scale points (**1 → 30 → 100 → 1000 whole genomes**) and record **runtime and cost** at each, producing the headline benchmarking dataset. This is hackathon **Outcome 3** — the published cost/runtime-vs-scale numbers — turned into a pickable task.

**Difficulty:** medium · **Effort:** large

## Background

The scaffolding already exists: `README.md` → Benchmarking defines the scale scenarios and submit command, `benchmarks/samplesheets/` holds input templates, and `benchmarks/results.template.csv` defines the results schema (scale, `workflow_variant`, `storage_strategy`, instance types, wall-clock, vCPU-hours, cost, **cost-per-genome**). What's missing is the actual runs + recorded data, and (optionally) a script to automate the submit → collect → append loop.

Datasets are the open **1000 Genomes** and **PGP-UK** cohorts. Keep everything else fixed (pipeline revision, region, storage strategy) so scale is the only variable.

> **Start small and gate spend.** Confirm the 1-genome run completes end-to-end and lands results in S3 **before** launching the 100/1000-genome runs — those cost real money and take hours. Pin `-r` so every run uses identical pipeline code.

## What to do

- [ ] Create the samplesheets for each scale (1 / 30 / 100 / 1000) from the templates; stage inputs in S3.
- [ ] Run sarek at each scale with `-with-report -with-timeline -with-trace` for runtime data; pin the revision and hold the storage strategy constant.
- [ ] Record one row per run in `benchmarks/results.csv`: wall-clock, total vCPU-hours, estimated cost, derived cost-per-genome, success/failure.
- [ ] Capture cost via cost-allocation tags + Cost Explorer (needs `07-cost-allocation-tags.md`) or estimate from vCPU-hours × price.
- [ ] Summarise the cost/runtime-vs-scale curve in the README (does cost-per-genome flatten? where does fan-out break?).
- [ ] (Optional) Automate the loop in `scripts/` so a team can re-run the whole sweep reproducibly.

## Implementation pointers

- **`benchmarks/samplesheets/`** — build `wgs_n1/n30/n100/n1000.csv` from the templates.
- **`benchmarks/results.csv`** — copy from `results.template.csv`; the schema is already right for this.
- **Runtime** — Nextflow `-with-report`/`-with-timeline`/`-with-trace` emit per-task timing; stage them to S3 with results.
- **Cost** — depends on `07-cost-allocation-tags.md`; a `run-id` tag per submission gives clean per-run attribution.
- Coordinate with `26` (Sentieon variant), `04` (storage strategy), and `19` (a `benchmark`/on-demand profile removes Spot-reclaim noise from the numbers).

## Acceptance criteria

- Sarek completes at ≥3 scale points (incl. at least one ≥100-genome run) with results in S3.
- `benchmarks/results.csv` has runtime **and** cost (and cost-per-genome) per run.
- A short written scaling analysis lands in the README.

## References

- [nf-core/sarek](https://nf-co.re/sarek) · [Nextflow execution reports](https://www.nextflow.io/docs/latest/tracing.html)
- [1000 Genomes](https://www.internationalgenome.org/) · [PGP-UK](https://www.personalgenomes.org.uk/)
- Docs: `README.md` → Benchmarking; `benchmarks/`
- Related: `04-benchmark-storage.md`, `26-benchmark-sentieon-vs-gatk.md`, `07-cost-allocation-tags.md`
