"""Nextflow nested stack — head-node job role and job definition.

Ported from ``lib/nextflow-stack.ts``. The IAM policies and container env vars
reference SSM parameters via CloudFormation ``{{resolve:ssm:...}}`` dynamic
references so queue ARNs and the bucket name are wired at deploy time.
"""

from typing import Optional

import aws_cdk as cdk
from aws_cdk import aws_batch as batch
from aws_cdk import aws_iam as iam
from constructs import Construct


class NextflowStack(cdk.NestedStack):
    nextflow_job_role: iam.Role
    nextflow_job_definition: batch.CfnJobDefinition

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        group_name: str,
        nextflow_image: str,
        s3_bucket_param: str,
        on_demand_queue_param: str,
        spot_queue_param: str,
        s3_nextflow_prefix: Optional[str] = None,
        s3_logs_dir_prefix: Optional[str] = None,
        s3_work_dir_prefix: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account = cdk.Stack.of(self).account
        region = cdk.Stack.of(self).region

        s3_nextflow_prefix = s3_nextflow_prefix or "_nextflow"
        s3_logs_dir_prefix = s3_logs_dir_prefix or "logs"
        s3_work_dir_prefix = s3_work_dir_prefix or "runs"

        # Create Nextflow Job Role
        self.nextflow_job_role = iam.Role(
            self,
            "IAMNextflowJobRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
            ],
            inline_policies={
                f"Nextflow-Batch-Access-{region}": iam.PolicyDocument(
                    statements=[
                        # Batch read access
                        iam.PolicyStatement(
                            sid="BatchReadAccessAllowAll",
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                            actions=["batch:List*", "batch:Describe*"],
                        ),
                        # Batch tagging permissions
                        iam.PolicyStatement(
                            sid="BatchTagAccess",
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                            actions=[
                                "batch:TagResource",
                                "batch:ListTagsForResource",
                                "batch:UntagResource",
                            ],
                        ),
                        # CloudWatch logs read access
                        iam.PolicyStatement(
                            sid="CloudwatchReadLogEvents",
                            effect=iam.Effect.ALLOW,
                            resources=[
                                f"arn:aws:logs:{region}:{account}:log-group:"
                                "/aws/batch/job:log-stream:*"
                            ],
                            actions=["logs:GetLogEvents"],
                        ),
                        # Batch job submission
                        iam.PolicyStatement(
                            sid="BatchWriteAccessAllowJobSubmission",
                            effect=iam.Effect.ALLOW,
                            resources=[
                                f"{{{{resolve:ssm:{on_demand_queue_param}:1}}}}",
                                f"{{{{resolve:ssm:{spot_queue_param}:1}}}}",
                                "arn:aws:batch:*:*:job-definition/nf-*:*",
                            ],
                            actions=["batch:*Job"],
                        ),
                        # Batch job definition management
                        iam.PolicyStatement(
                            sid="BatchWriteAccessAllowJobDefinition",
                            effect=iam.Effect.ALLOW,
                            resources=[
                                "arn:aws:batch:*:*:job-definition/nf-*",
                                "arn:aws:batch:*:*:job-definition/nf-*:*",
                            ],
                            actions=["batch:*JobDefinition"],
                        ),
                    ]
                ),
                f"Nextflow-S3Bucket-Access-{region}": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[
                                f"arn:aws:s3:::{{{{resolve:ssm:{s3_bucket_param}:1}}}}",
                                f"arn:aws:s3:::{{{{resolve:ssm:{s3_bucket_param}:1}}}}/*",
                            ],
                            actions=["s3:*"],
                        ),
                    ]
                ),
                f"Nextflow-Instance-Access-{region}": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ecs:DescribeTasks",
                                "ec2:DescribeInstances",
                                "ec2:DescribeInstanceTypes",
                                "ec2:DescribeInstanceAttribute",
                                "ecs:DescribeContainerInstances",
                                "ec2:DescribeInstanceStatus",
                            ],
                            resources=["*"],
                        ),
                    ]
                ),
            },
        )

        # Create Nextflow Job Definition
        self.nextflow_job_definition = batch.CfnJobDefinition(
            self,
            "BatchNextflowJobDefinition",
            job_definition_name=f"nextflow-{namespace}",
            type="container",
            timeout=batch.CfnJobDefinition.TimeoutProperty(
                attempt_duration_seconds=3600,
            ),
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                memory=16384,
                vcpus=4,
                image=nextflow_image,
                job_role_arn=self.nextflow_job_role.role_arn,
                mount_points=[
                    batch.CfnJobDefinition.MountPointsProperty(
                        source_volume="aws-cli",
                        container_path="/opt/aws-cli",
                        read_only=True,
                    )
                ],
                volumes=[
                    batch.CfnJobDefinition.VolumesProperty(
                        name="aws-cli",
                        host=batch.CfnJobDefinition.VolumesHostProperty(
                            source_path="/opt/aws-cli",
                        ),
                    )
                ],
                environment=[
                    # Work (child) jobs default to the Spot queue for cost savings; they are
                    # retriable so Spot interruptions are tolerable. The head node itself still
                    # runs on the On-Demand queue (that's the queue you submit this job to).
                    # Override per-run by setting NF_JOB_QUEUE in the submit-job container env.
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="NF_JOB_QUEUE",
                        value=f"{{{{resolve:ssm:{spot_queue_param}:1}}}}",
                    ),
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="NF_LOGSDIR",
                        value=(
                            f"s3://{{{{resolve:ssm:{s3_bucket_param}:1}}}}/"
                            f"{s3_nextflow_prefix}/{s3_logs_dir_prefix}"
                        ),
                    ),
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="NF_WORKDIR",
                        value=(
                            f"s3://{{{{resolve:ssm:{s3_bucket_param}:1}}}}/"
                            f"{s3_nextflow_prefix}/{s3_work_dir_prefix}"
                        ),
                    ),
                ],
            ),
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "NextflowBucket",
            value=f"s3://{{{{resolve:ssm:{s3_bucket_param}:1}}}}",
            description=(
                "S3 Bucket used to store Nextflow metadata (session cache, logs, and "
                "intermediate results)"
            ),
        )
        cdk.CfnOutput(
            self,
            "LogsDir",
            value=(
                f"s3://{{{{resolve:ssm:{s3_bucket_param}:1}}}}/"
                f"{s3_nextflow_prefix}/{s3_logs_dir_prefix}"
            ),
            description="S3 URI where nextflow session cache and logs are stored",
        )
        cdk.CfnOutput(
            self,
            "WorkDir",
            value=(
                f"s3://{{{{resolve:ssm:{s3_bucket_param}:1}}}}/"
                f"{s3_nextflow_prefix}/{s3_work_dir_prefix}"
            ),
            description="S3 URI where workflow intermediate results are stored",
        )
        cdk.CfnOutput(
            self,
            "NextflowJobDefinition",
            value=self.nextflow_job_definition.ref,
            description=(
                "Batch Job Definition that creates a nextflow head node for running "
                "workflows"
            ),
        )
        cdk.CfnOutput(
            self,
            "NextflowJobRole",
            value=self.nextflow_job_role.role_arn,
            description=(
                "IAM Role that allows the nextflow head node job access to S3 and Batch"
            ),
        )
