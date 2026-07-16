# AI Prompts for Pipeline Migration

This file contains starter prompts to accelerate your pipeline migration work using AI tools like Kiro, Claude, ChatGPT, or GitHub Copilot.

## How to Use These Prompts

1. Copy the entire context file (event overview document) into your AI chat session first
2. Then use these prompts to get specific guidance
3. Iterate on the AI's responses by asking follow-up questions
4. Adapt the generated content to your specific pipeline

---

## Prompt 1: Generate Migration Audit Checklist

**Goal:** Create a comprehensive pre-migration audit checklist for my specific pipeline

**Context for AI:**
```
I have an existing Nextflow DSL2 pipeline that performs [DESCRIBE YOUR PIPELINE: e.g., "variant calling using GATK"]. It currently runs on [ENVIRONMENT: e.g., "my laptop" or "university HPC cluster"]. The pipeline uses [NUMBER] Docker containers and processes [DATA VOLUME: e.g., "10-50 whole genome samples at a time"].

Key characteristics:
- Pipeline structure: [e.g., "linear workflow" or "branching with parallel processes"]
- Reference data: [e.g., "human genome hg38, dbSNP, 30GB total"]
- Current resource usage: [e.g., "peak 32 CPU cores, 128GB RAM"]
- External dependencies: [e.g., "GATK container from Broad, custom R scripts"]
```

**Prompt:**
```
Based on the AWS Nextflow Hackathon context (Goal 4: Bring Your Own Pipeline), generate a detailed migration audit checklist for my pipeline. Include:

1. Pipeline structure analysis (what to check for AWS Batch compatibility)
2. Container inventory template (how to document all containers used)
3. Path analysis checklist (how to find hard-coded local paths)
4. Resource requirements mapping (how to translate current resources to AWS Batch labels)
5. Reference data staging requirements (what data needs to move to S3)
6. Risk assessment framework (how to identify blockers vs minor issues)

Format as a markdown checklist I can print and fill out.
```

**Expected Output:**
A detailed markdown checklist document with sections for each audit area, including specific items to verify and space to record findings.

---

## Prompt 2: Generate ECR Migration Commands

**Goal:** Create shell scripts to migrate my pipeline's containers to Amazon ECR

**Context for AI:**
```
My pipeline uses these Docker containers:
1. [CONTAINER 1: e.g., "broadinstitute/gatk:4.3.0.0"]
2. [CONTAINER 2: e.g., "quay.io/biocontainers/samtools:1.15"]
3. [CONTAINER 3: e.g., "my-custom-image:latest from private registry"]

My AWS details:
- Region: [e.g., "us-east-1"]
- AWS Account ID: [e.g., "123456789012"]
- ECR repository naming convention: [e.g., "nextflow-tools/"]
```

**Prompt:**
```
Using the container list above, generate a complete shell script that:

1. Pulls each container from its source registry
2. Tags the container for my ECR repositories
3. Creates ECR repositories if they don't exist
4. Pushes containers to ECR
5. Includes error handling and progress messages
6. Outputs a summary with the new ECR URIs

Also provide:
- ECR lifecycle policy JSON to keep only the last 10 images
- IAM policy snippet for AWS Batch to pull from these ECR repos
```

**Expected Output:**
A complete bash script with error handling, plus ECR lifecycle policy JSON and IAM policy document. Output should be copy-pasteable and production-ready.

---

## Prompt 3: Transform Nextflow Config for AWS Batch

**Goal:** Convert my existing nextflow.config to work with AWS Batch

**Context for AI:**
```
Here is my current nextflow.config:

[PASTE YOUR CONFIG FILE]

My AWS infrastructure:
- S3 bucket: [e.g., "s3://my-nextflow-bucket"]
- AWS Batch job queue: [e.g., "nextflow-job-queue"]
- AWS region: [e.g., "us-east-1"]
- ECR URIs for containers: [e.g., "123456789012.dkr.ecr.us-east-1.amazonaws.com/nextflow-tools/gatk:4.3.0.0"]
```

**Prompt:**
```
Based on Goal 4 (Bring Your Own Pipeline) in the hackathon context, transform my nextflow.config for AWS Batch execution. Include:

1. Convert executor from [current: e.g., "local"] to "awsbatch"
2. Update all file paths from local filesystem to S3 URIs
3. Update container directives with ECR URIs
4. Add AWS-specific settings (region, queue, workDir)
5. Configure retry strategy for Spot instance interruptions
6. Create an "aws" profile block for easy switching
7. Add resource labels appropriate for AWS Batch

Provide:
- Complete transformed config file
- Side-by-side comparison showing key changes
- Explanation of why each change was needed
```

**Expected Output:**
Transformed nextflow.config file with AWS Batch configuration, comparison table, and detailed change explanations.

---

## Prompt 4: Design S3 Bucket Organization

**Goal:** Create an S3 bucket structure optimized for my pipeline

**Context for AI:**
```
My pipeline characteristics:
- Input data: [e.g., "FASTQ files, 50-100GB per sample"]
- Reference data: [e.g., "human genome, indices, databases, 50GB total"]
- Output data: [e.g., "VCF files, BAM files, QC reports, 30GB per sample"]
- Expected usage: [e.g., "10-20 concurrent pipeline runs, weekly batches"]
- Retention requirements: [e.g., "keep results for 90 days, archive reference data indefinitely"]
```

**Prompt:**
```
Using the hackathon's reference data staging guidance (Goal 4), design an S3 bucket organization strategy for my pipeline. Include:

1. Complete bucket structure diagram (folders/prefixes)
2. Naming conventions for different data types
3. Where to place reference data, inputs, work directory, results
4. S3 lifecycle policy JSON for automatic archival/deletion
5. Cost estimation for storage (with assumptions documented)
6. Data access patterns (which paths are read-heavy vs write-heavy)
7. Recommendations for S3 storage classes per data type

Also provide AWS CLI commands to:
- Create the bucket structure
- Upload reference data efficiently
- Set lifecycle policies
```

**Expected Output:**
Complete S3 organization design document with diagrams, lifecycle policies, cost estimates, and ready-to-use AWS CLI commands.

---

## Prompt 5: Create Incremental Testing Plan

**Goal:** Design a systematic testing strategy to validate my migrated pipeline

**Context for AI:**
```
My pipeline details:
- Pipeline name: [e.g., "variant-calling-pipeline"]
- Typical runtime on original system: [e.g., "6 hours for 10 samples"]
- Critical output files: [e.g., "sample.vcf.gz, sample.bam, multiqc_report.html"]
- Known-good baseline: [e.g., "I have results from local run for comparison"]

AWS resources available:
- AWS Batch job queue: [e.g., "nextflow-job-queue"]
- S3 bucket: [e.g., "s3://my-nextflow-bucket"]
- Test budget: [e.g., "$50 for testing"]
```

**Prompt:**
```
Based on the Testing and Validation Strategy module in Goal 4, create a comprehensive incremental testing plan for my migrated pipeline. Include:

1. **Phase 1 (Smoke Test)**:
   - Test dataset specification (what minimal data to use)
   - Expected runtime and cost
   - Success criteria
   - Command to run

2. **Phase 2 (Integration Test)**:
   - Medium-scale test dataset
   - Expected runtime and cost
   - What to validate beyond basic functionality
   - Command to run

3. **Phase 3 (Scale Test)**:
   - Production-scale dataset
   - Expected runtime and cost
   - Performance benchmarks to collect
   - Command to run

4. **Automated Validation Script**:
   - Shell or Python script to compare outputs
   - Checksum validation for key files
   - Result summary generation

5. **Troubleshooting Playbook**:
   - Top 5 likely errors and their fixes
   - How to access Batch job logs
   - How to debug failed processes

Provide ready-to-use test commands and scripts.
```

**Expected Output:**
Complete testing plan document with phase-by-phase instructions, automated validation scripts, and troubleshooting guide.

---

## Prompt 6: Compare AWS Batch vs Amazon Health Omics

**Goal:** Decide whether my pipeline should use AWS Batch or Amazon Health Omics

**Context for AI:**
```
My pipeline characteristics:
- Type: [e.g., "nf-core/sarek variant calling"]
- Customization level: [e.g., "standard nf-core with minor config changes" or "heavily customized with proprietary tools"]
- Execution frequency: [e.g., "weekly batches of 50 samples"]
- Compliance needs: [e.g., "HIPAA required" or "no special compliance requirements"]
- Team expertise: [e.g., "limited AWS experience" or "experienced with AWS infrastructure"]
```

**Prompt:**
```
Using the Health Omics evaluation guidance from Goal 4, help me decide between AWS Batch and Amazon Health Omics for my pipeline. Provide:

1. **Decision Matrix**: Score my pipeline against selection criteria:
   - Setup complexity preference
   - Customization requirements
   - Compliance needs
   - Cost sensitivity
   - Team AWS expertise

2. **Detailed Comparison**:
   - Estimated setup time for each platform
   - Estimated per-run cost for typical workload
   - What I gain/lose with each choice

3. **Recommendation**: Which platform suits my pipeline better and why?

4. **Migration Implications**:
   - If Health Omics: what adaptations are required?
   - If AWS Batch: what complexity should I prepare for?

5. **Next Steps**: Concrete action items based on recommendation
```

**Expected Output:**
Decision analysis document with scoring matrix, cost comparison, clear recommendation, and actionable next steps.

---

## Tips for Getting Better AI Results

1. **Be Specific**: Replace bracketed placeholders with your actual details
2. **Iterate**: If the AI's first response isn't quite right, ask follow-up questions
3. **Request Examples**: Ask for "show me an example" if concepts are unclear
4. **Validate Output**: AI-generated code should be reviewed and tested before production use
5. **Combine Prompts**: Use outputs from one prompt as inputs to the next
6. **Ask for Explanations**: Request "explain why" to understand the reasoning

## Example Follow-Up Questions

- "Can you explain why you chose that S3 lifecycle policy?"
- "What happens if I skip the smoke test phase?"
- "Show me how to debug this specific error: [paste error message]"
- "How would this change if I used Spot instances?"
- "Generate a CDK stack to automate this setup"
- "What's the estimated cost breakdown for this approach?"