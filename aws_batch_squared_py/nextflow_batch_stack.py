"""Top-level orchestration stack.

Ported from ``lib/nextflow-batch-stack.ts``. Wires all nested stacks together,
publishes queue/bucket references to SSM (so the Nextflow head-node role can
resolve them at deploy time), and declares cross-stack dependencies.
"""

import aws_cdk as cdk
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import NextflowBatchConfig
from .batch_stack import BatchStack
from .iam_stack import IamStack
from .launch_template_stack import LaunchTemplateStack
from .nextflow_ecr_stack import NextflowEcrStack
from .nextflow_stack import NextflowStack
from .s3_stack import S3Stack
from .vpc_stack import VpcStack


class NextflowBatchStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: NextflowBatchConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC Stack (or use existing)
        vpc_stack = VpcStack(
            self,
            "VpcStack",
            namespace=config.namespace,
            create_vpc=config.create_vpc,
            existing_vpc_id=config.vpc_id,
            existing_subnet_ids=config.subnet_ids,
        )

        # Create S3 Stack
        s3_stack = S3Stack(
            self,
            "S3Stack",
            namespace=config.namespace,
            group_name=config.group_name,
            bucket_name=config.s3_bucket_name,
            existing_bucket=config.existing_bucket,
            work_dir_expiration_days=config.work_dir_expiration_days,
        )

        # Create IAM Stack
        iam_stack = IamStack(
            self,
            "IamStack",
            s3_bucket_name=s3_stack.bucket_name,
        )
        iam_stack.add_dependency(s3_stack)

        # Create Launch Template Stack
        launch_template_stack = LaunchTemplateStack(
            self,
            "LaunchTemplateStack",
            namespace=config.namespace,
            group_name=config.group_name,
            batch_compute_ami=config.batch_compute_ami,
            s3_bucket_name=s3_stack.bucket_name,
            s3_reference_path=config.s3_reference_path,
        )

        # Create Batch Stack
        batch_stack = BatchStack(
            self,
            "BatchStack",
            namespace=config.namespace,
            vpc=vpc_stack.vpc,
            subnets=vpc_stack.subnets,
            launch_template_id=launch_template_stack.launch_template_id,
            batch_service_role=iam_stack.batch_service_role,
            instance_profile=iam_stack.batch_instance_profile,
            spot_fleet_role=iam_stack.batch_spot_fleet_role,
            on_demand_min_cpus=config.on_demand_min_cpus,
            on_demand_max_cpus=config.on_demand_max_cpus,
            spot_min_cpus=config.spot_min_cpus,
            spot_max_cpus=config.spot_max_cpus,
            batch_on_demand_instance_types=config.batch_on_demand_instance_types,
            batch_spot_instance_types=config.batch_spot_instance_types,
        )
        batch_stack.add_dependency(iam_stack)
        batch_stack.add_dependency(launch_template_stack)
        batch_stack.add_dependency(vpc_stack)

        # Build Nextflow image if needed
        if config.build_nextflow_image:
            nextflow_ecr_stack = NextflowEcrStack(
                self,
                "NextflowEcrStack",
                namespace=config.namespace,
            )
            nextflow_image_uri = nextflow_ecr_stack.image_uri
        else:
            if not config.existing_nextflow_image:
                raise ValueError(
                    "existingNextflowImage must be provided when buildNextflowImage is false"
                )
            nextflow_image_uri = config.existing_nextflow_image

        # Create SSM Parameters
        s3_bucket_param = ssm.StringParameter(
            self,
            "ParamS3Bucket",
            parameter_name=f"/{config.group_name}/{config.namespace}/s3-bucket",
            string_value=s3_stack.bucket_name,
            description="S3 Bucket",
        )

        on_demand_queue_param = ssm.StringParameter(
            self,
            "ParamOnDemandJobQueue",
            parameter_name=f"/{config.group_name}/{config.namespace}/job-queue/on-demand",
            string_value=batch_stack.on_demand_queue_arn,
            description="On-Demand AWS Batch Job Queue",
        )

        spot_queue_param = ssm.StringParameter(
            self,
            "ParamSpotJobQueue",
            parameter_name=f"/{config.group_name}/{config.namespace}/job-queue/spot",
            string_value=batch_stack.spot_queue_arn,
            description="Spot AWS Batch Job Queue",
        )

        # Create Nextflow Stack
        nextflow_stack = NextflowStack(
            self,
            "NextflowStack",
            namespace=config.namespace,
            group_name=config.group_name,
            nextflow_image=nextflow_image_uri,
            s3_bucket_param=s3_bucket_param.parameter_name,
            on_demand_queue_param=on_demand_queue_param.parameter_name,
            spot_queue_param=spot_queue_param.parameter_name,
        )
        nextflow_stack.add_dependency(batch_stack)
        nextflow_stack.node.add_dependency(s3_bucket_param)
        nextflow_stack.node.add_dependency(on_demand_queue_param)
        nextflow_stack.node.add_dependency(spot_queue_param)

        # Outputs
        cdk.CfnOutput(self, "S3BucketName", value=s3_stack.bucket_name)
        cdk.CfnOutput(self, "BatchJobRoleArn", value=iam_stack.batch_job_role.role_arn)
        cdk.CfnOutput(
            self, "OnDemandJobQueueArn", value=batch_stack.on_demand_queue_arn
        )
        cdk.CfnOutput(self, "SpotJobQueueArn", value=batch_stack.spot_queue_arn)
