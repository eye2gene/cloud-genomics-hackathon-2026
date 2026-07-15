## Summary

Tune the Linux page-cache write-back thresholds (`vm.dirty_bytes` / `vm.dirty_background_bytes`) on worker instances so large sequential writes streaming to S3 don't balloon host memory or cause write stalls.

**Difficulty:** easy · **Effort:** small

## Background

Genomics tasks write large intermediate files that stream out to S3. With the default write-back settings, dirty pages can accumulate and then flush in bursts, spiking memory use and stalling I/O. Capping dirty bytes forces earlier, smoother write-back.

These are `sysctl` values set at boot on the compute instances via the launch-template cloud-init in `lib/launch-template-stack.ts`.

## What to do

- [ ] Add a cloud-init step (a `bootcmd`/`sysctl` write) in `lib/launch-template-stack.ts` setting sensible caps, e.g. `vm.dirty_bytes` ~1.2 GB and `vm.dirty_background_bytes` ~600 MB (tune to instance RAM).
- [ ] Redeploy and confirm the values on a live node (`sysctl vm.dirty_bytes vm.dirty_background_bytes`, or `scripts/nf-debug.sh ssm <i-id>`).
- [ ] Ideally quantify the effect during the storage benchmarking work.

## Implementation pointers

- **`lib/launch-template-stack.ts`** — the cloud-init in `userData.addCommands(...)`. Add the sysctls either as a `write_files` entry under `/etc/sysctl.d/*.conf` (plus `sysctl --system` in `bootcmd`) or write them directly in `bootcmd`. Size the caps relative to the worker instance RAM.
- No other stack changes needed — the launch template feeds both compute environments in **`lib/batch-stack.ts`**.

## Acceptance criteria

- New worker instances boot with the configured `vm.dirty_bytes` / `vm.dirty_background_bytes`.
- No regression in node bootstrap / ECS registration.

## References

- [Linux kernel VM sysctl documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html) (`dirty_bytes`, `dirty_background_bytes`)
- [cloud-init modules](https://cloudinit.readthedocs.io/en/latest/reference/modules.html)
