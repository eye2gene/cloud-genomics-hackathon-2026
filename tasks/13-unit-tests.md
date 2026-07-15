## Summary

Replace the placeholder test with real CDK unit tests using the assertions module: `Template.fromStack(...)` checks per nested stack, plus coverage of the `bin/` validation branches. These need no AWS account and run in milliseconds via `bun test`.

**Difficulty:** medium · **Effort:** medium

## Background

`test/aws_batch_squared.test.ts` is currently a passing placeholder — there's no real coverage. The CDK [assertions module](https://docs.aws.amazon.com/cdk/v2/guide/testing.html) lets us synthesize a stack in-memory and assert on the resulting template, which is fast and free.

The project runs tests with **Bun** (`bun test`); the assertions module works fine under the Bun runtime.

## What to do

- [ ] Add `Template.fromStack(...)` assertions per nested stack: two Batch job queues, Spot + On-Demand compute environments, IAM policy scoping, the head-node job-definition env vars (`NF_JOB_QUEUE`/`NF_WORKDIR`/`NF_LOGSDIR`), S3 bucket removal policy + lifecycle.
- [ ] Cover the validation branches that exist in `bin/aws_batch_squared.ts` — missing `vpcId`/`subnetIds` when `createVpc=false`, and missing `existingNextflowImage` when `buildNextflowImage=false`. (Note: the `existingBucket`→`s3BucketName` check is **not** in `bin`; it's thrown inside `S3Stack` at synth. Either test it at the stack level, or lift that validation into `bin` alongside the others so all input validation lives in one place.)
- [ ] Ensure `bun test` runs them green.

## Implementation pointers

- **`test/aws_batch_squared.test.ts`** — use `Template.fromStack(...)` from `aws-cdk-lib/assertions`. Because the resources live in **nested** stacks, either synth the app and load each nested-stack template, or instantiate the nested stacks (`BatchStack`, `NextflowStack`, `IamStack`, …) directly to assert on queues, CEs, IAM scoping, and the head-node job-def env vars.
- Cover the validation branches in **`bin/aws_batch_squared.ts`** (missing `vpcId`/`subnetIds`, `s3BucketName`, `existingNextflowImage`) — this may require exporting the config-building/validation logic so it's unit-testable.
- Runs via `bun test` (already configured).

## Acceptance criteria

- Meaningful template assertions exist for each nested stack.
- `bin/` validation error paths are covered.
- `bun test` passes locally (and in CI once that lands).

## References

- [Testing constructs (CDK assertions)](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)
- [`aws-cdk-lib/assertions` API](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.assertions-readme.html)
- [Bun test runner](https://bun.com/docs/cli/test)
- Code: `test/aws_batch_squared.test.ts`, `bin/aws_batch_squared.ts`, `lib/*.ts`
