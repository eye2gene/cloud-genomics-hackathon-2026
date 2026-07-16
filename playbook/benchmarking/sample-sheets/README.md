# Sample Sheets for Benchmarking

This directory contains pre-configured sample sheets for nf-core/sarek at various scales.

## Available Sample Sheets

### 1000 Genomes Project

- **1000genomes-1sample.csv** - Single sample for quick testing (HG00096)
- **1000genomes-5samples.csv** - 5 samples for small-scale benchmarking
- **1000genomes-10samples.csv** - TODO: Add 10 samples
- **1000genomes-50samples.csv** - TODO: Add 50 samples
- **1000genomes-100samples.csv** - TODO: Add 100 samples

### PGP-UK Samples

- **pgpuk-1sample.csv** - TODO: Add single PGP-UK sample
- **pgpuk-10samples.csv** - TODO: Add 10 PGP-UK samples

## Data Source

Data is available via the [AWS Registry of Open Data](https://registry.opendata.aws/) (RODA). Free to access.

There is an [MCP server for RODA](https://aws.amazon.com/blogs/opensource/introducing-mcp-server-for-registry-of-open-data-on-aws/) that you can use with Kiro to discover datasets, preview bucket structures, and sample files.

**Add to Kiro** (`~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "awslabs.roda-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.roda-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Sample Sheet Format

Sample sheets follow the nf-core/sarek CSV format:

```csv
patient,sample,lane,fastq_1,fastq_2
<patient_id>,<sample_id>,<lane>,<s3://path/to/R1.fq.gz>,<s3://path/to/R2.fq.gz>
```

## Creating Your Own Sample Sheets

Use the [AWS Open Data Registry](https://registry.opendata.aws/) to find public genomics datasets. The AWS Open Data MCP is available in Kiro - ask it to find relevant datasets and generate sample sheets for you.

Example Kiro prompt: "Find WGS datasets from the 1000 genomes data on AWS Open Data and generate a 10-sample samplesheet in nf-core/sarek format."

**Column descriptions:**
- `patient`: Unique patient identifier
- `sample`: Sample identifier (can be same as patient for single-sample patients)
- `lane`: Sequencing lane (use 1 if unknown)
- `fastq_1`: S3 path to forward read FASTQ file
- `fastq_2`: S3 path to reverse read FASTQ file

## Creating Custom Sample Sheets

1. Browse available samples in the 1000 Genomes S3 bucket
2. Copy this template and add your sample rows
3. Ensure S3 paths are accessible from your AWS account
4. Validate format before running pipeline

## Testing Before Benchmarking

Always test with a single sample first:
```bash
nextflow run nf-core/sarek \
  -profile awsbatch \
  --input sample-sheets/1000genomes-1sample.csv \
  --outdir s3://your-bucket/test-run/
```

## Coverage Information

The 1000 Genomes DRAGEN samples are sequenced at approximately 30x coverage.

**Expected file sizes (per sample):**
- FASTQ R1: ~15-20 GB
- FASTQ R2: ~15-20 GB
- Total input per sample: ~30-40 GB


