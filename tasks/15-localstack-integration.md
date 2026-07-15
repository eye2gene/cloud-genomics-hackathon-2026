## Summary

Add integration smoke tests that deploy the stack against a **free, self-hosted AWS emulator** so wiring problems are caught on a laptop and in CI without a real AWS account or a paid emulator licence. Default to [MiniStack](https://ministack.org/) — an MIT-licensed, drop-in local AWS emulator (single Docker container, port `4566`, no account / key / telemetry).

**Difficulty:** hard · **Effort:** large

## Background

Unit tests (assertions) validate the synthesized template but not that resources actually deploy and connect. Running `cdk deploy` against a local emulator exercises the real deploy path — bootstrapping, nested stacks, SSM parameter resolution, IAM — cheaply and repeatably.

For a hackathon we want a **fully free** option — participants shouldn't need a paid licence or account:

- **MiniStack** is MIT-licensed and free, and is designed as a drop-in LocalStack replacement (same `localhost:4566` endpoint), so `cdklocal` / endpoint-override setups largely carry over.
- LocalStack has a free Community edition but keeps a number of services/features behind its paid Pro tier, so "free" is qualified there.

> The local-emulator space moved quickly in 2026 (MiniStack, Floci, LocalEmu and others appeared as free LocalStack alternatives). Keep the choice loosely coupled — anything exposing the AWS APIs on `:4566` should work — but default to MiniStack because it's free and MIT-licensed.

Caveat (applies to **every** emulator): coverage of Batch / ECS / EC2 / CodeBuild is uneven, so scope the smoke test to what emulates reliably (VPC, S3, IAM, SSM, and CloudFormation/stack composition) rather than a full pipeline run.

## What to do

- [ ] Run MiniStack locally (its Docker container) and point the AWS SDK/CLI at `http://localhost:4566`.
- [ ] Use `cdklocal` (or CDK endpoint/context overrides) to `bootstrap` + `deploy` the app against it.
- [ ] Scope the smoke test to reliably-emulated services; assert the stack deploys and key resources/params exist.
- [ ] Wire it into CI as a separate (optional / nightly) job so it doesn't slow every PR.
- [ ] Document how to run it locally.

## Implementation pointers

- Mostly new tooling, not core-stack changes: add a MiniStack service (docker-compose or `docker run ministackorg/ministack`) and use **`aws-cdk-local` / `cdklocal`** (or endpoint overrides) to `bootstrap`/`deploy`.
- Add a helper under **`scripts/`** (alongside `scripts/nf-debug.sh`) and a separate CI job (see the CI issue) — keep it off the per-PR critical path if it's slow.
- Keep the emulator endpoint configurable (an env var) so MiniStack can be swapped for another `:4566`-compatible emulator without code changes.
- Scope assertions to reliably-emulated services (VPC / S3 / IAM / SSM + stack composition); Batch/ECS/CodeBuild emulation is limited, so don't expect a full pipeline run.

## Acceptance criteria

- `cdklocal deploy` (or equivalent) completes against MiniStack for the supported subset — no paid licence or AWS account required.
- A documented command runs the smoke test locally.
- CI can run it (at least on demand / nightly).

## References

- [MiniStack](https://ministack.org/) · [MiniStack on GitHub](https://github.com/ministackorg/ministack) · [MiniStack on Docker Hub](https://hub.docker.com/r/ministackorg/ministack)
- [Testing AWS CDK infrastructure locally with MiniStack](https://medium.com/@umandajayo/test-your-aws-cdk-infrastructure-locally-without-a-real-aws-account-9b7a319e8ba8)
- [`aws-cdk-local` (`cdklocal`)](https://github.com/localstack/aws-cdk-local)
