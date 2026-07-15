## Summary

Make CloudWatch log retention configurable across all log groups the stack creates, and review the S3 lifecycle windows, to keep standing costs predictable.

**Difficulty:** easy · **Effort:** small

## Background

Log-group retention is set inconsistently: `lib/batch-stack.ts` sets the container-instance log group to one week, but other groups (the Batch job group `/aws/batch/job`, the CodeBuild image-build group, and the trigger Lambda group) may default to **never expire**, which accrues cost over time. Separately, `lib/s3-stack.ts` expires work-dir intermediates after `workDirExpirationDays` (default 30) — worth confirming it matches how long runs need to stay resumable.

## What to do

- [ ] Audit every log group the stack creates and set an explicit retention (configurable via context, with a sensible default).
- [ ] Confirm/adjust the S3 work-dir lifecycle window and document the trade-off (resumability vs storage cost).
- [ ] Verify no log group is left on "never expire" unintentionally.

## Implementation pointers

- **`lib/batch-stack.ts`** — `ContainerInstanceLogGroup` retention is hardcoded to `ONE_WEEK`; make it configurable.
- **`lib/nextflow-ecr-stack.ts`** — the CodeBuild project and trigger Lambda create their own log groups; set explicit retention on them.
- **`lib/s3-stack.ts`** — review the `workDirExpirationDays` lifecycle window (and document the resumability trade-off).
- **`bin/aws_batch_squared.ts`** — surface a `logRetentionDays` context key.
- Note `/aws/batch/job` is created by AWS Batch itself (not in code) — decide whether to manage it explicitly.

## Acceptance criteria

- All stack-created log groups have an explicit, documented retention.
- Retention is configurable via context.
- S3 lifecycle behaviour documented in the README.

## Seqera Batch Forge reference

Forge ships **all** its host log groups with **7-day retention** (`SEQERA_BATCH_FORGE_FINDINGS_clean.md` §4): `tower/forge`, `tower/cloud-init`, `tower/cloud-init-output`, `tower/ecs-agent`, `tower/ebs-autoscale` — each streamed per-instance. Seven days is enough to debug a bootstrap failure on an ephemeral (Spot) host without accruing standing cost, and is a reasonable default to copy for the container-instance groups here. Job/app logs go separately to `/aws/batch/job`.

## References

- [CloudWatch Logs: log groups and retention](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)
- [Amazon S3 lifecycle management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- Code: `lib/batch-stack.ts`, `lib/s3-stack.ts`, `lib/nextflow-ecr-stack.ts`
