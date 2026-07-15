## Summary

Two related pieces of configuration ergonomics, best done together: **(A)** surface the compute knobs that are still hardcoded or unwired (worker EBS/scratch volume sizes), and **(B)** add **named deployment profiles** that bundle all the knobs into a few opinionated presets — `dev` / `production` and analysis-size presets (`small` / `medium` / `large`). Instead of setting a dozen `-c key=value` flags correctly and consistently, an operator picks one profile and gets a coherent configuration; the size presets can only exist once the size knobs (A) are configurable.

**Difficulty:** medium · **Effort:** medium

## Background

Compute *capacity* is already configurable (`onDemand/spotMinCpus`, `*MaxCpus`, `batchOnDemand/SpotInstanceTypes`). Two things are still awkward:

1. **Some "size of compute" knobs aren't configurable.** In `lib/launch-template-stack.ts` the launch template attaches three EBS volumes with fixed sizes — `/dev/xvda` (root, **hardcoded 100 GB**), `/dev/xvdcz` (**hardcoded 22 GB**), and `/dev/xvdba` (sized from `dockerStorageVolumeSize`, default 100 GB) — but **`dockerStorageVolumeSize` is never passed** from `lib/nextflow-batch-stack.ts`, so it's stuck at the default. For genomics, disk is often what fills up ("no space left on device"), so worker disk size needs to be tunable. (This is separate from the faster local-NVMe path in `03-nvme-scratch.md` — this is about sizing the default EBS path.)

2. **The knobs interact and are error-prone individually.** A "production" run wants on-demand head + dedicated head CE + longer retention + pinned versions + tighter IAM; a quick "dev" run wants tiny caps + short retention + spot everything. Getting one wrong silently changes cost or reliability. A **profile** is a preset that fills in sensible values for a whole scenario, which individual `-c` flags can still override. Two orthogonal axes:
   - **Environment profile** — `dev` vs `production` (reliability, retention, IAM strictness, version pinning, dedicated head CE).
   - **Analysis-size profile** — `small` / `medium` / `large` (max vCPUs, instance-type families, head memory/timeout, **and the volume sizes from (A)**) matched to how many genomes a run processes.

Together this is the single ergonomic front door that pulls in head sizing, dedicated head CE, log retention, volume sizes, version pinning, and IAM. It directly serves "configure things better / different profiles for production / size of analysis".

## What to do

**(A) Make the remaining size knobs configurable**
- [ ] Surface `dockerStorageVolumeSize` (already a prop — just thread it through) plus `rootVolumeSize` (and optionally a secondary/scratch size) as context keys, defaulting to today's values.
- [ ] Replace the literal `100` / `22` in the launch template with the new props.

**(B) Add deployment profiles**
- [ ] Define a `profiles` map (TypeScript objects) of preset configs — at minimum `dev` and `production`, plus size presets.
- [ ] Add a `profile` (and optionally `size`) context key; resolve to a base config, then let explicit `-c` keys override (precedence: explicit context > profile > built-in default).
- [ ] Keep the current "no profile" behaviour unchanged (defaults as today).
- [ ] Document the new size keys, each profile's values, and the override precedence in the README config table.

## Implementation pointers

- **`bin/aws_batch_squared.ts`** — where context is read into `NextflowBatchConfig`. Add the new size keys, then a `profiles` record (e.g. `lib/profiles.ts`) and merge `{ ...defaults, ...profiles[profile], ...explicitContext }`. Log the resolved profile so a deploy is auditable; fail fast on an unknown profile name (like the existing validation block).
- **`lib/nextflow-batch-stack.ts`** / **`lib/launch-template-stack.ts`** — thread the volume-size props into `LaunchTemplateStack` (the `dockerStorageVolumeSize` prop already exists but isn't populated — start there) and replace the hardcoded `100` / `22`.
- Good candidate values per profile:
  - `dev` — small `*MaxCpus`, spot-heavy, short `workDirExpirationDays` / `logRetentionDays`, small volumes, `nextflowVersion` unpinned OK.
  - `production` — on-demand head (`06-dedicated-head-ce.md`), pinned `nextflowVersion` (`17-pin-nextflow-version.md`), longer retention, tighter IAM (`09-tighten-iam.md`), cost-allocation tags (`07-cost-allocation-tags.md`), hardening (`24-security-production-hardening.md`).
  - size presets — scale `spot/onDemandMaxCpus`, `headMemory`/`headTimeoutSeconds` (`05-head-node-sizing.md`), and the (A) volume sizes.
- **`README.md`** — add the size keys to the config table, plus a table per profile and a short "how overrides work" note.

## Acceptance criteria

- Worker root and docker/scratch volume sizes can be set via context (defaults reproduce today's 100 / 22 / 100 GB).
- `-c profile=production` (and `-c size=large`) deploys a coherent config without needing other flags; individual `-c` flags still override.
- No profile = today's behaviour.
- README documents the new size keys, each profile, and the precedence rules.

## References

- [CDK context](https://docs.aws.amazon.com/cdk/v2/guide/context.html)
- [EC2 launch template block device mappings](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/launch-template-block-device-mapping.html) · [`gp3` volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html)
- Code: `bin/aws_batch_squared.ts`, `lib/nextflow-batch-stack.ts`, `lib/launch-template-stack.ts`
- Related: `03` (NVMe scratch), `05` (head sizing), `06`, `07`, `08`, `09`, `17`, `24` — the knobs a profile bundles
