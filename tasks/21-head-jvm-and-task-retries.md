## Summary

Set the head-node **JVM heap sizing** and add **default task retry/error-strategy** settings in the generated `nextflow.config`, so (a) the driver actually uses the memory it's given and (b) transient/Spot/OOM task failures are retried instead of failing the run.

**Difficulty:** easy · **Effort:** small

## Background

The head-node entrypoint (`docker/nextflow-head/nextflow.aws.sh`) writes a minimal `nextflow.config` and runs the driver. Two robustness settings are missing:

- **No JVM heap sizing.** Nextflow runs on the JVM, which by default sizes its heap to a fraction of container memory — and inside a container without explicit flags it can under- or mis-size. If you bump head memory (see `05-head-node-sizing.md`), the driver won't necessarily use it. Seqera's `nf-launcher` sets `NXF_JVM_ARGS=-XX:InitialRAMPercentage=40 -XX:MaxRAMPercentage=75` for exactly this reason (see `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §8b).
- **No default retry policy for child tasks.** The generated config sets `aws.batch.maxSpotAttempts = 5` (Spot reclaim) but no `process.errorStrategy` / `maxRetries`. So a task that hits a transient error or an out-of-memory kill fails the whole run. The nf-core convention is to retry with escalating resources keyed on `task.attempt`.

Both are small entrypoint/config additions, high value for reliability at scale.

## What to do

- [ ] Export `NXF_OPTS` / `NXF_JVM_ARGS` (e.g. `-XX:MaxRAMPercentage=75`) in the head-node entrypoint so the driver JVM uses the container's memory; make it overridable via env.
- [ ] Add sensible default retry directives to the generated `nextflow.config` — e.g. `process.errorStrategy` = retry on transient/OOM exit codes, `process.maxRetries` = 2–3 — while leaving them overridable by a user-supplied config/profile.
- [ ] (Optional) Add a dynamic-resource retry example (bump memory with `task.attempt`) to the docs.
- [ ] Verify a deliberately-OOM'd task retries and the run survives.

## Implementation pointers

- **`docker/nextflow-head/nextflow.aws.sh`** — set `export NXF_OPTS="-XX:MaxRAMPercentage=75 ${NXF_OPTS:-}"` near the top (respect any inherited value); add the retry directives to both branches that write `$NF_CONFIG` (append-to-existing and create-new), after the existing `aws.batch.maxSpotAttempts` line. Keep them as defaults that a supplied `nextflow.config` can override.
- Keep it aligned with `05-head-node-sizing.md` (memory the JVM flags then actually use) and `19-deployment-profiles.md` (a `production` profile can raise retries).

## Acceptance criteria

- The driver JVM heap scales with the head-node container memory.
- A transient/OOM child-task failure is retried per the default policy instead of failing the run.
- Both settings remain overridable by a user config/profile.

## References

- [Nextflow `errorStrategy` / `maxRetries` / dynamic retries](https://www.nextflow.io/docs/latest/process.html#errorstrategy)
- [Nextflow environment variables (`NXF_OPTS`)](https://www.nextflow.io/docs/latest/config.html#environment-variables)
- [JVM container memory flags (`MaxRAMPercentage`)](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/what-is-corretto-17.html)
- Code: `docker/nextflow-head/nextflow.aws.sh`
- Related: `05-head-node-sizing.md`, `19-deployment-profiles.md`
