## Summary

Add a GitHub Actions CI workflow that installs dependencies, synthesizes the stack, and runs the tests on every pull request — and add a `cdk-nag` security/compliance check to the synth step.

**Difficulty:** medium · **Effort:** medium

## Background

There's currently no CI, so infrastructure changes aren't automatically validated. A minimal pipeline (`bun install` → `bunx aws-cdk synth` → `bun test`) catches breakage early without deploying. Adding [`cdk-nag`](https://github.com/cdklabs/cdk-nag) as an Aspect surfaces common security/compliance issues (over-broad IAM, unencrypted resources, etc.) at synth time — complementing the "tighten IAM" work.

The project uses Bun, so use the [`oven-sh/setup-bun`](https://github.com/oven-sh/setup-bun) action.

## What to do

- [ ] Add `.github/workflows/ci.yml` triggered on pull requests: checkout → setup-bun → `bun install` → `bunx aws-cdk synth` → `bun test`.
- [ ] Add `cdk-nag` (e.g. `AwsSolutionsChecks`) as an Aspect, gated so CI reports findings (start as warnings, tighten over time).
- [ ] Make the build fail on synth/test errors.

## Implementation pointers

- New **`.github/workflows/ci.yml`** — `oven-sh/setup-bun` → `bun install` → `bunx aws-cdk synth` → `bun test`, triggered on `pull_request`.
- **`bin/aws_batch_squared.ts`** — add `cdk-nag` via `Aspects.of(app).add(new AwsSolutionsChecks())` (start with warnings/annotations, tighten over time).
- **`package.json`** — add `cdk-nag` as a dev dependency (`bun add -d cdk-nag`).

## Acceptance criteria

- PRs run install + synth + test automatically.
- `cdk-nag` findings are reported in the workflow.
- A red build blocks obviously broken changes.

## References

- [GitHub Actions documentation](https://docs.github.com/actions)
- [`oven-sh/setup-bun`](https://github.com/oven-sh/setup-bun)
- [`cdk-nag`](https://github.com/cdklabs/cdk-nag)
