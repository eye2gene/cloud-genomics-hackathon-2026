## Summary

Give the Nextflow head node its own small On-Demand compute environment/queue so the long-lived driver is isolated from workers (whenever workers also run On-Demand), from other concurrent runs, and can be sized independently. Note this is a **conditional** improvement — see the background for when it actually matters.

**Difficulty:** medium · **Effort:** medium

## Background

**By default this isn't a problem, and it's worth being clear about that.** The head-node job definition (`lib/nextflow-stack.ts`) sets `NF_JOB_QUEUE` to the **Spot** queue, so worker (child) jobs go to Spot while the head node is the only thing submitted to the On-Demand queue. In the default path the On-Demand queue carries drivers only — there is no driver-vs-worker contention.

The dedicated head environment earns its keep in the cases where that assumption breaks:

- **Workers routed to On-Demand (per run).** `NF_JOB_QUEUE` is only a *default* — the head entrypoint (`docker/nextflow-head/nextflow.aws.sh`) writes it as `process.queue`, and it's overridable at submit time. Submit with `NF_JOB_QUEUE` pointed at the On-Demand queue (e.g. a pipeline where Spot interruptions are too disruptive, or a **benchmarking** run where you want to remove Spot-reclaim noise from the runtime/cost numbers) and the whole run's workers land on On-Demand — sharing the queue with the driver.
- **Per-process queue routing.** The entrypoint sets a *global* `process.queue`, but a supplied config/profile can pin specific processes to the On-Demand queue via `withName`/`withLabel` selectors (which outrank the global default). So a single run can legitimately mix Spot and On-Demand workers.
- **Concurrent runs.** Every head node, for every pipeline, is submitted to the one On-Demand queue/CE (bounded by `onDemandMaxCpus`). Run several pipelines at once and the long-lived drivers compete for the same capacity even when all workers are on Spot.
- **Per-role sizing.** Head nodes are small (4 vCPU / 16 GB); On-Demand workers — or the NVMe work instances from the local-NVMe-scratch issue — want different/larger instance types. One shared On-Demand CE with a single instance-type list is a compromise.

In all of these, a driver stuck `RUNNABLE` behind a wave of worker jobs is far worse than a delayed worker: losing or stalling the head node stalls the **entire** pipeline, whereas workers are retriable. A small, separately-sized, dedicated On-Demand head environment guarantees the driver always has capacity and can be tuned independently.

## What to do

- [ ] Add a small dedicated On-Demand compute environment + job queue for head nodes in `lib/batch-stack.ts` (modest max vCPUs).
- [ ] Point the head-node job definition/submission at the new head queue (`lib/nextflow-stack.ts`, README submit instructions).
- [ ] Keep worker (Spot) fan-out unchanged; confirm children still land on the Spot queue.
- [ ] Update `DEBUGGING.md` / README resource-name references.

## Implementation pointers

- **`lib/batch-stack.ts`** — add a small dedicated On-Demand `CfnComputeEnvironment` + `CfnJobQueue` for the head node (e.g. `Head-<ns>`, modest `maxvCpus`), and expose its ARN. Model it on the existing `OnDemandComputeEnv` / `OnDemandQueue`.
- **`lib/nextflow-batch-stack.ts`** — publish the new head-queue ARN as an SSM `StringParameter` (like `ParamOnDemandJobQueue`) and wire it through.
- **`README.md` / `DEBUGGING.md`** — document the new queue and update the submit instructions (submit the head job to the head queue). `NF_JOB_QUEUE` (workers → Spot) is unchanged.

## Acceptance criteria

- A separate head-node queue exists; submitting the head job there works end to end.
- Worker child jobs continue to run on the Spot queue.
- Docs updated with the new queue name.

## Seqera Batch Forge reference

This is the Forge topology, not a novel design — every Forge environment ships as a **head + work pair** (`SEQERA_BATCH_FORGE_FINDINGS_clean.md` §3):

| Property | `-head` | `-work` |
|---|---|---|
| Type | EC2 (on-demand) | SPOT |
| Allocation strategy | `BEST_FIT_PROGRESSIVE` | `SPOT_PRICE_CAPACITY_OPTIMIZED` |
| Instance types | `optimal` | NVMe families (`c5d, i3, i4i, m5ad, m5d, r5ad, r5d`) |
| min / max vCPU | `0` / `5000` | `0` / `5000` |
| Launch template / SG / subnets | shared | shared |

Worth copying: both CEs **scale to zero** (`minvCpus=0`), they **share one launch template**, and Forge uses **no `spotIamFleetRole`** — modern Batch uses the service-linked Spot role automatically (this repo still wires an explicit `spotFleetRole`, which could be simplified). The head CE is deliberately small; Seqera even registers the head job def with placeholder `1 vCPU / 1024 MB` and overrides per-submit.

## References

- [AWS Batch compute environments](https://docs.aws.amazon.com/batch/latest/userguide/compute_environments.html) and [job queues](https://docs.aws.amazon.com/batch/latest/userguide/job_queues.html)
- [Nextflow on AWS Batch](https://www.nextflow.io/docs/latest/aws.html)
- Code: `lib/batch-stack.ts`, `lib/nextflow-stack.ts`
