## Summary

Make the **Nextflow engine version** a real, pinnable configuration value. Today the version is neither wired through from context nor actually honoured by the image build, so every rebuild silently ships whatever `get.nextflow.io` returns as "latest" — and the head-node job definition always points at the `:latest` tag regardless.

**Difficulty:** medium · **Effort:** small

## Background

The head-node image is built by `lib/nextflow-ecr-stack.ts`. There is already a `nextflowVersion` prop (default `"latest"`), but three things break end-to-end version pinning:

1. **It's never wired through.** `lib/nextflow-batch-stack.ts` constructs `NextflowEcrStack` with only `{ namespace }` — `nextflowVersion` is never passed, and it isn't a key on `NextflowBatchConfig`. So there is no context knob for it at all.
2. **The build ignores it.** The CodeBuild step runs `docker build --build-arg VERSION=$NEXTFLOW_VERSION`, but the Dockerfile declares no `ARG VERSION` and installs Nextflow with `curl -s https://get.nextflow.io | bash`, which always grabs the **latest stable at build time**. The build-arg only ends up in the image *tag*, not the installed engine.
3. **The job definition always uses `:latest`.** `imageUri` is hard-coded to `…:latest`, so even a correctly-versioned image isn't the one the head node runs.

Net effect: a rebuild can silently change the Nextflow engine under a running project, and there is no way to pin it. This is the "easier to change / pin versions" gap.

The correct pin is `NXF_VER`: setting it (at build in the Dockerfile, or as an env var in the head-node container) makes both `get.nextflow.io` and the launcher use exactly that version.

## What to do

- [ ] Add a `nextflowVersion` key to `NextflowBatchConfig` (`bin/aws_batch_squared.ts`) and thread it into `NextflowEcrStack`.
- [ ] Make the image build actually honour it: set `NXF_VER=<version>` in the Dockerfile (or `ARG VERSION` consumed by the install step) so the pinned engine is baked in.
- [ ] Tag and reference the image by version, not just `:latest`: have `imageUri` resolve to the pinned tag so the job definition runs the intended engine.
- [ ] Document the key and the "reproducible vs always-current" trade-off in the README config table.

## Implementation pointers

- **`bin/aws_batch_squared.ts`** / **`lib/nextflow-batch-stack.ts`** — add `nextflowVersion` to the config interface and pass it to `new NextflowEcrStack(this, 'NextflowEcrStack', { namespace, nextflowVersion })`.
- **`lib/nextflow-ecr-stack.ts`** — in `dockerfileContent`, pin with `ENV NXF_VER=<version>` before the `get.nextflow.io` line (an unset/`latest` value should preserve today's behaviour). Make `this.imageUri` reference the version tag (fall back to `:latest` when unset).
- **`docker/nextflow-head/nextflow.aws.sh`** — optionally export `NXF_VER` at runtime as a belt-and-braces pin.
- **`README.md`** — add `nextflowVersion` to the configuration table (Reproducibility section already flags this).

## Acceptance criteria

- Setting `-c nextflowVersion=<x.y.z>` produces an image whose `nextflow -version` reports exactly that version, and the head-node job definition runs it.
- Leaving it unset preserves current behaviour (latest at build time).
- README documents the key and the trade-off.

## References

- [Nextflow `NXF_VER` / self-update](https://www.nextflow.io/docs/latest/config.html#environment-variables)
- [AWS Batch job definitions](https://docs.aws.amazon.com/batch/latest/userguide/job_definitions.html)
- Code: `lib/nextflow-ecr-stack.ts`, `lib/nextflow-batch-stack.ts`, `bin/aws_batch_squared.ts`
- Seqera reference: `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §8b — the `nf-launcher` image pins Nextflow via `NXF_VER=24.10.4`.
