## Summary

Curate the scattered documentation into a coherent **"playbook"** — the hackathon's stated headline output ("a practical, open playbook that helps bioinformaticians run reproducible genomic pipelines in the cloud with confidence"). This is the reference/decision layer that sits above the 30-minute on-ramp (`28-onboarding-quickstart.md`): architecture, decision guides, cost guidance, a troubleshooting index, and the benchmarking write-up.

**Difficulty:** easy · **Effort:** medium

## Background

The knowledge exists but is spread across `README.md` (long), `DEBUGGING.md`, `SEQERA_BATCH_FORGE_FINDINGS_clean.md`, the `benchmarks/` templates, and (soon) the benchmarking results. A hackathon team — and anyone reading afterwards — needs a navigable playbook that answers "where do I run this, how do I troubleshoot it, and what does it actually cost", with the trade-offs laid out. This issue is the writing/curation task that ties the others' outputs together; it's a great non-code contribution for team members who'd rather write than code.

## What to do

- [ ] Establish a docs structure (a `docs/` folder or a restructured README with a clear ToC): Overview → Getting Started (links `28`) → Architecture → **Decision guides** → Configuration reference → Benchmarking results → Troubleshooting → Cost.
- [ ] Write the **decision guides** the hackathon asks for, backed by the benchmark data as it lands:
  - Batch vs HealthOmics (`27`), storage strategy (`04`/`22`), Spot vs On-Demand (`06`/`30`), GATK vs Sentieon (`26`).
- [ ] Keep the **configuration reference** authoritative: document every context key + the profiles (`19`); add a check (or a note) so the README table can't drift from `bin/aws_batch_squared.ts`.
- [ ] Build a **troubleshooting index** from `DEBUGGING.md` — symptom → one-line diagnosis → the `nf-debug.sh` command.
- [ ] Fold the reusable, non-proprietary architecture insights from `SEQERA_BATCH_FORGE_FINDINGS_clean.md` into an "how it works / why these choices" section.
- [ ] Add lightweight ADRs (architecture decision records) for the big calls (head=on-demand/work=Spot, S3-as-workdir, stock AMI + user-data), so the *reasoning* is captured, not just the result.

## Implementation pointers

- **`README.md`** / new **`docs/`** — prefer a short README that links into deeper docs over one very long file; make the ToC the map.
- **Config reference** — a small script/test that asserts every context key in `bin/aws_batch_squared.ts` appears in the README table would prevent drift (ties into `13-unit-tests.md`).
- Treat this as a **living document** updated as benchmark issues (`25`/`26`/`27`) produce numbers — leave clearly-marked placeholders for results.
- Keep provenance for anything derived from the Seqera findings; don't reproduce proprietary/Seqera-hosted specifics as if they're ours.

## Acceptance criteria

- A navigable playbook exists with a clear table of contents.
- Each decision guide (Batch/HealthOmics, storage, Spot/On-Demand, GATK/Sentieon) has a section, populated or clearly stubbed for incoming data.
- The configuration reference covers all context keys + profiles and has an anti-drift mechanism or note.
- A symptom→diagnosis troubleshooting index is in place.

## References

- [nf-core docs style](https://nf-co.re/docs) · [Diátaxis documentation framework](https://diataxis.fr/)
- [Architecture decision records](https://adr.github.io/)
- Docs: `README.md`, `DEBUGGING.md`, `SEQERA_BATCH_FORGE_FINDINGS_clean.md`, `benchmarks/`
- Related: `28-onboarding-quickstart.md` (the on-ramp this sits above), and all benchmarking/decision issues
