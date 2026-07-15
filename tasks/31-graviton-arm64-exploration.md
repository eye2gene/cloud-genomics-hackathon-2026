## Summary

Explore **AWS Graviton (arm64)** compute for the worker fleet and measure the cost/runtime delta against x86 on the same sarek workload. Graviton instances are typically ~20–40% cheaper per vCPU-hour, so if the genomics containers run on arm64 it's a direct cost lever — but not every bioinformatics container is multi-arch, so this is an *exploration with a clear go/no-go*, not an assumed win.

**Difficulty:** hard · **Effort:** medium

## Background

The stack is x86-only today: the compute AMI resolves the **x86** ECS-optimized AL2 SSM parameter, the Batch CEs use x86 families (`optimal`), and the head image is `amazoncorretto:17` built for x86. Graviton (`c7g`, `m7g`, `r7g`, and NVMe `*gd` variants) can cut cost substantially — *if* the pipeline's task containers have arm64 builds. Many biocontainers/nf-core modules are now multi-arch, but coverage is incomplete, so the real question this issue answers is **"how much of sarek runs on arm64, and is it cheaper end-to-end?"**

This is naturally a **benchmark variant** (an `arch` dimension) rather than a default change.

## What to do

- [ ] Add the ability to target arm64: an arm64 ECS AMI (the `.../amazon-linux-2/recommended` **arm64** SSM parameter, or AL2023 arm64) and Graviton instance types on the work CE.
- [ ] Confirm the head-node image builds/runs on arm64 (Corretto 17 is multi-arch) — or keep the head on x86 and only move workers.
- [ ] Run sarek on Graviton workers vs x86 at ≥1 scale point; record which processes lacked arm64 containers and how they were handled (fallback, `wave`/`--platform`, or excluded).
- [ ] Record both in `benchmarks/results.csv` with an `arch` dimension: runtime, cost, cost-per-genome.
- [ ] Write up the verdict: net cost delta and the container-coverage caveat.

## Implementation pointers

- **`bin/aws_batch_squared.ts`** / **`lib/nextflow-batch-stack.ts`** — a `computeArch` / arm64 toggle that selects the arm64 AMI SSM parameter and Graviton instance types (ties into the instance-type config in `19`).
- **`lib/batch-stack.ts`** — `ec2Configuration.imageType` and instance types must match the architecture; Graviton NVMe families (`*gd`) also feed `03-nvme-scratch.md`.
- **`lib/nextflow-ecr-stack.ts`** — the head image is `amazoncorretto:17` (multi-arch); a CodeBuild arm64 build (or a manifest list) is needed only if the head runs on arm64.
- **Container coverage** — the crux. Check nf-core/sarek module containers for arm64 manifests; Wave can help build missing arch variants. Document gaps honestly.
- Reuse the harness from `25-benchmark-scale-runs.md`; hold everything but architecture constant.

## Acceptance criteria

- The platform can deploy an arm64/Graviton worker fleet (behind a toggle/profile; x86 remains default).
- Sarek runs on Graviton at ≥1 scale point; container-coverage gaps are documented with how they were handled.
- Cost/runtime for arm64 vs x86 recorded in the results CSV, with a clear cost-per-genome comparison and a go/no-go recommendation.

## References

- [AWS Graviton](https://aws.amazon.com/ec2/graviton/) · [Batch on Graviton](https://docs.aws.amazon.com/batch/latest/userguide/compute_environment_parameters.html)
- [ECS-optimized AMIs (arm64)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html) · [multi-arch containers / Wave](https://docs.seqera.io/wave)
- Related: `25-benchmark-scale-runs.md`, `03-nvme-scratch.md`, `19-deployment-profiles.md`
