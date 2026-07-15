## Summary

Update the toolchain and runtimes: bump `aws-cdk-lib` / `aws-cdk` CLI / `@types/node` / TypeScript, and move off the **deprecated Lambda `python3.9` runtime**. Keeping these current picks up security fixes, new L2 defaults, and avoids running on end-of-life runtimes.

**Difficulty:** easy · **Effort:** small

## Background

Current pins (`package.json`):
- `aws-cdk-lib` **2.208.0**, `aws-cdk` (CLI) **2.1024.0** — both trail the latest 2.x; the CDK ships frequently with security and construct fixes.
- `@types/node` **22.7.9**, `typescript` **~5.6.3** — fine, but worth keeping in step with the Node runtime the project targets (Bun + `tsconfig` target `ES2022`).
- `constructs` **^10.0.0** — keep compatible with the chosen `aws-cdk-lib`.

Runtime pins in code:
- **`lib/nextflow-ecr-stack.ts` uses `lambda.Runtime.PYTHON_3_9`** for the image-build trigger Lambda. **Python 3.9 on Lambda is deprecated** — new function creation gets restricted and it stops receiving security patches. Bump to a supported runtime (3.12/3.13).
- CodeBuild `LinuxBuildImage.STANDARD_7_0` and `amazoncorretto:17` (head image) are current enough; note them but no action needed unless bumping deliberately.
- The compute AMI is the **ECS-optimized Amazon Linux 2** (`imageType: "ECS_AL2"`). AL2 is heading toward end of support; migrating to **ECS AL2023** (`ECS_AL2023`) is a larger, separate task (bootstrap differences) — call it out here but track it with the launch-template work (`10-externalize-userdata.md`).

## What to do

- [ ] Bump `aws-cdk-lib` and the `aws-cdk` CLI to a recent matching 2.x; run `bunx aws-cdk synth` + `bun test` to confirm no breaking diffs.
- [ ] Change the trigger Lambda runtime from `PYTHON_3_9` to a supported version (3.12 or 3.13) and confirm the inline handler still works (it uses only `boto3` + `json`).
- [ ] Refresh `@types/node` / `typescript` as needed to match the runtime; keep `constructs` compatible with the new `aws-cdk-lib`.
- [ ] Review `cdk diff` after the bump — new library versions can change synthesized defaults.
- [ ] (Note, not in scope here) Track the ECS AL2 → AL2023 migration separately.

## Implementation pointers

- **`package.json`** — bump `aws-cdk-lib`, `aws-cdk`, and dev types; `bun install` to refresh `bun.lock`.
- **`lib/nextflow-ecr-stack.ts`** — `runtime: lambda.Runtime.PYTHON_3_12` (or `_3_13`).
- Do this **before or alongside `14-ci-github-actions.md`** so CI (synth + test, and `cdk-nag`) guards the upgrade and future bumps.
- Pairs well with a lockstep-updates policy (e.g. Dependabot/Renovate) — optional follow-up.

## Acceptance criteria

- `aws-cdk-lib` / CLI updated; `synth`, `diff`, and `bun test` all pass with no unexpected resource changes.
- No deprecated Lambda runtime remains (`PYTHON_3_9` gone).
- Any intentional synthesized-default changes from the bump are reviewed and noted.

## References

- [AWS Lambda runtime deprecation policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html#runtime-support-policy)
- [aws-cdk-lib releases](https://github.com/aws/aws-cdk/releases)
- [Amazon ECS-optimized AMIs (AL2 / AL2023)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html)
- Code: `package.json`, `lib/nextflow-ecr-stack.ts`
