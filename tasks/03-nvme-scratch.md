## Summary

Give worker jobs fast **local NVMe instance-store scratch** instead of relying on the root EBS volume, and point each task's temp/work directory at it. For I/O-heavy genomics steps this can dramatically cut runtime.

**Difficulty:** hard · **Effort:** medium

## Background

The fastest scratch on EC2 is the ephemeral NVMe physically attached to certain instance families (the `d`-suffix types). To use it well, the launch-template bootstrap must detect the NVMe disks, stripe them into one big volume with LVM, format and mount it, and the container's temp directory must be pointed there.

This touches:
- `lib/launch-template-stack.ts` — detect NVMe, `pvcreate` → `vgcreate` → `lvcreate -l 100%FREE`, `mkfs`, mount (e.g. at `/scratch`).
- `lib/batch-stack.ts` — the **work/Spot** compute environment must use NVMe instance types (e.g. `c5d,m5d,m5ad,r5d,r5ad,i3,i4i`) rather than the literal `optimal`.
- Job/container config — mount the scratch into the task and set the Nextflow task working/temp dir to it.

> Note: instance-store data is ephemeral (lost on stop/Spot reclaim). That's fine for scratch because Nextflow retries interrupted tasks, but it must not hold anything that needs to survive.

## What to do

- [ ] Detect and LVM-stripe all NVMe instance-store disks in the launch-template cloud-init; format + mount as scratch.
- [ ] Add config to set the work CE instance types to NVMe families (surface via context alongside `batchSpotInstanceTypes`).
- [ ] Mount the scratch into worker containers and point the task temp dir at it.
- [ ] Validate with a real run; capture before/after runtime (feeds the benchmarking issue).

## Implementation pointers

- **`lib/launch-template-stack.ts`** — add NVMe detection + LVM striping (`pvcreate` → `vgcreate` → `lvcreate -l 100%FREE`) + `mkfs`/mount (e.g. `/scratch`) in the cloud-init. Note today's `blockDevices` are EBS only (`/dev/xvda`, `/dev/xvdcz`, `/dev/xvdba`) — no instance-store handling yet.
- **`lib/batch-stack.ts`** — the **Spot** (`SpotComputeEnv`) `computeResources.instanceTypes` must be NVMe families instead of `optimal`.
- **`bin/aws_batch_squared.ts`** — set `batchSpotInstanceTypes` to the NVMe list (already a context key); consider adding a `scratchPath`.
- **`docker/nextflow-head/nextflow.aws.sh`** — point the task scratch/temp dir at the mount (e.g. `process.scratch`) in the generated `nextflow.config`.

## Acceptance criteria

- Worker instances mount a single striped NVMe scratch volume.
- Worker jobs write intermediates to local NVMe; the run completes successfully.
- Falls back gracefully (or is clearly gated) on instance types without NVMe.

## Seqera Batch Forge reference

Forge does **exactly this** — its launch-template bootstrap (verbatim in `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §4) is a near-copyable blueprint:

```bash
yum install -q -y nvme-cli lvm2
mkdir -p /scratch/fusion
NVME_DISKS=($(nvme list | grep 'Amazon EC2 NVMe Instance Storage' | awk '{ print $1 }'))
NUM_DISKS=${#NVME_DISKS[@]}
if   (( NUM_DISKS == 1 )); then mkfs -t xfs ${NVME_DISKS[0]}; mount ${NVME_DISKS[0]} /scratch/fusion
elif (( NUM_DISKS  > 1 )); then
  pvcreate ${NVME_DISKS[@]}; vgcreate scratch ${NVME_DISKS[@]}
  lvcreate -l 100%FREE -n volume scratch
  mkfs -t xfs /dev/mapper/scratch-volume; mount /dev/mapper/scratch-volume /scratch/fusion
fi
chmod a+w /scratch/fusion
```

Note the single-disk vs multi-disk branch (no LVM needed for one disk), `xfs` (not ext4), and the `chmod a+w` so non-root task containers can write. Forge's `-work` CE uses `c5d, i3, i4i, m5ad, m5d, r5ad, r5d` — every family has NVMe instance store. This scratch is also the prerequisite for the Fusion data path (`22-fusion-wave-datapath.md`).

## References

- [Amazon EC2 instance store](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)
- [LVM configuration guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_and_managing_logical_volumes/index)
- [Nextflow scratch directive](https://www.nextflow.io/docs/latest/process.html#scratch) and [AWS Batch executor](https://www.nextflow.io/docs/latest/aws.html)
