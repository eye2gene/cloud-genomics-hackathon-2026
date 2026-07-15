# Suggested improvements

A prioritized, developer-facing backlog for the CDK app — the concrete, file-referenced checklist.
The narrative rationale for the bigger items lives in the README's
[Potential improvements](./README.md#potential-improvements) section; this file tracks status and
points at the exact code to change.

## High priority — correctness / functionality

- [ ] **Add real test coverage.** `tests/unit/test_stacks.py` is a placeholder.
  Add `Template.from_stack(...)` assertions per nested stack (queues, compute envs, IAM policy scoping,
  job-definition env vars) and cover the `config.py` validation branches (missing
  `vpcId`/`s3BucketName`/`existingNextflowImage`). No AWS account needed; runs in milliseconds.
- [ ] **Keep account-specific values out of code.** Ensure nothing account-specific is baked into
  source (README/config examples included) — all of it belongs in context.
- [ ] **Pin or confirm the SSM dynamic-reference versions.** `nextflow_stack.py` resolves
  `{{resolve:ssm:<param>:1}}` (version `1`). Confirm that's intended, or resolve latest.

## Performance — storage and the data path

- [ ] **Benchmark storage strategies against the same workload**, capturing runtime **and** cost:
  AWS CLI staging (current), tuned `gp3`/`io2` EBS scratch, **local NVMe instance-store**, FUSE-over-S3,
  EFS, and FSx for Lustre. The scratch/shared-storage layer is usually the biggest lever on both
  runtime and cost. (See the comparison table in the README.)
- [ ] **Local NVMe instance-store scratch** for I/O-heavy steps. Use NVMe instance families (the
  `d`-suffix types — `c5d`, `m5d`, `m5ad`, `r5d`, `r5ad`, `i3`, `i4i`), and in the launch-template
  cloud-init LVM-stripe all NVMe disks into one volume (`pvcreate` → `vgcreate` → `lvcreate -l 100%FREE`),
  mount it as scratch, and point the work container's temp dir at it. Requires the **work** compute
  environment to use NVMe instance types (not `optimal`).
- [ ] **Cache container images per host** — `ECS_IMAGE_PULL_BEHAVIOR=once`, so a large image is pulled
  once per instance instead of once per task. ⚠️ Set it via cloud-init **`bootcmd`** (before the ECS
  agent starts); **never** by restarting the agent in `runcmd` (see the caveat at the top).
- [ ] **Tune kernel write-back** (`vm.dirty_bytes` / `vm.dirty_background_bytes`) on worker instances
  so large sequential writes streaming to S3 don't balloon host memory.

## Right-sizing and cost

- [ ] **Right-size / parameterize the head node.** `nextflow_stack.py` hardcodes `vcpus=4`,
  `memory=16384`, and a `3600s` timeout. Surface these as context and tune per pipeline — a smaller
  head node is cheaper (it runs On-Demand for the whole run), but large DAGs need more memory and a
  longer timeout.
- [ ] **A dedicated head compute environment.** The head node currently shares the On-Demand queue
  with any On-Demand workers; a small separate On-Demand environment just for head nodes isolates the
  long-lived driver from bursty worker demand.
- [ ] **Cost-allocation tags.** Tag every resource (`project`, `team`, `pipeline`, `run-id`) via
  `Tags.of(scope).add(...)` at the app level so spend can be attributed once activated as
  cost-allocation tags.
- [ ] **Periodic review of log retention and S3 lifecycle** windows to keep standing costs predictable.

## Robustness / maintainability

- [ ] **Externalize the launch-template user-data.** `aws_batch_squared_py/launch_template_stack.py` builds a large
  multipart cloud-init as an array of string literals — hard to read and easy to break (this
  session's outage came from an unsafe edit to it). Move it to a template asset file, or make the
  bootstrap resilient (fast-failing, non-blocking optional steps) so a slow/failed step can't stop
  the instance joining ECS.
- [ ] **Tighten IAM.** Several policies use `Resource: "*"` with broad actions (`s3:*` on the bucket,
  `batch:*Job`). Scope to the minimum required and review the `AmazonS3ReadOnlyAccess` attachments.
  A clean split is InstanceRole (scoped S3 + Batch submit), ExecutionRole (image pull + secrets),
  ServiceRole (`AWSBatchServiceRole`).
- [ ] **Add `cdk-nag` (or cfn-guard) to the workflow.** Wire compliance/security checks into
  `synth`/CI (the AWS IaC tooling is already available).
- [ ] **Reconcile the `-vN` compute-env naming.** Names now carry a `-v4` suffix from forced
  replacements. Document *why* a rename is sometimes required (Batch caches the launch-template
  `$Latest` version per CE), or adopt a cleaner replacement strategy (e.g. pin an explicit LT version).
- [ ] **Make region configurable end-to-end.** Thread region consistently from `env`/context; the
  head-node config currently defaults to a single region.

## Extensibility

- [ ] **Package this as a reusable L3 CDK construct** — expose the whole platform as a single
  `NextflowBatch` construct with typed props instead of raw context, so others can drop it into their
  own CDK app in a few lines. Consider publishing (npm, or multi-language via JSII).

## Testing and CI

- [ ] **Unit tests** with the CDK assertions module (see above).
- [ ] **Local integration tests** against an AWS emulator (e.g. LocalStack) so a `synth`/`deploy`
  smoke test runs on a laptop and in CI without spending on real infrastructure.
- [ ] **Wire up CI** — build + `synth` + tests on pull requests.

## Docs / housekeeping

- [ ] **Add example configs / a smoke-test workflow** committed to the repo (e.g. a small `nf-core`
  test-profile invocation) so a deployed stack can be validated end-to-end in one command.
- [ ] **Expand the operational docs.** `DEBUGGING.md` covers triage and log locations; consider adding
  usage, configuration, and permissions references to round out the guide set.
