## Summary

Scope the IAM policies down to least privilege. Several policies currently use broad `Resource: "*"` and wildcard actions (`s3:*` on the bucket, `batch:*Job`) plus the broad `AmazonS3ReadOnlyAccess` managed policy.

**Difficulty:** medium · **Effort:** medium

## Background

`lib/iam-stack.ts` and `lib/nextflow-stack.ts` grant more than they need:
- `s3:*` on the workflow bucket, and `AmazonS3ReadOnlyAccess` (read on **all** buckets) attached to the instance role.
- `batch:*Job` and `batch:*JobDefinition` with broad scoping.

A cleaner model is a clear split of duties: **InstanceRole** (scoped S3 read/write on the workflow bucket + Batch submit), **ExecutionRole** (image pull + secrets), **ServiceRole** (`AWSBatchServiceRole`). Scope actions to the specific verbs actually used and resources to specific ARNs.

**Two concrete cleanups found in the code:**
- **`batchJobRole` is dead code.** `lib/iam-stack.ts` creates `batchJobRole` and it's only ever surfaced as a CfnOutput (`lib/nextflow-batch-stack.ts`) — it is **never attached to any job definition**. The head node uses `nextflowJobRole` (`lib/nextflow-stack.ts`) and the generic job def sets no role. Either wire it up or remove it.
- **No `ExecutionRole` exists at all.** There is currently no dedicated ECS task-execution role (image pull + secrets). Seqera Forge uses a dedicated `-ExecutionRole` trusted by `ecs-tasks.amazonaws.com` with `AmazonECSTaskExecutionRolePolicy` (+ secrets) — adopting that three-role split (InstanceRole / ExecutionRole / ServiceRole) is the cleaner target model (see `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §7).

## What to do

- [ ] Enumerate the S3 and Batch actions actually needed at runtime and replace wildcards with explicit action lists.
- [ ] Remove or replace `AmazonS3ReadOnlyAccess` with a bucket-scoped read policy if broad read isn't required.
- [ ] Confirm the head node can still submit/describe jobs and read/write the bucket after tightening.
- [ ] Pair this with the `cdk-nag` issue to catch remaining over-broad grants automatically.

## Implementation pointers

- **`lib/iam-stack.ts`** — `batchInstanceRole` attaches `AmazonS3ReadOnlyAccess` (reads **all** buckets) plus an inline `s3:*` on the workflow bucket; `batchJobRole` also uses `s3:*`. Replace the wildcards with explicit action lists and drop/replace the read-all managed policy.
- **`lib/nextflow-stack.ts`** — `nextflowJobRole` uses `AmazonS3ReadOnlyAccess`, `s3:*` on the bucket, and `batch:*Job` / `batch:*JobDefinition`. Scope actions to those actually used at runtime.
- Pair with the `cdk-nag` issue to catch remaining over-broad grants automatically.

## Acceptance criteria

- No unnecessary `*` actions/resources remain in the roles.
- A full run (head + child jobs, S3 read/write) still succeeds.

## References

- [IAM best practices — grant least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)
- [Amazon S3 actions](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html) · [AWS Batch actions](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsbatch.html)
- Code: `lib/iam-stack.ts`, `lib/nextflow-stack.ts`
