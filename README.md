# AWS Batch Squared — Nextflow on AWS Batch

> [!CAUTION]
> **NO WARRANTY · NOT PRODUCTION-READY · NOT SECURITY-REVIEWED**
>
> This project is provided **AS IS, with NO WARRANTY OF ANY KIND**, for **educational and
> experimental use** (hackathons, prototyping, benchmarking). It has **not** undergone any security
> review, hardening, or audit. It provisions **real AWS resources that cost money** and, if
> misconfigured, could expose data or run up charges.
>
> - Do **not** use it in production, or with sensitive / identifiable data, without your own
>   thorough security review and testing.
> - Run it only in a **sandbox / throwaway AWS account** that you control.
> - **You** are responsible for all AWS costs and for reviewing the IAM permissions and network
>   configuration before you deploy.
>
> Released under the **[MIT License](#license)** — see the [`LICENSE`](./LICENSE) file. There is no
> guarantee it works in production.

A one-command way to stand up a **genomics workflow platform on AWS**: [Nextflow](https://www.nextflow.io/)
running on [AWS Batch](https://docs.aws.amazon.com/batch/latest/userguide/what-is-batch.html).

You submit a Nextflow pipeline to a single "head node" job. That head node then launches one
child job per pipeline process, fanning work out across auto-scaling **Spot** and **On-Demand**
compute that scales back down to zero when idle. [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
holds the work directory, reference data, and results.

The whole thing is defined as code with the [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
in TypeScript, so one `cdk deploy` builds every AWS resource for you — no clicking around the console.

> **Hackathon note.** This README assumes you know Nextflow but are **new to AWS and the CDK**.
> Every AWS concept is explained inline with a link to read more. If you just want to get running,
> jump to [Quick start](#quick-start). If you want to understand what you're deploying first, read
> [AWS and CDK in five minutes](#aws-and-cdk-in-five-minutes).

---

## Contents

- [What you get](#what-you-get)
- [AWS and CDK in five minutes](#aws-and-cdk-in-five-minutes)
- [How it works ("Batch squared")](#how-it-works-batch-squared)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Submitting a workflow](#submitting-a-workflow)
- [Benchmarking](#benchmarking)
- [Monitoring and troubleshooting](#monitoring-and-troubleshooting)
- [Cost awareness and cleanup](#cost-awareness-and-cleanup)
- [Configuration reference](#configuration-reference)
- [Command reference](#command-reference)
- [Project layout](#project-layout)
- [Potential improvements](#potential-improvements)
- [License](#license)

---

## What you get

After one deploy, your AWS account contains everything needed to run reproducible Nextflow
pipelines at scale:

- A private network to run compute in.
- An S3 bucket for reference data, the Nextflow work directory, and results.
- An auto-scaling pool of compute: cheap interruptible **Spot** instances for the many small
  pipeline tasks, and reliable **On-Demand** instances for the long-lived head node.
- A pre-built Nextflow "head node" container that knows how to dispatch each pipeline process as
  its own AWS Batch job.
- All the permissions (IAM roles) wired up so those pieces can talk to each other, scoped to
  your bucket and your queues.

You interact with it exactly as you'd expect from Nextflow: submit a pipeline, watch processes
get scheduled, collect results from S3.

---

## AWS and CDK in five minutes

If you've never used AWS, here are the only services this project touches. You don't need to
configure any of them by hand — the CDK does that — but knowing what they are makes the rest of
this README (and any troubleshooting) far easier.

| Service                                                                                                                      | What it is                                                                                                                 | Why it's here                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------| ----------------------------------------------------------------------------------------------------------------------------| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [**AWS Batch**](https://docs.aws.amazon.com/batch/latest/userguide/what-is-batch.html)                                       | A managed job scheduler. You hand it a container + resource request; it finds/launches a machine, runs it, and shuts down. | Runs the Nextflow head node **and** every pipeline task.                                                                                                                                                                                 |
| [**Amazon EC2**](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html)                                          | Virtual machines ("instances").                                                                                            | Batch runs your containers on EC2 instances under the hood.                                                                                                                                                                              |
| [**EC2 Spot**](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html)                                | Spare EC2 capacity at up to ~90% off, but AWS can reclaim it with two minutes' notice.                                     | Worker tasks run on Spot to cut cost; Nextflow retries any task that gets interrupted.                                                                                                                                                   |
| [**Amazon ECS**](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)                                   | A container runtime that Batch uses internally to place containers on instances.                                           | You rarely touch it directly, but logs and clusters show up named after it.                                                                                                                                                              |
| [**Amazon S3**](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)                                          | Object storage (buckets of files, addressed by `s3://` URIs).                                                              | Reference data, the Nextflow work dir, session cache, and results all live here.                                                                                                                                                         |
| [**Amazon VPC**](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)                                   | A private virtual network for your resources.                                                                              | Compute instances run inside it. Includes a [NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) so private instances can reach the internet (to pull images and data) without being publicly reachable. |
| [**IAM**](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)                                                | Identity and permissions. "Roles" grant a resource permission to call other AWS APIs.                                      | Lets the head node submit Batch jobs and read/write your S3 bucket — and nothing else.                                                                                                                                                   |
| [**Amazon ECR**](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)                                    | A private Docker image registry.                                                                                           | Stores the Nextflow head-node container image this project builds.                                                                                                                                                                       |
| [**AWS CodeBuild**](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html)                                     | Managed build service.                                                                                                     | Builds the head-node image during deploy (so you don't need Docker locally).                                                                                                                                                             |
| [**SSM Parameter Store**](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) | A simple key/value config store.                                                                                           | The stack publishes the bucket name and queue ARNs here so other pieces can look them up at deploy time.                                                                                                                                 |
| [**CloudWatch Logs**](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)                    | Centralised logs.                                                                                                          | Where head-node and task logs land for debugging.                                                                                                                                                                                        |
| [**Mountpoint for Amazon S3**](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint.html)                        | A tool that mounts an S3 prefix as a local folder.                                                                         | Exposes shared reference data to every instance at `/mnt/s3-reference`.                                                                                                                                                                  |

### CloudFormation and the CDK

- [**AWS CloudFormation**](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)
  is AWS's infrastructure-as-code engine. You give it a JSON/YAML *template* describing the
  resources you want; it creates, updates, or deletes them to match — as one atomic unit called a
  **stack**. If something fails mid-deploy, it rolls back.
- The [**AWS CDK**](https://docs.aws.amazon.com/cdk/v2/guide/home.html) lets you write that
  infrastructure in a real programming language (here, TypeScript) instead of hand-writing
  templates. `cdk synth` compiles your code into a CloudFormation template; `cdk deploy` hands it
  to CloudFormation.

The commands you'll use, and what they do:

| Command         | Plain-English meaning                                                                                            | Docs                                                                         |
| -----------------| ------------------------------------------------------------------------------------------------------------------| ------------------------------------------------------------------------------|
| `cdk bootstrap` | One-time setup per account/region: creates a small support stack (an S3 bucket + roles) the CDK needs to deploy. | [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) |
| `cdk synth`     | Compile the TypeScript into a CloudFormation template. Great for a dry run.                                      | [Apps & synth](https://docs.aws.amazon.com/cdk/v2/guide/apps.html)           |
| `cdk diff`      | Show what would change vs. what's already deployed.                                                              | [`cdk diff`](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)              |
| `cdk deploy`    | Create/update the real AWS resources.                                                                            | [Deploy](https://docs.aws.amazon.com/cdk/v2/guide/deploy.html)               |
| `cdk destroy`   | Tear the stack down.                                                                                             | [`cdk destroy`](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)           |

> **You do not edit code to configure a deployment.** Behaviour is driven by
> [**CDK context**](https://docs.aws.amazon.com/cdk/v2/guide/context.html) — key/value settings in
> `cdk.context.json` or passed on the command line with `-c key=value`. See the
> [Configuration reference](#configuration-reference).

---

## How it works ("Batch squared")

The name comes from the core trick: **the head node is itself an AWS Batch job, and it submits
more AWS Batch jobs.**

1. You submit **one** job — the Nextflow head node — to the **On-Demand** queue.
2. That container runs `nextflow run <your pipeline>`. Its entrypoint writes a `nextflow.config`
   that selects the AWS Batch executor and points the work directory at S3.
3. As Nextflow evaluates the pipeline, it submits **one child Batch job per process** to the
   **Spot** queue (fast, cheap, interruptible).
4. Batch scales EC2 capacity up to run those tasks and back down to zero when the queue drains.
5. All intermediate and final data flows through S3, so the run is durable and `-resume`-able.

**Why the head/worker split matters:** the head node drives the whole pipeline, so losing it
kills the run — it runs on stable On-Demand capacity. Individual tasks are retriable, so they run
on much cheaper Spot capacity. This single trade-off is what makes large runs both reliable and
affordable.

---

## Architecture

The app synthesizes to one CloudFormation stack, `NextflowBatchStack`, composed of **nested
stacks** (one CloudFormation stack per concern, wired together by a parent):

```
                          NextflowBatchStack (orchestrator)
                                     │
   ┌──────────┬──────────┬──────────┼───────────┬────────────┬─────────────┐
   ▼          ▼          ▼           ▼           ▼            ▼             ▼
 VpcStack   S3Stack   IamStack   Launch       BatchStack   NextflowStack  NextflowEcrStack
                                 TemplateStack                             (image build)
   │          │                    │              │            │
   └ vpc,     └ bucketName         └ user-data    └ compute     └ head-node job
     subnets    (+ SSM param)        bootstrap      envs +        definition +
                                                    queues        IAM role
                                                    (+ SSM params)
```

Shared values (the S3 bucket name and job-queue ARNs) are published to **SSM Parameters** and read
back downstream via CloudFormation dynamic references (`{{resolve:ssm:...}}`). This indirection is
deliberate: the Nextflow job definition and role resolve those values at deploy time.

| Nested stack            | Responsibility                                                                                                                                                                                                                                                                            |
| -------------------------| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **VpcStack**            | Creates a VPC (`10.0.0.0/16`, 2 Availability Zones, 2 NAT gateways, public + private subnets) or looks up an existing one. Compute runs in the **private** subnets.                                                                                                                       |
| **S3Stack**             | Creates (retained on delete, S3-managed encryption) or imports the workflow bucket. Adds lifecycle rules to abort stale multipart uploads and expire old work-dir intermediates.                                                                                                          |
| **IamStack**            | The Batch job / instance / spot-fleet / service roles, scoped to the bucket.                                                                                                                                                                                                              |
| **LaunchTemplateStack** | An [EC2 launch template](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-templates.html) with cloud-init that installs the CloudWatch agent + AWS CLI v2, mounts S3 reference data via Mountpoint for S3 at `/mnt/s3-reference`, and ships instance logs to S3/CloudWatch. |
| **BatchStack**          | Spot (`SPOT_PRICE_CAPACITY_OPTIMIZED`) and On-Demand (`BEST_FIT_PROGRESSIVE`) compute environments, matching job queues, a security group, a log group, and a generic job definition.                                                                                                     |
| **NextflowStack**       | The Nextflow head-node job definition (`nextflow-<namespace>`) and its IAM role (Batch submit + S3 access).                                                                                                                                                                               |
| **NextflowEcrStack**    | Builds the Nextflow head-node image: an ECR repo + a CodeBuild project, triggered on deploy by a small Lambda-backed custom resource.                                                                                                                                                     |

---

## Prerequisites

You need four things on your laptop. Links go to the official install guides.

1. **[Bun](https://bun.com/)** — this project uses Bun as both its JavaScript runtime and package
   manager: it runs the TypeScript CDK app directly (no compile step) and installs dependencies.
   [Install Bun](https://bun.com/docs/installation), optionally via a version manager like
   [mise](https://mise.jdx.dev/). Check with `bun --version`. (Node.js 18+ works too — see the note
   below.)
2. **The AWS CLI v2** — for credentials and for submitting jobs.
   [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
   Check with `aws --version`.
3. **AWS credentials** for your (sandbox) account, configured locally.
   Run `aws configure` (or set `AWS_PROFILE`) and confirm with `aws sts get-caller-identity`.
   See [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
   > At the hackathon you'll be given credentials for a sandbox account — use those.
4. **Docker is *not* required.** The head-node image is built in the cloud by CodeBuild.

You do **not** need to install the CDK globally — this repo pins it as a dev dependency, so
`bunx aws-cdk ...` just works after `bun install`.

> **Using Node instead of Bun?** Node.js 18+ works too. Add `ts-node` as a dev dependency
> (`npm install -D ts-node`), change the `app` line in `cdk.json` to
> `"npx ts-node --prefer-ts-exts bin/aws_batch_squared.ts"`, then use `npm install` and
> `npx cdk <cmd>` wherever this guide says `bun install` / `bunx aws-cdk`. Node is AWS's officially
> supported runtime; Bun is the default here because it runs the TypeScript app directly and is a
> little faster (running the CDK under Bun is
> [demonstrated by a CDK maintainer](https://github.com/mrgrain/bun-cdk-app)).

---

## Quick start

From the `aws_batch_squared/` directory:

```bash
# 1. Install project dependencies
bun install

# 2. One-time per account+region: prepare it for the CDK
#    (safe to re-run; does nothing if already bootstrapped)
bunx aws-cdk bootstrap

# 3. See what will be created, without touching AWS
bunx aws-cdk synth

# 4. Deploy everything. Takes ~15-25 min the first time
#    (the VPC, NAT gateways, and the CodeBuild image build dominate).
bunx aws-cdk deploy
```

The default settings in `cdk.context.json` are chosen so this works out of the box: it **creates**
a new VPC and S3 bucket and **builds** the Nextflow image for you. No IDs to fill in.

> **Heads-up on the image build.** The head-node image is built by CodeBuild, kicked off during
> deploy but running **asynchronously** — `cdk deploy` can return before the image finishes building
> and pushing to ECR. If your very first job submission can't find the image, give it a few minutes
> and check the `nextflow-image-build-<namespace>` project in the
> [CodeBuild console](https://console.aws.amazon.com/codesuite/codebuild/projects).

Deployment runs in `eu-west-2` (London) by default. To target a different region, set
`CDK_DEFAULT_REGION` before deploying, e.g. `CDK_DEFAULT_REGION=us-east-1 bunx aws-cdk deploy`.

When it finishes, the CLI prints **stack outputs** — note these, you'll use them to submit jobs:

- `S3BucketName` — your workflow bucket (auto-named `cdk-new1-cdk-nfbatch-eu-west-2-<account-id>`).
- `OnDemandJobQueueArn` / `SpotJobQueueArn` — the two Batch queues.

> **Switching AWS accounts later?** `cdk.context.json` caches account-specific lookups (like
> Availability Zones). If you point the project at a different account and see stale values, delete
> the cached entries in that file (or the whole file) and re-run — the CDK will look them up again.
> See [Context](https://docs.aws.amazon.com/cdk/v2/guide/context.html).

---

## Submitting a workflow

After deploy, submit a Nextflow pipeline to the **head-node job definition** on the **On-Demand
queue**. The head node then launches child Batch jobs for each pipeline process.

Resource names come from the `namespace` context value (default `cdk-nfbatch-eu-west-2`):

- Head-node job definition: `nextflow-<namespace>`
- On-Demand queue (submit here): `OnDemand-<namespace>`
- Spot queue (child jobs land here automatically): `Spot-<namespace>`

Here's a run of the [nf-core/sarek](https://nf-co.re/sarek) test profile. Replace `BUCKET` with
your `S3BucketName` output:

```bash
NAMESPACE="cdk-nfbatch-eu-west-2"
BUCKET="cdk-new1-cdk-nfbatch-eu-west-2-<account-id>"

aws batch submit-job \
  --job-name sarek-test \
  --job-queue "OnDemand-$NAMESPACE" \
  --job-definition "nextflow-$NAMESPACE" \
  --container-overrides '{
    "command": [
      "nf-core/sarek",
      "--outdir", "s3://'"$BUCKET"'/results/sarek-test/",
      "-profile", "test"
    ]
  }'
```

How the command is interpreted:

- The **first** element (`nf-core/sarek`) is the Nextflow **project** — a pipeline name/URL or an
  `s3://` URI.
- The **rest** are ordinary Nextflow / pipeline arguments.
- The container entrypoint prepends `nextflow run` for you and writes a `nextflow.config` that sets
  the AWS Batch executor and the S3 work directory (from the `NF_JOB_QUEUE` / `NF_WORKDIR` /
  `NF_LOGSDIR` env vars the job definition provides). **Do not** put `run` in the command yourself.

Where data goes (all under your bucket):

- Work directory (intermediates): `s3://<bucket>/_nextflow/runs/`
- Session cache + logs (enables `-resume`): `s3://<bucket>/_nextflow/logs/`
- Results: wherever you point `--outdir`.

By default, child (worker) jobs are dispatched to the **Spot** queue for cost savings. To force
workers onto On-Demand for a single run, add `NF_JOB_QUEUE` to the `environment` in
`--container-overrides`.

---

## Benchmarking

A core goal of this project is a **reproducible way to measure runtime and cost** of whole-genome
sequencing (WGS) workflows as they scale — and to compare workflow variants and storage strategies
on the same data. This section describes what to run and how to record results.

### Datasets

Two open human germline WGS datasets:

- **1000 Genomes Project** — a large public catalogue of human genomes, available with no egress
  cost from the AWS Open Data registry (public bucket `s3://1000genomes`, `us-east-1`). See
  [registry.opendata.aws/1000-genomes](https://registry.opendata.aws/1000-genomes/).
- **Personal Genome Project UK (PGP-UK)** — up to **100 genomes** from an open-consent research
  cohort. See [personalgenomes.org.uk](https://www.personalgenomes.org.uk/).

> The exact per-sample file locations (the `s3://...` FASTQ URIs) go in the samplesheet CSVs below.
> The templates ship with placeholders for you to fill in.

> **Region tip.** `s3://1000genomes` lives in `us-east-1`. Reading it from a stack deployed in
> another region adds latency and cross-region transfer cost. For large runs, either deploy in
> `us-east-1` or copy the inputs you need into your own bucket in the deployment region first.

### What to run — the input samplesheet

Benchmark runs use [nf-core/sarek](https://nf-co.re/sarek) driven by a standard nf-core
**samplesheet CSV**. For germline WGS the columns are:

| Column | Meaning |
| --- | --- |
| `patient` | Patient / individual identifier. |
| `sex` | `XX`, `XY`, or `NA`. |
| `status` | `0` for normal / germline (use `1` only for tumour samples). |
| `sample` | Sample identifier, unique per sample. |
| `lane` | Sequencing lane; use multiple rows with the same `sample` for multi-lane data. |
| `fastq_1` / `fastq_2` | `s3://` URIs to the paired-end FASTQ files. |

Fill-in templates live in [`benchmarks/samplesheets/`](./benchmarks/samplesheets):

- [`1000genomes.template.csv`](./benchmarks/samplesheets/1000genomes.template.csv)
- [`pgpuk.template.csv`](./benchmarks/samplesheets/pgpuk.template.csv)

Create one samplesheet per scale by including that many samples (rows), then upload it to your
bucket:

```bash
# e.g. the 10-genome scenario
aws s3 cp benchmarks/samplesheets/wgs_n10.csv \
  s3://<bucket>/benchmarks/samplesheets/wgs_n10.csv
```

### Scale scenarios

Run the same workflow at increasing scale and record runtime + cost at each point. Create each
samplesheet from the templates above.

| Scenario | # genomes | Suggested dataset | Samplesheet (you create it) | Purpose |
| --- | --- | --- | --- | --- |
| S1 | 1 | either | `benchmarks/samplesheets/wgs_n1.csv` | Smoke test; per-genome baseline. |
| S2 | 10 | 1000 Genomes | `benchmarks/samplesheets/wgs_n10.csv` | Early scaling behaviour. |
| S3 | 50 | 1000 Genomes | `benchmarks/samplesheets/wgs_n50.csv` | Mid-scale throughput. |
| S4 | 100 | PGP-UK | `benchmarks/samplesheets/wgs_n100.csv` | Full PGP-UK cohort. |
| S5 | 500 | 1000 Genomes | `benchmarks/samplesheets/wgs_n500.csv` | Large-scale cost / runtime. |
| S6 | 1000 | 1000 Genomes | `benchmarks/samplesheets/wgs_n1000.csv` | Stress test; maximum fan-out. |

> Start small. Confirm S1 completes end-to-end and lands results in S3 **before** launching the
> larger scenarios — the big runs cost real money and take hours.

### Running a scenario

Submit the head node with the scenario's samplesheet and a unique output prefix:

```bash
NAMESPACE="cdk-nfbatch-eu-west-2"
BUCKET="cdk-new1-cdk-nfbatch-eu-west-2-<account-id>"
SCALE="n1"

aws batch submit-job \
  --job-name "sarek-bench-$SCALE" \
  --job-queue "OnDemand-$NAMESPACE" \
  --job-definition "nextflow-$NAMESPACE" \
  --container-overrides '{
    "command": [
      "nf-core/sarek",
      "-r", "3.5.1",
      "--input",  "s3://'"$BUCKET"'/benchmarks/samplesheets/wgs_'"$SCALE"'.csv",
      "--outdir", "s3://'"$BUCKET"'/benchmarks/results/'"$SCALE"'/",
      "--genome", "GATK.GRCh38",
      "--tools",  "haplotypecaller"
    ]
  }'
```

Always pin the pipeline revision (`-r 3.5.1`) so every run uses the **same** pipeline code — that's
essential for comparable numbers.

### Recording results

Track every run in a results CSV. A template is provided at
[`benchmarks/results.template.csv`](./benchmarks/results.template.csv) — copy it to
`benchmarks/results.csv` and append one row per run. Capture at least: scale, dataset, workflow
variant, storage strategy, instance types, wall-clock time, total vCPU-hours, estimated cost, and
the derived **cost per genome**.

- **Runtime:** add `-with-report` and `-with-timeline` to the command to have Nextflow emit an
  execution report and timeline for the run.
- **Cost:** tag runs (see [Add cost-allocation tags](#right-sizing-and-cost)) and read spend back
  from [AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html),
  or estimate from vCPU-hours × instance price.

### Workflow variants to compare

**Standard (GATK).** The command above uses the default bwa-mem + GATK HaplotypeCaller path.

**Sentieon-accelerated (optional).** [Sentieon](https://www.sentieon.com/) reimplements several GATK
steps for speed and is a natural comparison point. Swap the aligner and caller:

```jsonc
"command": [
  "nf-core/sarek", "-r", "3.5.1",
  "--input",   "s3://<bucket>/benchmarks/samplesheets/wgs_n1.csv",
  "--outdir",  "s3://<bucket>/benchmarks/results/n1-sentieon/",
  "--genome",  "GATK.GRCh38",
  "--aligner", "sentieon-bwamem",
  "--tools",   "sentieon_haplotyper"
]
```

Sentieon is **commercial and requires a licence.** nf-core/sarek reads it from a Nextflow secret
named `SENTIEON_LICENSE_BASE64` (a base64-encoded licence-server `IP:Port` string, or a `.lic`
file). Because runs here are launched non-interactively by the head node, to benchmark Sentieon
you'll need to:

1. **Make the secret available on the head node before `nextflow run`** — for example, store the
   licence in [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
   and extend the head-node entrypoint (`docker/nextflow-head/nextflow.aws.sh`) to run
   `nextflow secrets set SENTIEON_LICENSE_BASE64 <base64-value>` on startup.
2. **Ensure the compute subnets can reach your Sentieon licence server** (outbound to its
   `IP:Port`) — the private subnets have NAT egress, so an internet-reachable server works.

See the [nf-core/sarek Sentieon docs](https://nf-co.re/sarek/docs/usage) for the full option list
(`sentieon_dedup`, `sentieon_dnascope`, emit modes, joint germline genotyping, and so on).

### Stretch goal — bring your own pipeline

The platform is **not** sarek-specific: the head node runs whatever Nextflow **project** you pass as
the first command element. To benchmark a different pipeline, swap it in:

```jsonc
"command": [
  "nf-core/rnaseq", "-r", "3.14.0",
  "--input",  "s3://<bucket>/benchmarks/samplesheets/rnaseq.csv",
  "--outdir", "s3://<bucket>/benchmarks/results/rnaseq/",
  "--genome", "GRCh38"
]
```

Any nf-core pipeline, a public Git URL, or an `s3://` project works. Two things to watch: each
pipeline has its **own samplesheet schema**, and its **reference data** must be available (bundled
by the pipeline, uploaded under the bucket's `reference/` prefix, or fetched at runtime). Keep
`-r <version>` pinned for reproducibility.

## Monitoring and troubleshooting

- **Follow the run live.** In the [AWS Batch console](https://console.aws.amazon.com/batch/home),
  open the head-node job and its log stream. Each `Submitted process >` line corresponds to a child
  job appearing on the Spot queue.
- **Logs** for the head node and tasks land in [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)
  under `/aws/batch/job`. Instance-level bootstrap logs go to `/aws/ecs/container-instance/<namespace>`.
- **Jobs stuck in `RUNNABLE`?** That usually means Batch can't place them: check the compute
  environment's max vCPUs, that instances can reach the internet (NAT gateway), and that the vCPU/
  memory you requested fits the allowed instance types.
- **Resume a failed run** by re-submitting with `-resume` — the session cache in
  `s3://<bucket>/_nextflow/logs/` lets Nextflow skip completed processes.
- **Reference data.** Upload shared inputs under the bucket's reference prefix (default
  `reference/`); it's mounted read-only on every instance at `/mnt/s3-reference`.

---

## Cost awareness and cleanup

Running compute costs money. A few things worth knowing for a sandbox budget:

- **Compute scales to zero.** With `minCpus = 0`, idle queues cost nothing — you pay only while
  jobs run.
- **NAT gateways are the sneaky always-on cost.** The two NAT gateways in the created VPC bill per
  hour and per GB even when no jobs run. If you're pausing for a while, tear the stack down.
- **Spot saves the most.** Workers on Spot can be up to ~90% cheaper than On-Demand; see
  [AWS Batch pricing](https://aws.amazon.com/batch/pricing/) and
  [EC2 Spot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html).
- **S3 storage.** Work-dir intermediates under `_nextflow/runs/` auto-expire after 30 days by
  default (tunable via `workDirExpirationDays`). Results and reference data are never auto-deleted.

Tear everything down when you're done:

```bash
bunx aws-cdk destroy
```

> **The S3 bucket is retained by design** (`RemovalPolicy.RETAIN`) so you don't lose results to an
> accidental `destroy`. After destroying the stack, delete the bucket manually if you want to stop
> paying for stored data.

---

## Configuration reference

All settings are [CDK context](https://docs.aws.amazon.com/cdk/v2/guide/context.html) values. Set
them in `cdk.context.json` or pass `-c key=value` on the CLI. Validation lives in
`bin/aws_batch_squared.ts`.

| Key                                   | Default                        | Notes                                                                                                 |
| ---------------------------------------| --------------------------------| -------------------------------------------------------------------------------------------------------|
| `namespace`                           | `cdk-nfbatch-eu-west-2`        | Names Batch/compute resources and SSM paths.                                                          |
| `groupName`                           | `cdk-new1`                     | Prefix for SSM parameter paths and the generated bucket name.                                         |
| `createVpc`                           | `true` (via context)           | If `false`, you must provide `vpcId` **and** `subnetIds`.                                             |
| `vpcId` / `subnetIds`                 | —                              | Existing VPC/subnets (required only when `createVpc` is `false`).                                     |
| `existingBucket`                      | `false`                        | If `true`, `s3BucketName` is required.                                                                |
| `s3BucketName`                        | auto                           | Workflow bucket. Auto-named `<groupName>-<namespace>-<account>` when created.                         |
| `buildNextflowImage`                  | `true` (via context)           | If `true`, builds the head-node image via CodeBuild. If `false`, `existingNextflowImage` is required. |
| `existingNextflowImage`               | —                              | ECR image URI to use instead of building one.                                                         |
| `batchComputeAmi`                     | latest ECS-optimized AL2 (SSM) | AMI for compute instances; resolved from a public SSM parameter.                                      |
| `s3ReferencePath`                     | `reference`                    | Prefix under the bucket mounted at `/mnt/s3-reference`.                                               |
| `onDemandMinCpus` / `onDemandMaxCpus` | `0` / `500`                    | On-Demand vCPU bounds (min 0 = scale to zero).                                                        |
| `spotMinCpus` / `spotMaxCpus`         | `0` / `500`                    | Spot vCPU bounds.                                                                                     |
| `batchOnDemandInstanceTypes`          | `optimal`                      | Comma-separated list, or the literal `optimal`.                                                       |
| `batchSpotInstanceTypes`              | `optimal`                      | Comma-separated list, or the literal `optimal`.                                                       |
| `workDirExpirationDays`               | `30`                           | Days after which `_nextflow/runs/` intermediates expire (`0` disables). Newly-created buckets only.   |

Default region is `eu-west-2`, falling back to `CDK_DEFAULT_REGION`.

Example: deploy against your own existing VPC and bucket, using a pre-built image:

```bash
bunx aws-cdk deploy \
  -c createVpc=false \
  -c vpcId=vpc-xxxxxxxx \
  -c subnetIds=subnet-aaaa,subnet-bbbb \
  -c existingBucket=true \
  -c s3BucketName=my-nfbatch-bucket \
  -c buildNextflowImage=false \
  -c existingNextflowImage=<account>.dkr.ecr.eu-west-2.amazonaws.com/nextflow-head:latest
```

---

## Command reference

```bash
bun install            # install dependencies

bun run build          # tsc — type-check / compile TypeScript (optional; Bun runs TS directly)
bun run watch          # tsc -w — recompile on change
bun test               # run tests with Bun's built-in test runner

bunx aws-cdk bootstrap # one-time per account/region
bunx aws-cdk synth     # synthesize CloudFormation (dry run)
bunx aws-cdk diff      # diff against the deployed stack
bunx aws-cdk deploy    # deploy to the default AWS account/region
bunx aws-cdk destroy   # tear down (the S3 bucket is retained by design)
```

Bun runs the TypeScript app directly (the `app` command in `cdk.json` is
`bun bin/aws_batch_squared.ts`), so no build step is required before `synth`/`deploy`.

> **Testing:** `bun test` runs the suite. `test/aws_batch_squared.test.ts` is currently a
> placeholder — there's no real coverage yet. See [Potential improvements](#potential-improvements).

---

## Project layout

```
bin/aws_batch_squared.ts     # CDK app entrypoint: reads context, validates, instantiates the stack
lib/nextflow-batch-stack.ts  # orchestrator: wires nested stacks + SSM parameters
lib/vpc-stack.ts             # networking
lib/s3-stack.ts              # workflow bucket
lib/iam-stack.ts             # roles/policies
lib/launch-template-stack.ts # EC2 bootstrap (cloud-init user-data)
lib/batch-stack.ts           # compute environments + job queues
lib/nextflow-stack.ts        # Nextflow head-node job definition + role
lib/nextflow-ecr-stack.ts    # head-node image build (ECR + CodeBuild)
docker/nextflow-head/        # head-node container entrypoint (nextflow.aws.sh)
benchmarks/                  # benchmarking samplesheet + results CSV templates
test/                        # tests (Bun test runner)
cdk.context.json             # committed context (deployment settings + cached lookups)
```

---

## Potential improvements

This is a solid, working baseline. Below are enhancements worth exploring — a natural set of
hackathon challenges. They're roughly ordered by impact.

### Performance — storage and the data path

Today, task containers stage inputs/outputs to and from S3 using the AWS CLI (`aws.batch.cliPath`),
and shared reference data is exposed via Mountpoint for S3. That's simple and dependency-free, but
I/O-heavy genomics steps spend real time copying files. The scratch/shared-storage layer is often
the single biggest lever on both runtime and cost — a great thing to **benchmark**.

- **Benchmark the storage strategies.** There's no universal winner; each trades cost, speed, and
  complexity differently. Candidates worth measuring against the same workload:

  | Strategy | Gist | Trade-offs |
  | --- | --- | --- |
  | AWS CLI staging (current) | Copy inputs down / outputs up per task. | Simplest, no extra deps; slow on staging-bound steps. |
  | [Mountpoint for S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint.html) (current, for reference data) | S3 prefix as a read-mostly folder. | Great for shared read-only reference; not a general read/write scratch. |
  | Higher-throughput [EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html) (`gp3` tuned IOPS/throughput, or `io2`) | Bigger/faster network block volume for scratch. | Predictable, easy; pay for provisioned IOPS/throughput; network-bound. |
  | **Local NVMe instance-store** | Ephemeral disks physically attached to the instance. | Fastest local scratch; data is lost on stop/interruption. Requires NVMe instance families (`d`-suffix: `c5d`, `m5ad`, `m5d`, `r5ad`, `r5d`, `i3`, `i4i`). Merge multiple NVMe disks into one big volume in the launch-template cloud-init with LVM (`pvcreate` → `vgcreate` → `lvcreate -l 100%FREE`). |
  | [s3fs](https://github.com/s3fs-fuse/s3fs-fuse) / FUSE-over-S3 | Mount a bucket read/write via FUSE. | Easy POSIX-ish access; performance and consistency vary. |
  | Network file share — [Amazon EFS](https://docs.aws.amazon.com/efs/latest/ug/whatisefs.html) | Managed shared NFS across tasks. | True shared POSIX; higher latency/cost for heavy throughput. |
  | [Amazon FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html) | High-performance parallel filesystem, S3-linked. | Excellent throughput at scale; more setup and standing cost. |
  | [Seqera Fusion](https://docs.seqera.io/fusion) | S3 presented as POSIX, cached on local NVMe. | Fast, no explicit staging; needs privileged tasks and a Seqera licence at scale. |
  | [JuiceFS](https://juicefs.com/docs/community/introduction/) | POSIX filesystem over S3 + a metadata engine. | Strong POSIX semantics; needs a separate metadata store (e.g. Redis via [Amazon ElastiCache](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html)). |

  Capture runtime **and** cost per strategy at each scale point — that comparison is itself a useful
  hackathon output.
- **Cache container images per host.** Set `ECS_IMAGE_PULL_BEHAVIOR=once` so a large image is pulled
  once per instance instead of once per task — a big win when a run fans out into hundreds of tasks
  reusing the same image.
- **Tune kernel write-back** (`vm.dirty_bytes` / `vm.dirty_background_bytes`) on worker instances so
  large sequential writes streaming to S3 don't balloon host memory.

### Right-sizing and cost

- **Right-size the head node.** The head node runs the Nextflow driver, not the heavy compute, yet
  `nextflow-stack.ts` hardcodes `vcpus: 4` / `memory: 16384` / a `3600s` timeout. Surface these as
  context and tune them: a smaller head node is cheaper (it runs On-Demand for the whole pipeline),
  but very large DAGs need enough memory and a longer timeout. Measure and pick per pipeline.
- **A dedicated head compute environment.** The head node currently shares the On-Demand queue with
  any On-Demand workers. A small, separate On-Demand environment just for head nodes isolates the
  long-lived driver from bursty worker demand.
- **Add cost-allocation tags.** Tag every resource (e.g. `project`, `team`, `pipeline`, `run-id`) so
  spend can be attributed per team/run in [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
  once the tags are activated as [cost-allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html).
  CDK makes this easy with [`Tags.of(scope).add(...)`](https://docs.aws.amazon.com/cdk/v2/guide/tagging.html)
  at the app level. This directly feeds the benchmarking cost numbers.
- **Review CloudWatch log retention and S3 lifecycle** to keep long-running-account costs predictable.

### Testing and CI

- **Add unit tests** with the CDK [assertions module](https://docs.aws.amazon.com/cdk/v2/guide/testing.html):
  `Template.fromStack(...)` checks per nested stack (queues, compute envs, IAM scoping, job-definition
  env vars) plus the validation branches in `bin/aws_batch_squared.ts`. These need no AWS account and
  run in milliseconds via `bun test`.
- **Add local integration tests** against a local AWS emulator (e.g. [LocalStack](https://docs.localstack.cloud/))
  so a `synth`/`deploy` smoke test can run on a laptop **and** in [GitHub Actions](https://docs.github.com/actions),
  catching wiring problems without spending on real infrastructure.
- **Wire up CI** (build + `synth` + tests on pull requests), and consider adding automated
  security/compliance scanning such as [cdk-nag](https://github.com/cdklabs/cdk-nag).

### Extensibility

- **Package this as a reusable L3 CDK construct.** CDK constructs come in levels: L1 maps 1:1 to raw
  CloudFormation, L2 adds sensible defaults, and L3 (a "pattern") bundles a whole solution behind a
  small, opinionated API (see [construct levels](https://docs.aws.amazon.com/cdk/v2/guide/constructs.html#constructs_lib)).
  Exposing the whole platform as a single `NextflowBatch` construct — with typed props instead of raw
  context — would let others drop it into their own CDK app in a few lines, compose it with other
  infrastructure, and extend it cleanly. Publishing it (npm, or multi-language via
  [JSII](https://aws.github.io/jsii/)) would make it genuinely reusable beyond this repo.

### Maintainability

- **Tighten IAM.** Some policies use broad `Resource: "*"` or `s3:*`. Scope actions and resources to
  the minimum required, and review the `AmazonS3ReadOnlyAccess` managed-policy attachments.
- **Externalize the launch-template user-data.** The multipart cloud-init is built as a long array of
  string literals; moving it to a template asset file would make it far easier to read and maintain.

---

## License

Released under the **MIT License** — see the [`LICENSE`](./LICENSE) file.

The software is provided "as is", without warranty of any kind, and has **not** undergone any
security review. Please read the disclaimer at the top of this README before deploying anything.
