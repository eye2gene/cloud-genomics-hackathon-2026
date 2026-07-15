## Summary

Benchmark the candidate scratch/shared-storage strategies against the **same** workload and scales, capturing both **runtime and cost**. The storage layer is usually the single biggest lever on genomics pipeline performance and spend, so a fair comparison is a high-value output.

**Difficulty:** medium · **Effort:** large

## Background

The platform currently stages inputs/outputs with the AWS CLI (`aws.batch.cliPath`) and exposes reference data via Mountpoint for S3. Several alternatives trade cost, speed, and complexity differently and are worth measuring head-to-head.

Candidates:
- AWS CLI staging (current baseline)
- Tuned `gp3` / `io2` EBS scratch
- Local NVMe instance-store (see the NVMe scratch issue)
- FUSE-over-S3 (e.g. s3fs)
- Amazon EFS (shared NFS)
- Amazon FSx for Lustre (S3-linked)

Use the benchmarking harness already sketched in the repo: `benchmarks/samplesheets/` (input templates) and `benchmarks/results.template.csv` (results schema), and the scale scenarios in `README.md` → Benchmarking (1 / 10 / 50 / 100 / 500 / 1000 genomes).

## What to do

- [ ] Define a fixed workload (pipeline + revision + samplesheet) and hold it constant.
- [ ] Implement/toggle each storage strategy and run at a few representative scales.
- [ ] Record wall-clock time, vCPU-hours, and estimated cost per strategy in `benchmarks/results.csv`; derive cost-per-genome.
- [ ] Summarise findings (which strategy wins where) back into the README.

## Implementation pointers

- Make the storage strategy a **context toggle** in **`bin/aws_batch_squared.ts`** so each benchmark run is a clean deploy variant.
- **`lib/launch-template-stack.ts`** — per-strategy mount/staging setup (Mountpoint, NVMe, s3fs); **`lib/batch-stack.ts`** — instance types (NVMe families for the local-disk option).
- For the managed-filesystem options, add constructs: `aws-cdk-lib/aws-efs` (EFS) and `aws-cdk-lib/aws-fsx` (FSx for Lustre), placed in the VPC/subnets from **`lib/vpc-stack.ts`** and mounted via the launch template.
- **`benchmarks/`** — capture results in `results.template.csv`; inputs under `benchmarks/samplesheets/`.

## Acceptance criteria

- At least three strategies benchmarked on the identical workload at ≥2 scales.
- Runtime **and** cost captured per run in the results CSV.
- A short written comparison/recommendation.

## References

- [EBS volume types (`gp3`, `io2`)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html)
- [Amazon FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html) · [Amazon EFS](https://docs.aws.amazon.com/efs/latest/ug/whatisefs.html) · [Mountpoint for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint.html) · [s3fs](https://github.com/s3fs-fuse/s3fs-fuse)
- [AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
- Project docs: `README.md` → Benchmarking; `benchmarks/`
