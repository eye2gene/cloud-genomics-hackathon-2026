#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Afonso's 1-sample sarek benchmark (uk35C650)
# ============================================================
# Unique identifiers so we don't collide with others in the shared account
NAMESPACE="afonso-nfbatch"
GROUP_NAME="afonso"
REGION="eu-west-2"

# --- Step 1: Deploy infrastructure (skip if already deployed) -----------

CDK_DIR="$(dirname "$0")/../../ways-to-run/patterns/batch-squared/infrastructure/typescript"

echo "=== Step 1: Deploy infrastructure ==="
echo "CDK directory: $CDK_DIR"

pushd "$CDK_DIR" > /dev/null

# Install dependencies
bun install

# Bootstrap CDK (idempotent - safe to re-run)
bunx aws-cdk bootstrap --region "$REGION"

# Deploy the stack with unique names
bunx aws-cdk deploy \
  -c namespace="$NAMESPACE" \
  -c groupName="$GROUP_NAME" \
  -c createVpc=true \
  -c existingBucket=false \
  -c buildNextflowImage=true \
  --require-approval never

popd > /dev/null

# --- Step 2: Get the bucket name from CloudFormation outputs -----------

echo ""
echo "=== Step 2: Resolve bucket name ==="

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="${GROUP_NAME}-${NAMESPACE}-${ACCOUNT_ID}"

echo "Bucket: $BUCKET"

# --- Step 3: Upload sample sheet ---------------------------------------

echo ""
echo "=== Step 3: Upload sample sheet ==="

SAMPLESHEET="$(dirname "$0")/../sample-sheets/pgp10-fastqs-1sample.csv"

aws s3 cp "$SAMPLESHEET" "s3://${BUCKET}/benchmarks/samplesheets/wgs_n1.csv"

echo "Uploaded to s3://${BUCKET}/benchmarks/samplesheets/wgs_n1.csv"

# --- Step 4: Submit the pipeline run -----------------------------------

echo ""
echo "=== Step 4: Submit sarek run ==="

JOB_ID=$(aws batch submit-job \
  --job-name "afonso-sarek-n1" \
  --job-queue "OnDemand-${NAMESPACE}" \
  --job-definition "nextflow-${NAMESPACE}" \
  --container-overrides '{
    "command": [
      "nf-core/sarek",
      "-r", "3.9.0",
      "--input",  "s3://'"${BUCKET}"'/benchmarks/samplesheets/wgs_n1.csv",
      "--outdir", "s3://'"${BUCKET}"'/benchmarks/results/n1/",
      "--genome", "GATK.GRCh38",
      "--tools",  "haplotypecaller",
      "-with-report",
      "-with-timeline"
    ]
  }' \
  --query 'jobId' --output text)

echo ""
echo "=== Done! ==="
echo "Job submitted: $JOB_ID"
echo ""
echo "Monitor with:"
echo "  aws batch describe-jobs --jobs $JOB_ID --query 'jobs[0].status'"
echo ""
echo "Results will land at:"
echo "  s3://${BUCKET}/benchmarks/results/n1/"
