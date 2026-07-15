## Summary

Tag every resource the stack creates (e.g. `project`, `team`, `pipeline`, `run-id`) so spend can be attributed per team/run in Cost Explorer once the tags are activated as cost-allocation tags. This directly feeds the benchmarking cost numbers.

**Difficulty:** easy · **Effort:** small

## Background

There's currently no consistent tagging strategy, which makes per-run / per-team cost attribution hard. CDK makes stack-wide tagging trivial with `Tags.of(scope).add(...)` at the app or stack level, and tags then need to be **activated** as cost-allocation tags in the billing console before they show up in Cost Explorer.

## What to do

- [ ] Apply baseline tags at the app/stack level (`Tags.of(app).add("project", ...)`, etc.) in `bin/aws_batch_squared.ts` / the orchestrator stack.
- [ ] Allow tag values (at least `project`/`team`) to be supplied via context.
- [ ] Document that the tags must be activated as cost-allocation tags in the billing console.
- [ ] (Optional) Propagate a `run-id` tag onto submitted jobs for per-run attribution.

## Implementation pointers

- **`bin/aws_batch_squared.ts`** — apply `cdk.Tags.of(app).add(key, value)` at the app level (and/or on `NextflowBatchStack`). Add context keys for the `project` / `team` values.
- Per-run attribution (`run-id`) is a submit-time concern — pass it via `aws batch submit-job` tags/env and document it, rather than in CDK.
- **`README.md`** — document the tag keys and the "activate as cost-allocation tags in the billing console" step.

## Acceptance criteria

- Deployed resources carry the baseline tags.
- README documents the tag keys and the activation step.

## References

- [Tagging in the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/tagging.html)
- [Using cost-allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
- [AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
