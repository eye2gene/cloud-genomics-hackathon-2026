## Summary

Add an **optional Wave + Fusion data path** as an alternative to the current AWS-CLI staging model. This is the single change that most closes the performance gap with Seqera Batch Forge: instead of copying inputs/outputs to and from S3 per task, Fusion mounts the S3 work bucket as a POSIX filesystem cached on local NVMe, so S3 *is* the work directory.

**Difficulty:** hard · **Effort:** large

## Background

The reverse-engineered Forge environment (`SEQERA_BATCH_FORGE_FINDINGS_clean.md` §6) gets its speed from **Wave** (rebuilds each process container on the fly to inject the Fusion client) + **Fusion** (mounts S3 as POSIX, cached on NVMe at `/scratch/fusion`, bind-mounted to the task's working dir). There's no explicit staging step and no shared filesystem.

This platform currently uses the **classic** path: AWS CLI on the host, bind-mounted into tasks via `aws.batch.cliPath`, with S3 sync in the entrypoint. That's simpler and dependency-free but spends real time on staging for I/O-heavy steps.

Enabling Fusion is mostly a **runtime config** change (Nextflow's `fusion.enabled` / `wave.enabled`) plus a few infrastructure prerequisites; the infra is largely identical either way. It should be an **opt-in toggle**, because it has real trade-offs.

> Trade-offs / prerequisites: Fusion tasks must run **`privileged: true`** (FUSE mount), the work compute environment must use **NVMe instance types** (see `03-nvme-scratch.md`), and **Fusion at production scale needs a Seqera licence**. Wave/Fusion also depend on Seqera-hosted services (`wave.seqera.io`). This is why it's optional rather than the default.

## What to do

- [ ] Add a context toggle (e.g. `dataPath: "classic" | "fusion"`) surfaced through config.
- [ ] When `fusion`: emit `wave.enabled = true`, `fusion.enabled = true`, and Fusion NVMe cache settings in the generated `nextflow.config`; set the work CE to NVMe instance types; format/mount NVMe as scratch (reuse `03-nvme-scratch.md`); run child tasks `privileged` with the scratch bind-mounted to the task work dir.
- [ ] Keep `classic` as the default so nothing breaks and no external dependency/licence is required out of the box.
- [ ] Benchmark `classic` vs `fusion` on the same workload (feeds `04-benchmark-storage.md`) and document the licence/privileged trade-offs.

## Implementation pointers

- **`docker/nextflow-head/nextflow.aws.sh`** — conditionally write `wave { enabled = true }` / `fusion { enabled = true }` (+ Fusion cache path) into `nextflow.config` when the toggle is on.
- **`lib/batch-stack.ts`** — the Spot/work CE needs NVMe instance types (shared with `03-nvme-scratch.md`).
- **`lib/launch-template-stack.ts`** — NVMe detect + LVM stripe + mount at a scratch path (shared with `03`).
- **Child job definition / container options** — `privileged: true` and the scratch→workdir mount when Fusion is enabled. Note the current head job def sets no execution role; a private Wave registry pull needs one (see `09-tighten-iam.md`).
- **`bin/aws_batch_squared.ts`** — the `dataPath` toggle; a `production`/performance profile (`19-deployment-profiles.md`) can select it.

## Acceptance criteria

- With the toggle off, behaviour is unchanged (classic AWS-CLI staging, no new dependencies).
- With the toggle on, a real pipeline runs using Fusion (log shows `Fusion Info:` with the NVMe `disk_cache_size`), tasks run privileged on NVMe instances, and no explicit per-task S3 staging occurs.
- Trade-offs (licence, privileged, NVMe requirement) documented.

## References

- [Seqera Fusion](https://docs.seqera.io/fusion) · [Wave containers](https://docs.seqera.io/wave)
- [Nextflow Fusion / Wave config](https://www.nextflow.io/docs/latest/fusion.html)
- [Amazon EC2 instance store (NVMe)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)
- Reference: `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §4, §5b, §6
- Related: `03-nvme-scratch.md`, `04-benchmark-storage.md`, `09-tighten-iam.md`, `19-deployment-profiles.md`
