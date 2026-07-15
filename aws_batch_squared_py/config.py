"""Configuration for the Nextflow-on-Batch CDK app.

Ported from the TypeScript `NextflowBatchConfig` interface. Values are loaded
from CDK context (`-c key=value` or cdk.json) with sensible defaults, then
validated before any stack is instantiated.
"""

from dataclasses import dataclass
from typing import List, Optional

from aws_cdk import App


# Default AMI: the ECS-optimized Amazon Linux 2 image, resolved at deploy time
# from its public SSM parameter.
DEFAULT_BATCH_COMPUTE_AMI = (
    "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
)


@dataclass
class NextflowBatchConfig:
    namespace: str
    group_name: str
    create_vpc: bool
    existing_bucket: bool
    build_nextflow_image: bool
    vpc_id: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    s3_bucket_name: Optional[str] = None
    existing_nextflow_image: Optional[str] = None
    batch_compute_ami: str = DEFAULT_BATCH_COMPUTE_AMI
    s3_reference_path: str = "reference"
    # Default min vCPUs to 0 so idle compute environments scale to zero and cost nothing.
    on_demand_min_cpus: int = 0
    on_demand_max_cpus: int = 500
    spot_min_cpus: int = 0
    spot_max_cpus: int = 500
    batch_on_demand_instance_types: str = "optimal"
    batch_spot_instance_types: str = "optimal"
    # Days after which Nextflow work-dir intermediates are expired from S3 (0 disables).
    # Only applies to a newly-created bucket, and only under the Nextflow work prefix.
    work_dir_expiration_days: int = 30

    @staticmethod
    def from_context(app: App) -> "NextflowBatchConfig":
        """Build config from CDK context, mirroring the TS ``tryGetContext`` logic."""
        node = app.node

        def ctx(key: str):
            return node.try_get_context(key)

        def ctx_or(key: str, default):
            # Mirrors TS `||` (falsy fallback): empty/None/0 all fall back.
            value = ctx(key)
            return value if value else default

        def ctx_default(key: str, default):
            # Mirrors TS `??` (nullish fallback): only None falls back.
            value = ctx(key)
            return default if value is None else value

        config = NextflowBatchConfig(
            namespace=ctx_or("namespace", "cdk-nfbatch-eu-west-2"),
            group_name=ctx_or("groupName", "cdk-new1"),
            create_vpc=ctx("createVpc") is True,
            vpc_id=ctx("vpcId"),
            subnet_ids=ctx("subnetIds"),
            s3_bucket_name=ctx("s3BucketName"),
            existing_bucket=ctx("existingBucket") is True,
            build_nextflow_image=ctx("buildNextflowImage") is True,
            existing_nextflow_image=ctx("existingNextflowImage"),
            batch_compute_ami=ctx_or("batchComputeAmi", DEFAULT_BATCH_COMPUTE_AMI),
            s3_reference_path=ctx_or("s3ReferencePath", "reference"),
            on_demand_min_cpus=ctx_default("onDemandMinCpus", 0),
            on_demand_max_cpus=ctx_or("onDemandMaxCpus", 500),
            spot_min_cpus=ctx_default("spotMinCpus", 0),
            spot_max_cpus=ctx_or("spotMaxCpus", 500),
            batch_on_demand_instance_types=ctx_or("batchOnDemandInstanceTypes", "optimal"),
            batch_spot_instance_types=ctx_or("batchSpotInstanceTypes", "optimal"),
            work_dir_expiration_days=ctx_default("workDirExpirationDays", 30),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.build_nextflow_image and not self.existing_nextflow_image:
            raise ValueError(
                "When buildNextflowImage is false, existingNextflowImage must be provided"
            )

        if not self.create_vpc and (
            not self.vpc_id or not self.subnet_ids or len(self.subnet_ids) == 0
        ):
            raise ValueError(
                "When createVpc is false, vpcId and subnetIds must be provided"
            )
