# Benchmark Test Methodology

**Test ID:** test-YYYYMMDD-description  
**Date:** YYYY-MM-DD  
**Operator:** Your Name  
**Goal:** Goal 2 - Systematic Benchmarking  

---

## Test Objective

<!-- Describe what you are testing and why -->
**Primary question:**  
TODO: What specific hypothesis or comparison are you investigating?

**Dimensions being tested:**  
- [ ] Storage backend (specify: S3, EFS, FSx, etc.)  
- [ ] Scaling behavior (specify: N samples)  
- [ ] Variant caller (specify: GATK, Sentieon)  
- [ ] Compute strategy (specify: Spot, On-Demand)  

---

## Test Environment

### AWS Configuration
- **Region:** TODO (e.g., us-east-1)
- **Availability Zones:** TODO (e.g., us-east-1a, us-east-1b)
- **Account ID:** TODO (last 4 digits for reference)

### Compute Configuration
- **Batch Compute Environment:** TODO (name or ID)
- **Job Queue:** TODO (name or ID)
- **Instance Types:** TODO (e.g., c5.2xlarge, r5.4xlarge)
- **Max vCPUs:** TODO
- **Compute Strategy:** TODO (Spot / On-Demand / Mixed)
- **AMI ID:** TODO (if custom AMI used)

### Storage Configuration
- **Storage Backend:** TODO (S3 native, S3 Mountpoint, EFS, FSx, NVMe)
- **Work Directory:** TODO (full S3 or filesystem path)
- **Results Directory:** TODO (full S3 or filesystem path)
- **Storage Configuration Details:**
  - EFS/FSx throughput mode: TODO (if applicable)
  - FSx deployment type: TODO (Scratch/Persistent, if applicable)
  - S3 lifecycle policies: TODO (enabled/disabled)

### Network Configuration
- **VPC ID:** TODO
- **Subnet IDs:** TODO
- **S3 VPC Endpoint:** TODO (yes/no)
- **NAT Gateway:** TODO (yes/no)

---

## Pipeline Configuration

### Pipeline Details
- **Pipeline:** nf-core/sarek
- **Version:** TODO (e.g., 3.4.0)
- **Commit/Revision:** TODO (if using specific git revision)
- **Profile:** TODO (e.g., awsbatch, docker)

### Input Dataset
- **Sample Sheet:** TODO (filename, e.g., 1000genomes-5samples.csv)
- **Number of Samples:** TODO
- **Data Source:** TODO (e.g., 1000 Genomes Project, PGP-UK)
- **Reference Genome:** TODO (e.g., GRCh38, GRCh37)
- **Sequencing Coverage:** TODO (e.g., 30x)
- **Total Input Data Size:** TODO GB

### Variant Calling Configuration
- **Variant Caller:** TODO (GATK HaplotypeCaller / Sentieon)
- **Caller Version:** TODO
- **Calling Parameters:** TODO (describe any non-default parameters)

### Nextflow Configuration Files Used
- TODO: List all config files used (e.g., s3-native.config, spot-instances.config)
- TODO: Note any custom parameter overrides

---

## Execution Details

### Pre-Test Setup
- **Reference data staging:** TODO (describe how reference genome was staged)
- **Container images:** TODO (list ECR repositories or public images used)
- **IAM permissions verified:** TODO (yes/no)
- **Cost allocation tags applied:** TODO (list tags)

### Test Execution
- **Start Time:** TODO (YYYY-MM-DD HH:MM:SS UTC)
- **End Time:** TODO (YYYY-MM-DD HH:MM:SS UTC)
- **Total Runtime:** TODO minutes
- **Nextflow Command:**
  ```bash
  TODO: Paste exact nextflow run command used
  ```

### Monitoring Approach
- **CloudWatch Dashboard:** TODO (yes/no, dashboard name if applicable)
- **Nextflow Tower:** TODO (yes/no, run ID if applicable)
- **Manual Checks:** TODO (describe any manual monitoring performed)

---

## Results

### Performance Metrics
- **Total Runtime:** TODO minutes
- **Total Cost:** TODO USD (from Cost Explorer)
- **Cost per Sample:** TODO USD
- **Peak vCPUs Used:** TODO
- **Peak Memory Used:** TODO GB
- **Storage Throughput (Read):** TODO MB/s
- **Storage Throughput (Write):** TODO MB/s

### Job Execution Statistics
- **Total Jobs Submitted:** TODO
- **Jobs Succeeded:** TODO
- **Jobs Failed:** TODO
- **Jobs Retried:** TODO
- **Average Queue Wait Time:** TODO minutes
- **Spot Interruptions:** TODO (if using Spot instances)

### Data Volume
- **Input Data Size:** TODO GB
- **Intermediate Data Size:** TODO GB (work directory)
- **Output Data Size:** TODO GB
- **Total S3 Storage Used:** TODO GB

### Quality Metrics (if applicable)
- **Variants Called:** TODO (total count)
- **Ti/Tv Ratio:** TODO (transition/transversion ratio)
- **Concordance with Truth Set:** TODO % (if benchmark dataset)

---

## Cost Breakdown

<!-- Use AWS Cost Explorer to get detailed cost breakdown -->

| Cost Component | Amount (USD) | Notes |
|----------------|--------------|-------|
| EC2 Compute | TODO | |
| S3 Storage | TODO | |
| S3 Requests | TODO | |
| Data Transfer | TODO | |
| EFS/FSx | TODO | (if applicable) |
| CloudWatch | TODO | |
| Other | TODO | |
| **Total** | **TODO** | |

---

## Issues and Observations

### Issues Encountered
TODO: Describe any problems, errors, or unexpected behavior

**Issue 1:**  
- Description: TODO
- Resolution: TODO
- Impact on results: TODO

**Issue 2:**  
TODO: Add more as needed

### Noteworthy Observations
TODO: Any interesting findings, performance characteristics, or insights

---

## Reproducibility Checklist

- [ ] All configuration files committed to repository
- [ ] Sample sheet included or referenced
- [ ] Nextflow command documented
- [ ] AWS resource IDs recorded
- [ ] Environment variables documented
- [ ] Results CSV file completed and committed
- [ ] Cost data extracted from Cost Explorer
- [ ] CloudWatch metrics screenshots captured (optional)

---

## Comparison with Other Tests

TODO: Compare this test with similar tests varying one dimension

**Comparison Table:**

| Test ID | Storage | Compute | Samples | Runtime | Cost | Cost/Sample |
|---------|---------|---------|---------|---------|------|-------------|
| This test | TODO | TODO | TODO | TODO | TODO | TODO |
| test-XXX | TODO | TODO | TODO | TODO | TODO | TODO |
| test-YYY | TODO | TODO | TODO | TODO | TODO | TODO |

**Key Differences:**  
TODO: Explain what changed between tests and observed impact

---

## Conclusions and Recommendations

### Findings
TODO: Summarize key findings from this test

### Recommendations
TODO: Based on results, what would you recommend for this use case?

### Next Steps
TODO: What additional testing would be valuable?

---

## Appendix

### Configuration File Snapshots

TODO: Include relevant snippets from configuration files or reference committed files

### Log Excerpts

TODO: Include relevant log excerpts if they illustrate important points

### CloudWatch Queries

TODO: Document any CloudWatch Logs Insights queries used for analysis

### References

- nf-core/sarek documentation: https://nf-co.re/sarek
- AWS Batch documentation: https://docs.aws.amazon.com/batch/
- TODO: Add other relevant references
