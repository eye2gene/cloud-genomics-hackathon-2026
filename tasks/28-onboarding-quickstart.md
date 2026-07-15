## Summary

Create a **zero-to-first-run onboarding path** aimed at bioinformaticians who are *not* cloud experts: a scripted/checked "deploy → submit a 1-genome sarek run → see results in S3" flow that a hackathon team can complete in well under an hour, with the common failure modes pre-answered.

**Difficulty:** easy · **Effort:** medium

## Background

The hackathon audience is PhD students, postdocs, and research staff grouped by experience — many will be new to AWS/CDK. The current README is thorough but long; a first-time team needs a **short, guided, verifiable** on-ramp so they spend the day doing genomics and benchmarking, not debugging bootstrap. This is the highest-leverage "good first issue" because it unblocks every other team.

The pieces mostly exist — Quick start, submit instructions, `scripts/nf-debug.sh`, `DEBUGGING.md` — but they're not stitched into one guided, checked flow with a definitive "did it work?" signal.

## What to do

- [ ] Write a single **Getting Started (30 minutes)** guide: prerequisites check → `bootstrap` → `deploy` → submit the 1-genome smoke test → confirm results in S3.
- [ ] Provide a `scripts/smoke-test.sh` that submits the 1-genome run and polls to a clear PASS/FAIL (wrapping `nf-debug.sh`).
- [ ] Add a short **"first-run troubleshooting"** list surfacing the top failure modes already documented in `DEBUGGING.md` (nodes not joining ECS, image build, IAM), each with the one command that diagnoses it.
- [ ] Note the AWS Kiro companion (from the hackathon brief) where it helps scaffold config.
- [ ] Keep it copy-pasteable and sandbox-account friendly (assume least prior AWS knowledge).

## Implementation pointers

- **`README.md`** — a new, top-of-file "Getting Started (30 min)" section that links out to the deep-dive rather than front-loading it; make the happy path linear and verifiable.
- **`scripts/smoke-test.sh`** — submit `nf-core/sarek -r <rev>` on the 1-genome samplesheet, poll job status, print a clear PASS/FAIL + where results/logs landed. Build on `scripts/nf-debug.sh`.
- **`DEBUGGING.md`** — cross-link the top-3 first-run failures; don't duplicate, just index them.
- Pairs with `19-deployment-profiles.md` (a `dev` profile = the cheapest, fastest first deploy) and `20-pin-pipeline-revision.md` (the smoke test pins `-r`).

## Acceptance criteria

- A newcomer can go from clone → first successful 1-genome run using only the Getting Started section.
- `scripts/smoke-test.sh` returns an unambiguous PASS/FAIL and points to results/logs.
- The top first-run failure modes are indexed with a one-line diagnosis each.

## References

- [AWS CDK getting started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
- [nf-core/sarek quick start](https://nf-co.re/sarek)
- Docs/code: `README.md` → Quick start, `scripts/nf-debug.sh`, `DEBUGGING.md`
- Related: `19-deployment-profiles.md`, `20-pin-pipeline-revision.md`
