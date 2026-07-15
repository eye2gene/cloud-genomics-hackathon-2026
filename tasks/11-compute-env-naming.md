## Summary

Reconcile the `-vN` compute-environment naming. Either document *why* a rename is sometimes required, or adopt a cleaner strategy (e.g. pin an explicit launch-template version) so launch-template fixes propagate without a forced replacement.

**Difficulty:** medium · **Effort:** small

## Background

The compute environments in `lib/batch-stack.ts` are named `ondemand-<ns>-vN` / `spot-<ns>-vN`, and the suffix is bumped to force replacement. This is because **AWS Batch caches the launch-template `$Latest` version per compute environment**: after you fix the launch template, existing CEs keep launching the old version until they're replaced (documented in `DEBUGGING.md`). The `-vN` bump forces CloudFormation to create a fresh CE that picks up the fix.

A cleaner approach is to reference an explicit launch-template version in the CE so updates are detected as a diff and propagate, removing (or reducing) the need for manual suffix bumps.

## What to do

- [ ] Evaluate pinning an explicit LT version (instead of `$Latest`) in the compute-resources config so a template change forces a CE update.
- [ ] Either adopt that approach, or clearly document the `-vN` bump procedure (when and why) for operators.
- [ ] Ensure whatever is chosen is reflected in `DEBUGGING.md`.

## Implementation pointers

- **`lib/batch-stack.ts`** — `SpotComputeEnv` / `OnDemandComputeEnv` set `launchTemplate.version: "$Latest"` and carry the `-v4` name suffix. Consider passing an **explicit** LT version (from `LaunchTemplateStack.latestVersionNumber`) so a template change diffs and forces a CE update, reducing the need for manual `-vN` bumps.
- **`lib/launch-template-stack.ts`** — already emits `latestVersionNumber` as an output; surface it to the batch stack if you pin the version.

## Acceptance criteria

- Launch-template changes reliably reach compute environments (documented mechanism).
- Naming/replacement strategy is documented or improved.

## References

- [AWS Batch launch template support](https://docs.aws.amazon.com/batch/latest/userguide/launch-templates.html)
- [Updating AWS Batch compute environments](https://docs.aws.amazon.com/batch/latest/userguide/updating-compute-environments.html)
- Project docs: `DEBUGGING.md` → "Batch caches the launch-template `$Latest` version"; Code: `lib/batch-stack.ts`
