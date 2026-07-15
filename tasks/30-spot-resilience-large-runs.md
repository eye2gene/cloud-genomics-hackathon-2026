## Summary

Make large runs (100–1000 genomes) **survive Spot interruptions** without losing hours of progress. At that fan-out, Spot reclaims are a near-certainty, so the platform must retry interrupted tasks, resume cleanly from the S3 work dir, and diversify Spot pools — and the resume procedure must be documented.

**Difficulty:** medium · **Effort:** medium

## Background

The design is already Spot-friendly in the right places — the head node runs On-Demand (so the driver is never reclaimed), child jobs default to Spot, the entrypoint syncs the `.nextflow` session cache to S3, and `aws.batch.maxSpotAttempts = 5` is set. But a 1000-genome run pushes hundreds of concurrent Spot tasks, and several gaps make a large run more fragile than it needs to be:

- **No task-level `errorStrategy`/`maxRetries`** for non-Spot transient failures or OOM (see `21-head-jvm-and-task-retries.md`).
- **Narrow Spot pools.** The Spot CE uses `optimal` by default; a wider, deliberately diverse instance-type list (across families/sizes/AZs) gives `SPOT_PRICE_CAPACITY_OPTIMIZED` more pools to avoid, cutting interruption rate.
- **Resume isn't documented.** `-resume` works (the session cache is in S3), but there's no written "a run died — how do I restart it and skip completed work" procedure, and the cache-restore path should be verified end-to-end at scale.
- **No On-Demand fallback** for tasks that keep getting reclaimed — an optional escalation (retry N times on Spot, then route to the On-Demand queue) prevents a single unlucky task from stalling a huge run.

This is the reliability half of "run 1000 genomes" (Outcome 2/3) and pairs tightly with the benchmarking work.

## What to do

- [ ] Add default task retries with a sane `errorStrategy` (retry on Spot-reclaim + transient/OOM exit codes) — coordinate with `21` so this isn't duplicated.
- [ ] Widen and diversify the Spot instance-type list (more families/sizes) so `SPOT_PRICE_CAPACITY_OPTIMIZED` has more pools; verify capacity across AZs.
- [ ] Verify and **document the `-resume` procedure**: how the S3 session cache is restored, how to relaunch a failed run so completed tasks are skipped (the `Cached process` path), and any gotchas.
- [ ] (Optional) Add an On-Demand fallback: after repeated Spot interruptions, route the task to the On-Demand queue (per-process `queue` or an escalating retry).
- [ ] Prove it: run a large scenario, force/observe interruptions, and confirm the run completes via retries + resume.

## Implementation pointers

- **`docker/nextflow-head/nextflow.aws.sh`** — the generated `nextflow.config` already sets `maxSpotAttempts`; add `process.errorStrategy`/`maxRetries` (shared with `21`) and document the resume flow. The session-cache sync (`aws s3 sync .nextflow …`) is the resume backbone — verify it at scale.
- **`lib/batch-stack.ts`** — broaden `SpotComputeEnv` instance types (surface via `batchSpotInstanceTypes` / a size profile in `19`).
- **On-Demand fallback** — Nextflow can pin a process to a different `queue`; or use `aws.batch.maxSpotAttempts` + a `withLabel` override to the On-Demand queue for stubborn tasks.
- Coordinate with `06-dedicated-head-ce.md` (driver isolation) and `25-benchmark-scale-runs.md` (this is what makes the big runs finish).

## Acceptance criteria

- A ≥100-genome run completes despite Spot interruptions, via retries and/or resume.
- The `-resume` / restart-a-failed-run procedure is documented and verified (completed tasks are skipped).
- Spot pool diversity is configurable and documented; (optional) an On-Demand fallback exists for repeatedly-interrupted tasks.

## References

- [AWS Batch Spot best practices](https://docs.aws.amazon.com/batch/latest/userguide/spot_best_practices.html) · [`SPOT_PRICE_CAPACITY_OPTIMIZED`](https://docs.aws.amazon.com/batch/latest/userguide/allocation-strategies.html)
- [Nextflow `-resume` / caching](https://www.nextflow.io/docs/latest/cache-and-resume.html) · [`errorStrategy`](https://www.nextflow.io/docs/latest/process.html#errorstrategy)
- Code: `docker/nextflow-head/nextflow.aws.sh`, `lib/batch-stack.ts`
- Related: `21-head-jvm-and-task-retries.md`, `06-dedicated-head-ce.md`, `25-benchmark-scale-runs.md`
