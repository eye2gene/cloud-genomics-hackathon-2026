## Summary

Turn the cost-allocation **tags** (`07-cost-allocation-tags.md`) into actual **per-run / per-scale cost reporting** — so the benchmarking cost numbers (cost-per-genome) are pulled automatically rather than hand-copied from Cost Explorer. Start with a script that resolves a run's cost from the Cost Explorer API and appends it to the results CSV; optionally build a dashboard.

**Difficulty:** medium · **Effort:** medium

## Background

Cost is half of the hackathon's headline benchmarking output (Outcome 3: "real cost and runtime data at each scale point"). `07-cost-allocation-tags.md` makes spend *attributable* by tagging resources (and per-run via a `run-id` tag), but someone still has to read the numbers back and compute cost-per-genome by hand — tedious and error-prone across 6 scale points × multiple variants (storage, Sentieon, Graviton, service).

This issue closes that loop: given a `run-id` (or a scale/variant), fetch the cost and write it into `benchmarks/results.csv` automatically. That makes the whole benchmarking sweep reproducible and the cost column trustworthy.

> Note: Cost Explorer data lags (hours) and cost-allocation tags must be **activated** in Billing before they appear (called out in `07`). For near-real-time estimates, vCPU-hours × instance price is a good cross-check.

## What to do

- [ ] Depend on `07-cost-allocation-tags.md` being in place (baseline tags + per-run `run-id` tag on submitted jobs).
- [ ] Write a `scripts/` helper that, given a `run-id` (and/or date range), queries the Cost Explorer API filtered by tag and returns the run's cost, then appends/updates the row in `benchmarks/results.csv` (including derived cost-per-genome).
- [ ] Add a vCPU-hours × on-demand-price **estimate** as an independent cross-check (works before Cost Explorer settles, and for Spot sanity-checking).
- [ ] (Optional) Stand up a lightweight dashboard: a CUR → Athena → QuickSight setup, or a simple generated chart/summary from `results.csv`, showing cost-per-genome vs scale and across variants.
- [ ] Document how to activate the tags and run the report.

## Implementation pointers

- **`scripts/`** — a `cost-report.sh`/`.ts` alongside `nf-debug.sh` using the Cost Explorer `GetCostAndUsage` API with a `Tag` filter on `run-id` (or `project`/`team`). Bun can run a TS script directly.
- **Cost estimate cross-check** — combine Nextflow's `-with-trace` (per-task vCPU/time) with instance pricing for an at-run-time estimate that doesn't wait on Cost Explorer.
- **`benchmarks/results.csv`** — this issue *populates* the `estimated_cost_usd` / `cost_per_genome_usd` columns that already exist in the schema; keep it the single source of truth.
- **Dashboard (optional)** — CUR + Athena + QuickSight is the AWS-native path; for the hackathon a generated summary chart from `results.csv` may be enough (align with the `dataviz` approach if rendering).
- Pairs with `25`/`26`/`27`/`31` — every benchmark variant becomes a labelled, costed row automatically.

## Acceptance criteria

- Running the helper for a given `run-id` returns its cost and writes cost + cost-per-genome into `benchmarks/results.csv`.
- An independent vCPU-hours-based estimate is available as a cross-check.
- Activation + usage documented; (optional) a dashboard or summary chart shows cost-per-genome vs scale/variant.

## References

- [AWS Cost Explorer API (`GetCostAndUsage`)](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html) · [Cost allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
- [Cost and Usage Reports + Athena](https://docs.aws.amazon.com/cur/latest/userguide/cur-query-athena.html) · [Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/welcome.html)
- Related: `07-cost-allocation-tags.md`, `25-benchmark-scale-runs.md`, `26`, `27`, `31`
