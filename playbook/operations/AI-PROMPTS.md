# AI Assistant Prompts for Operations and Observability

These prompts are designed to help you leverage AI tools (Kiro, Claude, ChatGPT, GitHub Copilot, etc.) to build operational infrastructure and documentation for running Nextflow pipelines on AWS.

## How to Use These Prompts

1. **Copy the entire context file** (the main hackathon context document) into your AI tool first
2. **Then paste one of these prompts** to get targeted assistance
3. **Iterate**: Ask follow-up questions, request examples, or ask for clarification as needed

---

## Prompt 1: Cost Allocation Tagging Strategy

**Goal:** Generate a complete cost allocation tagging strategy for Nextflow pipelines on AWS

**Context for AI:**
I'm working on Goal 3 (Operations and Observability) of the AWS Nextflow Hackathon. I need to design a comprehensive cost allocation tagging strategy that allows us to track costs by project, pipeline, execution, and resource type.

**What I need:**
1. A complete tag schema with tag keys and example values
2. CDK code snippets showing how to apply these tags to:
   - AWS Batch compute environments
   - S3 buckets
   - EC2 instances (head nodes)
   - EFS/FSx file systems
   - CloudWatch Log Groups
3. A method for propagating Nextflow session IDs to AWS resource tags
4. Instructions for validating that tags are correctly applied
5. Example Cost Explorer queries using these tags

**Expected output:**
- Markdown documentation of the tagging strategy
- CDK code (Python or TypeScript) with tagging examples
- Cost Explorer filter definitions
- Validation procedure

**Constraints:**
- Tags must follow AWS naming conventions (no spaces, limited special characters)
- Tag schema should support both single-pipeline and multi-project deployments
- Consider tag inheritance from parent resources to child resources

---

## Prompt 2: CloudWatch Dashboard for Nextflow Operations

**Goal:** Create a production-ready CloudWatch dashboard for monitoring Nextflow pipeline operations

**Context for AI:**
I'm building an operational observability solution for Nextflow pipelines running on AWS Batch (Goal 3). I need a CloudWatch dashboard that provides at-a-glance visibility into pipeline health, compute utilization, and cost.

**What I need:**
1. A CloudWatch dashboard JSON definition with the following widgets:
   - Current running pipelines count
   - AWS Batch job queue depth (pending jobs)
   - Compute environment utilization (% of max vCPUs in use)
   - Failed jobs in last 24 hours
   - Average task runtime (from Batch metrics)
   - S3 request rate and throughput
   - Head node CPU and memory utilization
   - Daily cost estimate (if possible via API)
2. Explanation of each metric:
   - What it measures
   - What CloudWatch namespace and metric name to use
   - Normal vs abnormal value ranges
3. Instructions for importing this dashboard into an AWS account
4. Customization guide (how to adapt for specific pipelines)

**Expected output:**
- CloudWatch dashboard JSON (ready to import)
- Metrics dictionary explaining each widget
- Import instructions
- Optional: Screenshot or description of dashboard layout

**Constraints:**
- Use only AWS-native metrics (CloudWatch Metrics, no custom metrics initially)
- Dashboard must be region-specific (metrics are regional)
- Stay within CloudWatch dashboard limits (max 100 widgets per dashboard)

---

## Prompt 3: CloudWatch Logs Insights Queries for Troubleshooting

**Goal:** Generate a library of useful CloudWatch Logs Insights queries for debugging Nextflow pipelines

**Context for AI:**
I'm documenting operational best practices for Nextflow on AWS (Goal 3). I need a set of CloudWatch Logs Insights queries that help operators quickly find and diagnose pipeline issues.

**What I need:**
At least 10 CloudWatch Logs Insights queries covering:
1. Find all failed tasks in the last 24 hours
2. Find tasks that exceeded expected runtime (e.g., >2 hours)
3. Find tasks with specific error patterns (e.g., "OutOfMemoryError", "No space left on device")
4. Find tasks running on Spot instances that were interrupted
5. Find all log entries from a specific Nextflow session ID
6. Aggregate task runtimes by process name
7. Find tasks that were retried (and how many times)
8. Find the most recent logs for a failed pipeline
9. Count error types (group by error message pattern)
10. Find tasks with abnormally high memory usage

**For each query:**
- Provide the CloudWatch Logs Insights query syntax
- Explain what the query does
- Describe what log group(s) to run it against
- Explain how to interpret the results
- Provide example use cases (when would you run this query)

**Expected output:**
- Markdown document with query library
- Each query in a code block (ready to copy-paste)
- Explanations and interpretation guides

**Constraints:**
- Queries must work with standard Nextflow and AWS Batch log formats
- Assume logs are in CloudWatch Logs (not external logging systems)
- Queries should complete in reasonable time (<30 seconds for 1 day of logs)

---

## Prompt 4: Cost Optimization Checklist and Analysis

**Goal:** Create an actionable cost optimization checklist for Nextflow pipelines on AWS

**Context for AI:**
I'm working on cost monitoring and optimization (Goal 3). I need a prioritized checklist of cost optimization strategies specifically for Nextflow genomics pipelines on AWS, with expected savings and implementation difficulty.

**What I need:**
1. A checklist of at least 10 cost optimization strategies, including:
   - Spot instance usage
   - S3 lifecycle policies
   - Right-sizing compute environments
   - Storage backend selection
   - Container image optimization
   - S3 VPC endpoint usage
   - Batch job array optimization
   - Head node right-sizing
   - Data transfer cost reduction
   - CloudWatch log retention tuning
2. For each strategy:
   - Clear description of the optimization
   - Expected cost savings (percentage or dollar amount if possible)
   - Implementation difficulty (Low/Medium/High)
   - Trade-offs or risks
   - How to measure the impact
   - When to apply this strategy (use cases)
3. Prioritization framework:
   - Which optimizations to tackle first (quick wins)
   - Which require more planning (long-term optimizations)
4. Example cost analysis:
   - Before/after comparison for at least one strategy
   - How to calculate cost per genome

**Expected output:**
- Markdown checklist document
- Prioritization matrix (quick wins vs high effort/high impact)
- Example cost analysis with calculations
- Implementation guides for top 3 optimizations

**Constraints:**
- Focus on AWS-native optimizations (no third-party tools)
- Savings estimates should be realistic and conservative
- Consider trade-offs (e.g., Spot savings vs reliability)

---

## Prompt 5: Alerting Strategy and Runbook

**Goal:** Design a comprehensive alerting strategy with runbook procedures for Nextflow pipeline operations

**Context for AI:**
I'm setting up operational alerting for Nextflow pipelines on AWS (Goal 3). I need to define critical alerts, configure CloudWatch Alarms, and create runbook procedures for responding to each alert type.

**What I need:**
1. Alert definitions for at least 10 scenarios:
   - Pipeline failure (non-zero exit code)
   - High task failure rate (>10% in last hour)
   - Compute environment at max capacity (can't scale further)
   - Head node out of memory or disk space
   - Spot interruption rate exceeding threshold
   - Pipeline runtime exceeding expected duration
   - Compute environment underutilized for extended period
   - Unusual cost spike (daily spend >X)
   - Batch job queue depth growing without bound
   - Storage costs increasing rapidly
2. For each alert:
   - Metric and threshold (what triggers the alert)
   - Alert severity (Critical/Warning/Info)
   - SNS topic to publish to
   - Runbook procedure:
     - What to check first
     - How to diagnose root cause
     - Remediation steps
     - When to escalate
3. CDK code for creating these CloudWatch Alarms
4. SNS topic configuration (email, SMS, or Slack integration)
5. Alert suppression strategy (how to avoid false positives and alert fatigue)

**Expected output:**
- Alert definitions table (Markdown)
- CDK code (Python or TypeScript) for CloudWatch Alarms and SNS topics
- Runbook document with procedures for each alert
- Alert configuration best practices

**Constraints:**
- Alerts must be actionable (clear what to do when alert fires)
- Thresholds should be tunable (not hardcoded)
- Consider alert fatigue (avoid noisy alerts)
- Runbook procedures should be executable by non-experts

---

## Prompt 6: Container Image Optimization Guide

**Goal:** Create a practical guide for optimizing Docker container images for Nextflow pipelines

**Context for AI:**
I'm documenting operational best practices for Nextflow on AWS (Goal 3, spec: operational-best-practices.md). I need a guide that shows how to optimize container images to reduce startup time and improve pipeline efficiency.

**What I need:**
1. Dockerfile optimization techniques:
   - Choosing minimal base images
   - Multi-stage builds
   - Layer caching strategies
   - Removing unnecessary files
2. Before/after example:
   - "Naive" Dockerfile (large, slow to build/pull)
   - Optimized Dockerfile (smaller, faster)
   - Size comparison (MB)
   - Pull time comparison (seconds)
3. ECR best practices:
   - Image tagging strategy (avoid `latest`)
   - Lifecycle policies for old images
   - Image scanning for vulnerabilities
4. Image caching strategies:
   - Pre-pulling images to compute nodes
   - Custom AMI with pre-cached images
   - When caching is worth the effort
5. Measurement guide:
   - How to measure container pull time
   - How to measure impact on total pipeline runtime
   - When pull time is a bottleneck (short-running tasks)

**Expected output:**
- Markdown guide with Dockerfile examples
- Before/after comparison (with measurements)
- ECR configuration examples (lifecycle policies)
- Decision framework for when to optimize

**Constraints:**
- Examples should be relevant to genomics/bioinformatics tools
- Optimizations should not break tool functionality
- Focus on practical, measurable improvements

---

## Prompt 7: Right-Sizing Decision Framework

**Goal:** Generate a decision framework and calculator for right-sizing compute resources for Nextflow pipelines

**Context for AI:**
I'm working on operational best practices (Goal 3). I need a practical framework for choosing appropriate EC2 instance types for Nextflow head nodes and setting max vCPU limits for AWS Batch compute environments.

**What I need:**
1. Head node instance type selector:
   - Input variables: pipeline complexity (number of processes), expected concurrency, DAG depth
   - Output: Recommended instance type (e.g., t3.medium, m5.large, c5.xlarge)
   - Decision tree or formula
2. Max vCPU calculator for Batch compute environments:
   - Input variables: number of samples, average task CPUs, expected parallelism
   - Output: Recommended max vCPU setting
   - Formula or rules of thumb
3. Instance type recommendations for worker jobs:
   - Compute-intensive tasks (high CPU, low memory)
   - Memory-intensive tasks (high memory, moderate CPU)
   - I/O-intensive tasks (high disk/network throughput)
   - Balanced tasks (general-purpose)
4. Monitoring checklist:
   - What metrics indicate undersized resources
   - What metrics indicate oversized resources
   - When to scale up vs when to optimize code
5. Example calculations:
   - Small pipeline (10 samples, 20 processes)
   - Medium pipeline (100 samples, 30 processes)
   - Large pipeline (1000 samples, 40 processes)

**Expected output:**
- Decision framework document (Markdown)
- Formulas or decision trees
- Example calculations for different pipeline sizes
- Monitoring checklist

**Constraints:**
- Recommendations should be conservative (prefer slight over-provisioning to under-provisioning)
- Consider AWS account vCPU quotas
- Factor in cost (balance performance with cost-efficiency)

---

## Tips for Getting the Best Results

- **Be specific about your experience level**: If you're a beginner, say so — the AI will provide more detailed explanations
- **Request examples**: Ask for code snippets, configuration files, or sample data
- **Ask for clarification**: If the AI's response assumes knowledge you don't have, ask for more detail
- **Iterate**: Start with a prompt, then refine based on the AI's output
- **Reference the specs**: Mention which spec file (e.g., "cost-monitoring-setup.md") you're working on for more targeted responses
- **Request validation steps**: Ask how to test or verify that the generated solution works

---

## Example Follow-Up Questions

After getting an initial response, you can ask:

- "Can you provide a complete working example I can test?"
- "What are the most common mistakes when implementing this?"
- "How would this change if I'm using [specific tool or service]?"
- "Can you explain [concept] in simpler terms?"
- "What are the trade-offs I should consider?"
- "How do I troubleshoot if this doesn't work as expected?"
- "Can you generate CDK code for this configuration?"
- "What CloudWatch metrics should I monitor to validate this is working?"

---

**Remember:** These prompts are starting points. The most valuable AI interactions happen when you have a conversation — ask follow-ups, request refinements, and iterate until you have exactly what you need for the hackathon playbook.