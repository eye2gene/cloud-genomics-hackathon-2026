## Summary

Configure the ECS agent to pull each container image **once per instance** (`ECS_IMAGE_PULL_BEHAVIOR=once`) instead of once per task. When a Nextflow run fans out into hundreds of tasks that reuse the same image, this removes a large amount of redundant image-pull time and network traffic.

**Difficulty:** easy · **Effort:** small

## Background

Worker instances run many child jobs, most sharing the same container image. By default the ECS agent may re-pull images; setting `ECS_IMAGE_PULL_BEHAVIOR=once` caches the image on the host after the first pull.

The setting lives in `/etc/ecs/ecs.config` and is applied by the launch-template cloud-init in `lib/launch-template-stack.ts`.

> [!IMPORTANT]
> Set `ecs.config` values from cloud-init **`bootcmd`** (which runs *before* the ECS agent starts), **not** by restarting the agent in `runcmd`. As documented in `DEBUGGING.md`, restarting `ecs` inside `runcmd` deadlocks cloud-init (`ecs.service` is ordered `After=cloud-final.service`) and prevents the node from ever joining the cluster.

## What to do

- [ ] In `lib/launch-template-stack.ts`, write `ECS_IMAGE_PULL_BEHAVIOR=once` into `/etc/ecs/ecs.config` via a cloud-init `bootcmd` (or `write_files` before the agent starts).
- [ ] While editing `ecs.config`, also add `ECS_ENABLE_AWSLOGS_EXECUTIONROLE_OVERRIDE=true` — Seqera Batch Forge sets this in the same file so each job can send `awslogs` via its execution role (see `SEQERA_BATCH_FORGE_FINDINGS_clean.md` §4).
- [ ] Redeploy and confirm nodes still register with ECS (`scripts/nf-debug.sh status`).
- [ ] Verify the behaviour with a multi-task run: the image is pulled once per host, not per task.

## Implementation pointers

- **`lib/launch-template-stack.ts`** — the multipart cloud-init built in `userData.addCommands(...)`. Add a `bootcmd:` section that writes `ECS_IMAGE_PULL_BEHAVIOR=once` into `/etc/ecs/ecs.config` **before** the ECS agent starts. There is currently only `#cloud-config` (`write_files`) + a `runcmd` block — do **not** add an agent restart to `runcmd`.
- Both compute environments in **`lib/batch-stack.ts`** (`SpotComputeEnv`, `OnDemandComputeEnv`) share this single launch template, so the change applies to head and worker nodes automatically.

## Acceptance criteria

- New worker instances have `ECS_IMAGE_PULL_BEHAVIOR=once` in `/etc/ecs/ecs.config`.
- Compute environments remain `VALID` and nodes register with ECS.
- Second and subsequent tasks on the same host skip the image pull.

## References

- [ECS container agent configuration](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-config.html) (see `ECS_IMAGE_PULL_BEHAVIOR`)
- [cloud-init modules: `bootcmd` vs `runcmd`](https://cloudinit.readthedocs.io/en/latest/reference/modules.html)
- Project docs: `DEBUGGING.md` → "Instances launch, run cloud-init, then never join ECS"
