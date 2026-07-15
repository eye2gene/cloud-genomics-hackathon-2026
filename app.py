#!/usr/bin/env python3
"""CDK app entry point for Nextflow on AWS Batch.

Ported from ``bin/aws_batch_squared.ts``. Loads configuration from context,
validates it, and instantiates the top-level orchestration stack.
"""
import os

import aws_cdk as cdk

from aws_batch_squared_py.config import NextflowBatchConfig
from aws_batch_squared_py.nextflow_batch_stack import NextflowBatchStack


app = cdk.App()

# Load configuration from context or use defaults (validation runs inside).
config = NextflowBatchConfig.from_context(app)

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION") or "eu-west-2",
)

# Create the main stack that orchestrates all nested stacks.
NextflowBatchStack(
    app,
    "NextflowBatchStack",
    config=config,
    env=env,
    description="Deploys a base genomics workflow architecture for Nextflow on AWS Batch",
)

app.synth()
