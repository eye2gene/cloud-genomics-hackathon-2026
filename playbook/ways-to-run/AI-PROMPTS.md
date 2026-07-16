# AI Tool Prompts for Goal 1: Ways to Run Nextflow on AWS

This document contains starter prompts to accelerate your work on documenting execution patterns for running Nextflow on AWS. Copy and paste these prompts into your AI tool (Kiro, Claude, ChatGPT, etc.) to generate implementation guidance, code, or documentation.

---

## Prompt 1: Generate Getting-Started Guide for Laptop to Batch

**Goal:** Create a step-by-step tutorial for the simplest execution pattern.

**Context for AI:**
I'm working on documenting the "Laptop to Batch" execution pattern for running Nextflow on AWS. This pattern has Nextflow running on a user's laptop and submitting jobs to AWS Batch. The target audience includes bioinformatics researchers who are new to AWS but comfortable with command-line tools.

**Expected Output:**
A comprehensive getting-started guide in markdown format that includes:
- Prerequisites (AWS CLI, Nextflow installation, Docker)
- AWS infrastructure setup (minimal Batch environment using CDK or manual steps)
- Nextflow configuration file for AWS Batch executor
- Step-by-step workflow execution instructions
- Troubleshooting tips for common issues (credential errors, job stuck in RUNNABLE, network issues)
- Architecture diagram (text-based or description for diagram generation)
- When to use this pattern vs other patterns

**Prompt:**
```
Generate a comprehensive getting-started guide for the "Laptop to Batch" Nextflow execution pattern on AWS. This pattern runs Nextflow on a local laptop/workstation and submits jobs to AWS Batch for execution. Include:

1. Prerequisites section covering:
   - AWS CLI v2 installation and configuration
   - Nextflow installation (version 22.04+)
   - Docker installation for local testing
   - AWS account setup and IAM permissions needed

2. AWS Infrastructure setup (provide both CDK and manual Console options):
   - VPC configuration (use default VPC or create minimal VPC)
   - S3 bucket for work directory and results
   - AWS Batch compute environment (On-Demand or Spot)
   - AWS Batch job queue
   - IAM roles (execution role, instance role)

3. Nextflow configuration file (`nextflow.config`):
   - AWS Batch executor configuration
   - Resource specifications (CPU, memory)
   - Container settings (ECR, Docker registries)
   - Work directory pointing to S3

4. Step-by-step execution workflow:
   - Preparing input data and staging to S3
   - Launching a pipeline with `nextflow run`
   - Monitoring execution (CLI output, AWS Batch console, CloudWatch Logs)
   - Retrieving results from S3

5. Troubleshooting section:
   - "Access Denied" errors when accessing S3
   - Jobs stuck in RUNNABLE state
   - Container image not found errors
   - Pipeline hangs or laptop disconnects (importance of persistent connection)

6. Decision criteria: when to use Laptop to Batch vs EC2 Head or Batch Squared patterns

Format as markdown. Include code blocks for configuration files and CLI commands. Use clear section headings.
```

---

## Prompt 2: Create Decision Matrix for Choosing Execution Patterns

**Goal:** Help users choose the right pattern for their needs.

**Context for AI:**
I need to create a decision-making tool (matrix or flowchart) that helps hackathon attendees choose between Laptop to Batch, EC2 Head to Batch, Batch Squared, and Amazon Health Omics execution patterns based on their requirements.

**Expected Output:**
A decision matrix or flowchart description that evaluates patterns across dimensions like: pipeline duration, infrastructure management preference, cost sensitivity, automation needs, and technical complexity. Include prose explanations for each decision point.

**Prompt:**
```
Create a decision matrix or flowchart to help users choose between four Nextflow execution patterns on AWS:

1. Laptop to Batch (Nextflow on local laptop, submits to AWS Batch)
2. EC2 Head to Batch (Nextflow on persistent EC2 instance, submits to AWS Batch)
3. Batch Squared (Nextflow head node runs as Batch job, submits worker jobs)
4. Amazon Health Omics (fully managed AWS service for genomics workflows)

Evaluate each pattern across these dimensions:
- **Pipeline Duration**: How long does the pipeline run? (minutes, hours, days)
- **Infrastructure Management**: Do you want to manage infrastructure or prefer fully managed?
- **Cost Model**: Pay for persistent head node vs pay per run?
- **Automation Needs**: Manual execution vs event-driven/scheduled?
- **Technical Complexity**: Setup and operational complexity
- **Reliability**: Dependency on laptop connectivity
- **Use Case**: Development/testing vs production, genomics-specific vs general

Provide:
- A comparison table with rows for each pattern and columns for each dimension
- Prose recommendations like "Choose Laptop to Batch if... Choose EC2 Head if..."
- A flowchart-style decision tree (describe in text or pseudo-code)
- Example scenarios: "I'm a grad student testing pipelines on small datasets" → Laptop to Batch. "I'm running daily production variant calling for 100 samples" → EC2 Head or Health Omics.

Format as markdown with tables and bullet points.
```

---

## Prompt 3: Generate Infrastructure as Code for EC2 Head Pattern

**Goal:** Produce deployable CDK code for the EC2 Head to Batch pattern.

**Context for AI:**
I need to create or adapt CDK stacks (TypeScript or Python) to deploy the EC2 Head to Batch pattern. This includes an EC2 instance with Nextflow installed, AWS Batch compute environment, job queue, S3 bucket, and appropriate IAM roles.

**Expected Output:**
CDK stack code (TypeScript or Python) that provisions all necessary infrastructure. Include comments explaining each resource and configuration options (instance type, VPC settings, compute environment type).

**Prompt:**
```
Generate AWS CDK code (TypeScript preferred, or Python) to deploy the "EC2 Head to Batch" Nextflow execution pattern. This pattern has a persistent EC2 instance running Nextflow that submits jobs to AWS Batch.

Infrastructure requirements:
1. **VPC**: Create new VPC or allow using existing VPC (configurable via context parameter)
   - Public or private subnet for EC2 head node
   - S3 VPC endpoint for cost optimization
   
2. **EC2 Head Node**:
   - Instance type: `t3.medium` or `m5.large` (configurable)
   - AMI: Amazon Linux 2023 or Ubuntu 22.04
   - User data script to install:
     - Nextflow (latest version)
     - AWS CLI v2
     - Docker (optional, for local testing)
     - tmux or screen (for persistent sessions)
   - IAM instance role with permissions:
     - AWS Batch (SubmitJob, DescribeJobs, TerminateJob)
     - S3 (read/write to work bucket)
     - ECR (pull container images)
     - CloudWatch Logs (write logs)
   - Security group allowing SSH from specified CIDR (configurable)
   - Key pair for SSH access (configurable)

3. **AWS Batch**:
   - Compute environment (On-Demand and/or Spot)
   - Job queue linked to compute environment
   - Service role and execution role for Batch

4. **S3 Bucket**:
   - Encrypted bucket for work directory and results
   - Versioning enabled
   - Lifecycle policies (optional, to delete old work directories)

5. **Outputs**:
   - EC2 instance ID and public/private IP
   - Batch job queue ARN
   - S3 bucket name
   - SSH command to connect to EC2 instance

Configuration via CDK context (cdk.json):
- `ec2_instance_type`: Instance type for head node
- `key_pair_name`: SSH key pair name
- `vpc_id`: Existing VPC ID (optional, create new if not provided)
- `enable_spot`: Enable Spot instances in Batch compute environment
- `batch_max_vcpus`: Max vCPUs for Batch compute environment

Include:
- CDK stack class definition
- IAM role and policy definitions
- User data script (inline or as separate file reference)
- Comments explaining each resource and why it's needed
- Example cdk.json snippet showing configuration options

Format as CDK TypeScript code with comments. Organize into logical sections (networking, compute, storage, IAM).
```

---

## Prompt 4: Document Batch Squared Pattern with Entrypoint Script

**Goal:** Explain how Batch Squared works and provide the custom entrypoint script.

**Context for AI:**
I need to document the Batch Squared (Head on Batch) pattern where the Nextflow head node runs as an AWS Batch job. This requires a custom container image with an entrypoint script that handles cloning the pipeline, running Nextflow, and uploading results.

**Expected Output:**
A detailed explanation document covering the pattern, Dockerfile for the head node container, and the entrypoint bash script that orchestrates execution.

**Prompt:**
```
Document the "Batch Squared" (Head on Batch) execution pattern for Nextflow on AWS, where the Nextflow head node itself runs as an AWS Batch job that submits worker jobs. Include:

1. **Pattern Overview**:
   - Architecture diagram description (head node as Batch job, submits worker jobs to same or different queue)
   - Benefits: fully serverless, no persistent infrastructure costs, event-driven execution
   - Use cases: scheduled pipelines, event-triggered pipelines, intermittent execution

2. **Head Node Container Dockerfile**:
   - Base image: `public.ecr.aws/seqera-labs/nextflow:24.04.4`
   - Install AWS CLI v2
   - Copy custom entrypoint script (`nextflow.aws.sh`)
   - Set working directory and entrypoint

3. **Entrypoint Script (`nextflow.aws.sh`)**:
   - Environment variables:
     - `PIPELINE_REPO`: Git repository URL (optional)
     - `PIPELINE_S3_PATH`: S3 path to pipeline bundle (optional)
     - `NF_WORKDIR`: S3 work directory
     - `NF_OUTDIR`: S3 output directory
     - `NF_CONFIG_S3_PATH`: S3 path to custom nextflow.config (optional)
     - `NF_PARAMS_FILE`: S3 path to params file (optional)
   - Script logic:
     - Clone pipeline from Git OR download from S3
     - Download custom config and params file if provided
     - Run Nextflow with appropriate arguments (pass through CLI args)
     - Capture exit code
     - Upload Nextflow logs (.nextflow.log, .nextflow/ directory) to S3
     - Exit with appropriate code for Batch job status

4. **AWS Batch Job Definition**:
   - Job definition configuration:
     - Container image (ECR URI)
     - CPU and memory (e.g., 4 vCPUs, 16 GB for head node)
     - IAM job role (must have batch:SubmitJob permission)
     - Environment variables
     - Timeout (e.g., 48 hours)
   - CDK code snippet for creating job definition

5. **Submitting Head Node Jobs**:
   - AWS CLI command to submit job
   - How to pass parameters via container overrides
   - EventBridge rule for scheduled execution (example)
   - Lambda function for S3-triggered execution (example)

6. **Monitoring and Debugging**:
   - Viewing job status in AWS Batch console
   - Accessing CloudWatch logs for head node and worker jobs
   - Common failure scenarios and troubleshooting

Provide:
- Dockerfile code block
- Complete entrypoint script (bash)
- AWS CLI commands for job submission
- CDK TypeScript or Python code for job definition creation
- Markdown formatting with clear section headings
```

---

## Prompt 5: Compare Amazon Health Omics vs AWS Batch for Genomics Workloads

**Goal:** Create a detailed comparison to guide users in choosing between these services.

**Context for AI:**
Amazon Health Omics is a managed service for genomics workflows, while AWS Batch is a general-purpose batch computing service. I need a comparison document that helps users understand when to use each for Nextflow genomics pipelines.

**Expected Output:**
A comprehensive comparison covering setup complexity, cost model, features, limitations, and specific use case recommendations. Include a side-by-side table and narrative explanations.

**Prompt:**
```
Create a detailed comparison between Amazon Health Omics Workflows and AWS Batch for running Nextflow genomics pipelines on AWS. Cover:

1. **Service Overview**:
   - AWS Batch: General-purpose managed batch computing
   - Health Omics: Purpose-built managed service for genomics/omics workflows

2. **Setup Complexity**:
   - AWS Batch: What infrastructure you must provision (VPC, Batch compute environments, job queues, IAM roles)
   - Health Omics: What's required (workflow registration, IAM service role)
   - Time to first run for each

3. **Workflow Definition**:
   - AWS Batch: Nextflow with awsbatch executor, any Nextflow version
   - Health Omics: Nextflow DSL2 or WDL, specific requirements (container images, no work directory in S3)

4. **Cost Model**:
   - AWS Batch: EC2 instance costs (On-Demand or Spot pricing), storage costs (S3, EFS, FSx)
   - Health Omics: Per-run-hour pricing ($0.50/hour), Sequence Store ($0.01/GB-month), Reference Store
   - Example cost comparison for 2-hour variant calling pipeline with 100 GB data

5. **Features**:
   - AWS Batch: Full control over compute (instance types, custom AMIs), storage backends (S3, EFS, FSx, NVMe), networking (VPC configuration)
   - Health Omics: Genomic-optimized storage (Sequence Store, Reference Store with compression), automatic cost optimization, HIPAA-eligible

6. **Limitations**:
   - AWS Batch: Higher operational overhead, requires AWS infrastructure knowledge
   - Health Omics: Service availability (limited regions), less control over compute, Nextflow DSL2 only, max workflow duration limits

7. **Use Case Recommendations**:
   - Choose AWS Batch if:
     - Non-genomics pipelines or custom workflows
     - Need tight control over compute (specific instance types, custom AMIs)
     - Very long-running pipelines (>24 hours)
     - High-frequency execution (hundreds of runs per day)
     - Service not available in your region
   - Choose Health Omics if:
     - Genomics-focused workloads (variant calling, RNA-seq, etc.)
     - Want zero infrastructure management (fully managed)
     - Need genomic-optimized storage (Sequence/Reference Stores)
     - Compliance requirements (HIPAA-eligible)
     - Small to medium scale intermittent runs

8. **Migration Considerations**:
   - Adapting Nextflow workflow for Health Omics (DSL2, omics:// URIs)
   - Cost analysis before migration
   - Testing strategy (parallel runs on both platforms)

9. **Regional Availability**:
   - List AWS regions where each service is available

Provide:
- Side-by-side comparison table (rows: dimensions, columns: AWS Batch vs Health Omics)
- Narrative sections explaining each dimension
- Decision flowchart: start with questions ("Is my workload genomics-specific?", "Do I need tight cost control?") → recommended service
- Markdown formatting with tables and bullet points
```

---

## How to Use These Prompts

1. **Copy the entire prompt** (including context and expected output descriptions) into your AI tool.
2. **Customize as needed**: Add specific details about your environment, constraints, or preferences.
3. **Iterate**: If the AI's response isn't quite right, refine your prompt or ask follow-up questions.
4. **Combine outputs**: Use generated content as a starting point, then edit for accuracy and clarity.
5. **Validate**: Test generated code and commands in your AWS environment before including in documentation.

## Tips for Best Results

- **Be specific**: The more context you provide, the better the AI's response.
- **Request examples**: Ask for concrete code snippets, CLI commands, or sample data.
- **Ask for explanations**: Include "explain why" or "describe the rationale" for deeper understanding.
- **Iterate incrementally**: Start with high-level structure, then drill into details with follow-up prompts.
- **Reference the hackathon context file**: Mention specific tools, constraints, or goals from the event overview to keep responses aligned.