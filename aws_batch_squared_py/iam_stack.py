"""IAM nested stack — roles and instance profile for AWS Batch.

Ported from ``lib/iam-stack.ts``.
"""

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from constructs import Construct


class IamStack(cdk.NestedStack):
    batch_job_role: iam.Role
    batch_instance_role: iam.Role
    batch_instance_profile: iam.InstanceProfile
    batch_spot_fleet_role: iam.Role
    batch_service_role: iam.Role

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        s3_bucket_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        region = cdk.Stack.of(self).region

        # Batch Job Role
        self.batch_job_role = iam.Role(
            self,
            "BatchJobRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                f"S3Bucket-Access-{region}": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.DENY,
                            resources=[f"arn:aws:s3:::{s3_bucket_name}"],
                            actions=["s3:Delete*", "s3:PutBucket*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[f"arn:aws:s3:::{s3_bucket_name}"],
                            actions=["s3:ListBucket*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[f"arn:aws:s3:::{s3_bucket_name}/*"],
                            actions=["s3:*"],
                        ),
                    ]
                ),
            },
        )

        # Batch Instance Role
        self.batch_instance_role = iam.Role(
            self,
            "BatchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
            ],
            inline_policies={
                f"S3Bucket-Access-{region}": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            sid="S3BucketAllowAllObjectOps",
                            effect=iam.Effect.ALLOW,
                            resources=[
                                f"arn:aws:s3:::{s3_bucket_name}",
                                f"arn:aws:s3:::{s3_bucket_name}/*",
                            ],
                            actions=["s3:*"],
                        ),
                        iam.PolicyStatement(
                            sid="DenyDeleteBucket",
                            effect=iam.Effect.DENY,
                            resources=[f"arn:aws:s3:::{s3_bucket_name}"],
                            actions=["s3:DeleteBucket*", "s3:CreateBucket"],
                        ),
                    ]
                ),
            },
        )

        # Batch Instance Profile
        self.batch_instance_profile = iam.InstanceProfile(
            self,
            "BatchInstanceProfile",
            role=self.batch_instance_role,
        )

        # Batch Spot Fleet Role
        self.batch_spot_fleet_role = iam.Role(
            self,
            "BatchSpotFleetRole",
            assumed_by=iam.ServicePrincipal("spotfleet.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2SpotFleetTaggingRole"
                ),
            ],
        )

        # Batch Service Role
        self.batch_service_role = iam.Role(
            self,
            "BatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBatchServiceRole"
                ),
            ],
        )

        # Outputs
        cdk.CfnOutput(self, "BatchJobRoleArn", value=self.batch_job_role.role_arn)
        cdk.CfnOutput(
            self, "BatchServiceRoleArn", value=self.batch_service_role.role_arn
        )
        cdk.CfnOutput(
            self, "BatchSpotFleetRoleArn", value=self.batch_spot_fleet_role.role_arn
        )
        cdk.CfnOutput(
            self,
            "BatchInstanceProfileArn",
            value=self.batch_instance_profile.instance_profile_arn,
        )
