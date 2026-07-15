## Summary

Package the whole platform as a reusable **L3 CDK construct** — a single `NextflowBatch` construct with typed props instead of raw context — so others can drop it into their own CDK app in a few lines and extend it cleanly. Optionally publish it (npm, or multi-language via JSII).

**Difficulty:** hard · **Effort:** large

## Background

Today the app is consumed as a standalone CDK application configured through `cdk.context.json` / `-c` flags. Exposing it as an L3 pattern construct (a "solution behind a small, opinionated API") would let it be embedded and composed with other infrastructure, with a typed, discoverable interface and sensible defaults.

CDK constructs come in levels: L1 (raw CloudFormation), L2 (sensible defaults), L3 (whole-solution patterns). This is an L3 packaging exercise.

## What to do

- [ ] Refactor the orchestrator into a `NextflowBatch` construct that takes a typed `props` interface (mirroring today's config) with defaults.
- [ ] Keep a thin app/bin that instantiates the construct from context, so the current usage still works.
- [ ] Add construct-level unit tests and usage docs/examples.
- [ ] (Optional) Publish to npm; consider [JSII](https://aws.github.io/jsii/) for multi-language support and listing on [Construct Hub](https://constructs.dev/).

## Implementation pointers

- **`lib/nextflow-batch-stack.ts`** — refactor the orchestrator `NextflowBatchStack` into a reusable `NextflowBatch` **construct** (extends `Construct`) that takes a typed `props` interface mirroring `NextflowBatchConfig`, with sensible defaults. Keep a thin `Stack` subclass wrapping it so today's deployment path is unchanged.
- **`bin/aws_batch_squared.ts`** — instantiate the construct via the wrapper, still reading context.
- The nested stacks (`lib/*-stack.ts`) become children of the construct; check whether any should become plain `Construct`s rather than `NestedStack`s for cleaner embedding.
- **`package.json`** (+ optional JSII config) — for publishing to npm / Construct Hub.

## Acceptance criteria

- A single `NextflowBatch` construct encapsulates the platform behind typed props.
- The existing context-driven app still deploys via the thin wrapper.
- Usage example documented.

## References

- [AWS CDK constructs & levels (L1/L2/L3)](https://docs.aws.amazon.com/cdk/v2/guide/constructs.html)
- [JSII (multi-language libraries)](https://aws.github.io/jsii/)
- [Construct Hub](https://constructs.dev/)
- Code: `lib/nextflow-batch-stack.ts`, `bin/aws_batch_squared.ts`
