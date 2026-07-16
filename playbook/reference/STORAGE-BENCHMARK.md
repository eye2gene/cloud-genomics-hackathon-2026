# Storage Benchmark Results

## Context

When running Nextflow on AWS Batch with an S3 work directory, tasks stage data locally before processing. With multiple concurrent tasks on the same instance sharing a single EBS volume, throughput becomes the bottleneck.

## Test Setup

- Instance: m5.4xlarge (16 vCPUs, 64GB RAM)
- Test: 10 concurrent downloads of a 39GB CRAM file from S3 (same region, through VPC endpoint)
- Simulates: BASERECALIBRATOR/APPLYBQSR tasks all staging the same BAM/CRAM concurrently

## Results

| Storage Config | Per-download time | Aggregate throughput | Cost |
|---------------|------------------|---------------------|------|
| gp3 baseline (3000 IOPS, 125 MB/s) | 51 minutes | ~128 MB/s | Included |
| gp3 bumped (10000 IOPS, 1000 MB/s) | 13 minutes | ~490 MB/s | ~$40/month extra |
| Instance store NVMe RAID 0 (m5d.4xlarge) | 12.7 minutes | ~512 MB/s | Included with instance |

## Findings

1. **gp3 baseline is the bottleneck** — disk utilization at 100%, each download throttled to ~12.8 MB/s
2. **Bumping gp3 throughput gives 3.8× improvement** — from 51 min to 13 min per staging operation
3. **Instance store RAID 0 matches bumped gp3** — no additional benefit because network bandwidth (~500 MB/s aggregate from S3) becomes the ceiling
4. **The bottleneck shifts from disk to network** at ~500 MB/s with 10 concurrent downloads on m5.4xlarge

## Recommendation

Use gp3 with `Throughput: 1000` and `Iops: 10000` in the launch template. This provides:
- Near-maximum performance for S3 staging workloads
- Simpler than instance store (no RAID setup, device detection, or mixed instance type logic)
- Predictable capacity (500GB guaranteed vs variable instance store sizes)
- ~$40/month additional cost per instance while running (instances scale to zero when idle)

## Implementation

In `batch-template.yaml` launch template BlockDeviceMappings:
```yaml
- DeviceName: /dev/xvdba
  Ebs:
    VolumeSize: 500
    VolumeType: gp3
    Iops: 10000
    Throughput: 1000
    Encrypted: true
    DeleteOnTermination: true
```

## Sizing

For the 5-sample sarek run (our standard test):
- Peak concurrent staged data: ~10 tasks × 45GB CRAM = 450GB
- Plus XFS overhead: ~3-5%
- 500GB is tight but workable

For test_full_germline_aws (1 sample, 30x WGS, all variant callers):
- MARKDUPLICATES writes 137GB alone
- 20 BASERECALIBRATOR tasks × 50GB each (but staged sequentially, not all concurrent)
- Peak observed: ~400GB on a single instance
- 500GB sufficient with `scratch = '/tmp'` directing staging there

For production (100+ samples):
- Consider 1TB volume
- Or use EFS/FSx for Lustre (shared filesystem, no staging overhead)

## XFS Preallocation Note

On fast storage (NVMe instance store), XFS pre-allocates disk space aggressively for concurrent sequential writers. This makes `df` report more space used than `du`. The pre-allocated space is released when files are closed. On gp3 EBS, this effect is minimal (~3GB overhead vs ~180GB on NVMe).

Mount with `allocsize=64k` to limit preallocation if needed:
```bash
mount -o allocsize=64k /dev/xvdba /mnt/scratch
```
