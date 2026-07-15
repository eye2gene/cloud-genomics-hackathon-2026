## Summary

Make pipeline-revision pinning (`-r <release>`) the documented default in the submit instructions and examples, so runs are reproducible. Today the quick-start submits `nf-core/sarek` with no `-r`, which pulls whatever is on the pipeline's default branch at run time.

**Difficulty:** easy · **Effort:** small

## Background

Reproducibility has two halves: the **engine** version (see `17-pin-nextflow-version.md`) and the **pipeline** version. The head-node entrypoint (`docker/nextflow-head/nextflow.aws.sh`) runs `nextflow run $NEXTFLOW_PROJECT $NEXTFLOW_PARAMS` verbatim, so revision pinning is a submit-time concern — but the README's quick-start example omits `-r`, which teaches the non-reproducible path. Nextflow will then resolve the default branch's current HEAD, so two runs "of the same pipeline" weeks apart can execute different code.

This is mostly a docs + examples change (plus an optional guard-rail), not a code change to the stack.

## What to do

- [ ] Update the README submit examples to always pin a release, e.g. `... nf-core/sarek -r 3.9.0 ...`, and add a one-line note on *why*.
- [ ] Note the convention in `DEBUGGING.md` / benchmarking docs so benchmark runs pin a revision (otherwise runtime/cost numbers aren't comparable across days).
- [ ] (Optional) Add a soft guard: if the project is a git/nf-core pipeline and no `-r` was supplied, log a clear warning from the entrypoint.

## Implementation pointers

- **`README.md`** — the "Submitting a workflow" and "Benchmarking" sections; add `-r <release>` to every `nextflow run` / `submit-job` example and a short reproducibility note.
- **`docker/nextflow-head/nextflow.aws.sh`** — optional: detect a remote pipeline name with no `-r` in `$NEXTFLOW_PARAMS` and emit a warning (do not hard-fail; local/S3 projects legitimately have no revision).
- Pair with the deployment-profiles issue: a `production` profile should encourage/require pinned revisions.

## Acceptance criteria

- All README/submit examples pin a pipeline revision.
- The reproducibility rationale is documented.
- (If implemented) an un-pinned remote pipeline logs a visible warning.

## References

- [Nextflow pipeline revisions (`-r`)](https://www.nextflow.io/docs/latest/sharing.html#handling-revisions)
- [nf-core pipeline releases](https://nf-co.re/pipelines)
- Docs/code: `README.md`, `docker/nextflow-head/nextflow.aws.sh`
- Related: `17-pin-nextflow-version.md` (the engine half of reproducibility)
