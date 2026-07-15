## Summary

Run `nf-core/sarek` with the **Sentieon-accelerated** variant caller alongside the standard **GATK HaplotypeCaller** path, on the same data, and compare runtime, cost, and concordance. This is hackathon **Outcome 4** — the standard-vs-Sentieon comparison.

**Difficulty:** medium · **Effort:** medium

## Background

Sentieon reimplements GATK-equivalent germline calling with much faster, deterministic tools — often a large runtime (and therefore cost) win, at the price of a commercial **licence**. Sarek supports both: `--tools haplotypecaller` (GATK) vs `--tools sentieon_haplotyper`. The benchmarking schema already anticipates this — `benchmarks/results.template.csv` has a `workflow_variant` column and a seeded `sentieon-haplotyper` row.

There's prior Sentieon material in this repo under `old/sentieon/` (a working `main.nf`, `nextflow.config`/`aws.config`, a head-node Dockerfile, and a `sentieon.json` licence config) that can seed the config and licensing setup.

> **Licence handling.** Sentieon needs a licence (often a licence server or a `SENTIEON_LICENSE` env/URL). Provide it via Secrets Manager / an env var to the task — do **not** commit it. Gate this issue on having a licence available for the sandbox accounts.

## What to do

- [ ] Wire Sentieon licensing into the run (env var / secret), reusing the `old/sentieon/` config where useful.
- [ ] Run sarek at ≥1–2 scale points with `--tools haplotypecaller` and again with `--tools sentieon_haplotyper`, holding everything else constant.
- [ ] Record both variants in `benchmarks/results.csv` (the `workflow_variant` column) with runtime + cost + cost-per-genome.
- [ ] Compare **concordance** of the call sets (e.g. `bcftools`/`hap.py`) so the speed-up isn't mistaken for a change in results.
- [ ] Write up the trade-off: runtime/cost delta vs licence cost and accuracy.

## Implementation pointers

- **Pipeline config** — sarek `--tools sentieon_haplotyper`; see `old/sentieon/` for a known-good Nextflow config and the `sentieon.json` licence shape.
- **Licence** — inject `SENTIEON_LICENSE` (server host:port or a resolvable URL) via the task env / Secrets Manager; pair with the ExecutionRole/secrets work in `09-tighten-iam.md`.
- **Results** — same `benchmarks/results.csv`; just vary `workflow_variant`. Reuse the harness from `25-benchmark-scale-runs.md`.
- Keep the GATK run as the baseline so the comparison is apples-to-apples (same data, region, storage, scale).

## Acceptance criteria

- Both variant callers run to completion on the same input at ≥1 scale point.
- Runtime + cost recorded for each in the results CSV, with cost-per-genome.
- A concordance check confirms the call sets are equivalent (or the differences are characterised).
- A short written recommendation (when Sentieon pays for itself).

## References

- [nf-core/sarek — Sentieon](https://nf-co.re/sarek/docs/usage#sentieon) · [Sentieon DNAseq](https://www.sentieon.com/products/)
- [hap.py / benchmarking variant calls](https://github.com/Illumina/hap.py)
- Prior work: `old/sentieon/`
- Related: `25-benchmark-scale-runs.md`, `09-tighten-iam.md`
