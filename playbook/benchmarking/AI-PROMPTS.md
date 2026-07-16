# AI-Assisted Prompts for Systematic Benchmarking

These prompts are designed to help you leverage AI tools (Kiro, Claude, ChatGPT, GitHub Copilot) to accelerate your benchmarking work. Copy and paste these prompts into your AI tool, customizing the placeholders as needed.

---

## Prompt 1: Generate Storage Backend Test Plan

**Goal**: Create a detailed test execution plan for comparing different AWS storage backends.

**Context for AI**:
I'm working on Goal 2 (Systematic Benchmarking) of the AWS Nextflow Hackathon. I need to compare storage backends (S3 native, S3 Mountpoint, EFS, FSx for Lustre, and NVMe instance store) when running nf-core/sarek pipeline on AWS Batch.

**Prompt**:
```
I need to systematically benchmark 5 different storage backends for Nextflow pipelines on AWS Batch:
1. Amazon S3 (native Nextflow support)
2. S3 Mountpoint for Amazon S3 (FUSE-based)
3. Amazon EFS (managed NFS)
4. Amazon FSx for Lustre (high-performance parallel filesystem)
5. NVMe instance store (local ephemeral storage)

Generate a detailed test execution plan that includes:
- Infrastructure setup steps for each storage backend (CDK stack modifications needed)
- Nextflow configuration changes required for each backend
- Test methodology: what metrics to collect, how to ensure fair comparison
- Expected results and how to interpret them
- Common pitfalls to avoid

The pipeline is nf-core/sarek running on AWS Batch with 10 whole genome samples. Focus on making the comparison fair and reproducible.
```

**Expected Output**:
- Step-by-step infrastructure setup guide
- Nextflow config snippets for each storage backend
- Metrics collection strategy
- Results interpretation guidance

---

## Prompt 2: Create Scaling Test Automation Script

**Goal**: Generate a shell script to automate running scaling tests across multiple genome counts.

**Context for AI**:
I need to test nf-core/sarek at 1, 5, 10, 50, and 100 genomes to measure scaling behavior.

**Prompt**:
```
Generate a bash script that automates running nf-core/sarek scaling tests on AWS Batch. The script should:

1. Accept parameters:
   - Genome counts to test: [1, 5, 10, 50, 100]
   - Storage backend: s3-native, efs, fsx-lustre, etc.
   - Compute strategy: spot, ondemand, hybrid
   - S3 bucket for input data and results
   - AWS Batch job queue name

2. For each genome count:
   - Generate a sample sheet with the correct number of samples
   - Submit the Nextflow pipeline to AWS Batch
   - Wait for completion
   - Collect metrics from Nextflow trace and CloudWatch
   - Record results to CSV file (using results.template.csv schema)
   - Tag AWS resources with test identifier for cost tracking

3. Error handling:
   - Retry failed pipeline runs (up to 3 times)
   - Log errors to separate file
   - Continue to next test on failure

4. Output:
   - CSV file with all benchmark results
   - Summary report showing cost and runtime trends

Make the script modular so I can easily modify it for different test scenarios.
```

**Expected Output**:
- Bash script with command-line argument parsing
- Functions for each test stage
- CloudWatch metrics collection commands
- CSV output formatting

---

## Prompt 3: Generate Variant Caller Comparison Analysis

**Goal**: Create a data analysis script to compare GATK vs Sentieon results.

**Context for AI**:
I have benchmark results for GATK HaplotypeCaller and Sentieon Haplotyper. I need to analyze and visualize the differences.

**Prompt**:
```
I have CSV files with benchmark results comparing GATK HaplotypeCaller vs Sentieon Haplotyper on AWS Batch:

- gatk_results.csv: Contains runtime, cost, CPU utilization for GATK runs (1, 10, 100 genomes)
- sentieon_results.csv: Same metrics for Sentieon runs

Generate a Python script using pandas and matplotlib that:

1. Loads both CSV files and merges them by genome count

2. Calculates:
   - Speedup factor: GATK runtime / Sentieon runtime
   - Cost savings percentage: (GATK cost - Sentieon cost) / GATK cost * 100
   - Cost per genome for each variant caller
   - Licensing cost breakeven point (assuming Sentieon license is $20,000/year)

3. Generates visualizations:
   - Bar chart: Runtime comparison (GATK vs Sentieon) for each genome count
   - Line chart: Cost per genome vs genome count for both callers
   - Scatter plot: Speedup factor vs genome count
   - Breakeven analysis chart showing at what annual genome volume Sentieon becomes cost-effective

4. Outputs:
   - Summary statistics table (mean speedup, cost savings, etc.)
   - All charts saved as PNG files
   - Markdown report summarizing findings and recommendations

Include error handling for missing data and clear axis labels/titles on all charts.
```

**Expected Output**:
- Python script with pandas data processing
- Matplotlib visualization code
- Markdown report generation
- Statistical summary calculations

---

## Prompt 4: Design CloudWatch Dashboard for Benchmarking

**Goal**: Create a CloudWatch dashboard configuration to monitor benchmark runs in real-time.

**Context for AI**:
I need to monitor AWS Batch job execution, compute environment utilization, and costs during benchmark runs.

**Prompt**:
```
Generate a CloudWatch dashboard JSON configuration for monitoring Nextflow benchmarking runs on AWS Batch. The dashboard should include:

1. **Batch Job Metrics Section**:
   - Running job count (time series)
   - Pending job count (time series)
   - Failed job count (time series)
   - Job success rate (percentage gauge)

2. **Compute Environment Metrics Section**:
   - Desired vCPUs (time series)
   - Current vCPU utilization (time series)
   - Average CPU utilization percentage (gauge)
   - Average memory utilization (gauge)

3. **Cost Tracking Section**:
   - Estimated compute cost to-date (single value metric)
   - Cost trend over time (time series)
   - Cost by instance type (pie chart)

4. **Storage Performance Section**:
   - S3 request rate (GetObject and PutObject)
   - S3 data transfer (BytesDownloaded and BytesUploaded)
   - EFS/FSx throughput (if applicable)

5. **Custom Metrics Section**:
   - Spot interruption count (if using Spot instances)
   - Job retry count
   - Average queue wait time

Use appropriate time ranges (last 6 hours) and auto-refresh every 1 minute. Include annotations for test start/end times.

Provide the dashboard JSON that I can import into CloudWatch, plus AWS CLI commands to create custom metrics.
```

**Expected Output**:
- CloudWatch dashboard JSON configuration
- AWS CLI commands for publishing custom metrics
- Metric filter patterns for extracting data from logs
- Documentation on how to import and use the dashboard

---

## Prompt 5: Create Results Consolidation and Reporting Script

**Goal**: Generate a script to aggregate all benchmark results into a unified report for the community playbook.

**Context for AI**:
I have multiple CSV files from different benchmark tests (storage comparison, scaling analysis, variant caller comparison, Spot vs On-Demand). I need to consolidate them into a cohesive report.

**Prompt**:
```
Generate a Python script that consolidates benchmark results from multiple tests into a comprehensive report for the community playbook. The script should:

1. **Input Files**:
   - storage_benchmark_results.csv (S3, EFS, FSx, NVMe comparison)
   - scaling_results.csv (1, 5, 10, 50, 100 genome tests)
   - variant_caller_results.csv (GATK vs Sentieon)
   - spot_ondemand_results.csv (Spot vs On-Demand comparison)

2. **Data Processing**:
   - Load all CSV files into pandas DataFrames
   - Validate data completeness (check for missing required columns)
   - Calculate summary statistics for each benchmark dimension
   - Identify optimal configurations (lowest cost per genome, fastest runtime, best cost-performance balance)

3. **Generate Report Sections**:
   
   **a. Executive Summary**:
   - Key findings (bullet points)
   - Recommended configurations for different use cases
   - Cost savings achieved across all tests
   
   **b. Storage Backend Comparison**:
   - Table comparing all storage backends (runtime, cost, throughput)
   - Winner by category (fastest, cheapest, best balance)
   - Recommendations matrix: when to use each backend
   
   **c. Scaling Analysis**:
   - Scaling curves (runtime and cost vs genome count)
   - Identification of bottlenecks
   - Optimal batch size recommendations
   
   **d. Variant Caller Comparison**:
   - GATK vs Sentieon performance comparison
   - Breakeven analysis for Sentieon licensing
   - Recommendations by use case
   
   **e. Spot vs On-Demand**:
   - Cost savings achieved with Spot
   - Interruption rate and reliability impact
   - Recommendations for compute strategy

4. **Visualizations**:
   - Generate all charts in previous prompts
   - Create comparison matrices (heatmaps showing best options by criteria)
   - Cost-performance Pareto frontier chart

5. **Output Formats**:
   - Markdown report (for GitHub playbook)
   - HTML report (for website)
   - PDF report (for sharing)
   - Summary statistics JSON (for programmatic access)

Include proper markdown formatting, section headers, tables, and embedded chart references. Make the report publication-ready.
```

**Expected Output**:
- Python script for data consolidation and report generation
- Markdown report template
- Chart generation code
- Summary statistics calculations
- Export functions for multiple formats

---

## How to Use These Prompts

1. **Copy the entire prompt** (including the "Context for AI" section) into your AI tool
2. **Customize placeholders** with your specific values (file paths, bucket names, etc.)
3. **Iterate on the output**: If the AI's first response isn't perfect, ask follow-up questions:
   - "Can you add error handling for X?"
   - "How would I modify this for Y scenario?"
   - "Can you explain this section in more detail?"
4. **Validate the output**: Test generated code, review configurations, ensure alignment with benchmark methodology
5. **Document your changes**: Add comments and notes for future reproducibility

## Tips for Better AI Responses

- **Be specific about your environment**: Mention AWS region, instance types, pipeline versions
- **Provide context about constraints**: Time limits, budget constraints, skill level
- **Ask for explanations**: Request comments in code or explanatory notes in configurations
- **Request examples**: Ask for sample data, test cases, or usage examples
- **Iterate**: Don't expect perfection on the first try; refine the output through conversation