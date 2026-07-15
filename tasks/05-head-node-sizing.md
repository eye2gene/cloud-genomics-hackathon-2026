## Summary

Make the head-node job resources (vCPU, memory, timeout) configurable via CDK context and right-size them, instead of the current hardcoded values.

**Difficulty:** easy · **Effort:** small

## Background

`lib/nextflow-stack.ts` hardcodes the head-node job definition at `vcpus: 4`, `memory: 16384`, and `attemptDurationSeconds: 3600`. The head node runs the Nextflow driver (not the heavy compute), and it runs On-Demand for the whole pipeline — so a smaller head node is cheaper. But very large DAGs need more memory and a longer timeout. These should be tunable per pipeline.

## What to do

- [ ] Add context keys (e.g. `headVcpus`, `headMemory`, `headTimeoutSeconds`) to `NextflowBatchConfig` in `bin/aws_batch_squared.ts` with sensible defaults.
- [ ] Thread them into the head-node `CfnJobDefinition` in `lib/nextflow-stack.ts`.
- [ ] Document the new keys in the README configuration table.

## Implementation pointers

- **`bin/aws_batch_squared.ts`** — add `headVcpus` / `headMemory` / `headTimeoutSeconds` to `NextflowBatchConfig` (defaults 4 / 16384 / 3600) and read them from context.
- **`lib/nextflow-batch-stack.ts`** — pass the new values through to `NextflowStack` props.
- **`lib/nextflow-stack.ts`** — replace the hardcoded `containerProperties.vcpus` (4), `containerProperties.memory` (16384) and `timeout.attemptDurationSeconds` (3600) on `BatchNextflowJobDefinition` with the props.
- **`README.md`** — add the new keys to the configuration table.

## Acceptance criteria

- Head-node vCPU / memory / timeout can be set via context (`-c ...`) without code edits.
- Defaults preserve current behaviour.
- README configuration table updated.

## References

- [AWS Batch job definitions](https://docs.aws.amazon.com/batch/latest/userguide/job_definitions.html)
- [Nextflow on AWS Batch](https://www.nextflow.io/docs/latest/aws.html)
- Code: `lib/nextflow-stack.ts`, `bin/aws_batch_squared.ts`
