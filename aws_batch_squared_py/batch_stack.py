"""Batch nested stack — spot/on-demand compute environments, queues, job def.

Ported from ``lib/batch-stack.ts``. Uses the L1 ``Cfn*`` Batch constructs for
full control over allocation strategy and launch-template wiring.
"""

from typing import List

import aws_cdk as cdk
from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct


class BatchStack(cdk.NestedStack):
    on_demand_queue_arn: str
    spot_queue_arn: str
    security_group: ec2.SecurityGroup
    generic_job_definition_arn: str

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        vpc: ec2.IVpc,
        subnets: List[ec2.ISubnet],
        launch_template_id: str,
        batch_service_role: iam.Role,
        instance_profile: iam.InstanceProfile,
        spot_fleet_role: iam.Role,
        on_demand_min_cpus: int,
        on_demand_max_cpus: int,
        spot_min_cpus: int,
        spot_max_cpus: int,
        batch_on_demand_instance_types: str,
        batch_spot_instance_types: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Security Group
        self.security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            description="SG for genomics workflows on Batch",
            allow_all_outbound=True,
        )

        # Allow all TCP traffic within the security group
        self.security_group.add_ingress_rule(
            self.security_group,
            ec2.Port.all_tcp(),
            "Allow all TCP traffic within security group",
        )

        # Parse instance types
        on_demand_instance_types = (
            ["optimal"]
            if batch_on_demand_instance_types == "optimal"
            else [t.strip() for t in batch_on_demand_instance_types.split(",")]
        )
        spot_instance_types = (
            ["optimal"]
            if batch_spot_instance_types == "optimal"
            else [t.strip() for t in batch_spot_instance_types.split(",")]
        )

        # Create Spot Compute Environment using CfnComputeEnvironment for more control
        spot_compute_env = batch.CfnComputeEnvironment(
            self,
            "SpotComputeEnv",
            compute_environment_name=f"spot-{namespace}-v4",
            service_role=batch_service_role.role_arn,
            type="MANAGED",
            state="ENABLED",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="SPOT",
                # Optimizes for both price and interruption-resistance (vs plain
                # capacity-optimized).
                allocation_strategy="SPOT_PRICE_CAPACITY_OPTIMIZED",
                ec2_configuration=[
                    batch.CfnComputeEnvironment.Ec2ConfigurationObjectProperty(
                        image_type="ECS_AL2",
                    )
                ],
                launch_template=batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
                    launch_template_id=launch_template_id,
                    version="$Latest",
                ),
                instance_role=instance_profile.instance_profile_arn,
                instance_types=spot_instance_types,
                minv_cpus=spot_min_cpus,
                maxv_cpus=spot_max_cpus,
                security_group_ids=[self.security_group.security_group_id],
                spot_iam_fleet_role=spot_fleet_role.role_arn,
                subnets=[s.subnet_id for s in subnets],
                tags={"Name": f"{namespace}-compute-instance"},
            ),
        )

        # Create On-Demand Compute Environment
        on_demand_compute_env = batch.CfnComputeEnvironment(
            self,
            "OnDemandComputeEnv",
            compute_environment_name=f"ondemand-{namespace}-v4",
            service_role=batch_service_role.role_arn,
            type="MANAGED",
            state="ENABLED",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="EC2",
                # Progressive fall-through to other instance types when the preferred type
                # has no capacity, instead of wedging jobs in RUNNABLE (the failure mode of
                # plain BEST_FIT).
                allocation_strategy="BEST_FIT_PROGRESSIVE",
                ec2_configuration=[
                    batch.CfnComputeEnvironment.Ec2ConfigurationObjectProperty(
                        image_type="ECS_AL2",
                    )
                ],
                launch_template=batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
                    launch_template_id=launch_template_id,
                    version="$Latest",
                ),
                instance_role=instance_profile.instance_profile_arn,
                instance_types=on_demand_instance_types,
                minv_cpus=on_demand_min_cpus,
                maxv_cpus=on_demand_max_cpus,
                security_group_ids=[self.security_group.security_group_id],
                subnets=[s.subnet_id for s in subnets],
                tags={"Name": f"{namespace}-compute-instance"},
            ),
        )

        # Create Job Queues
        on_demand_queue = batch.CfnJobQueue(
            self,
            "OnDemandQueue",
            job_queue_name=f"OnDemand-{namespace}",
            priority=1000,
            state="ENABLED",
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=on_demand_compute_env.ref,
                )
            ],
        )

        spot_queue = batch.CfnJobQueue(
            self,
            "SpotQueue",
            job_queue_name=f"Spot-{namespace}",
            priority=1,
            state="ENABLED",
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=spot_compute_env.ref,
                )
            ],
        )

        # Create CloudWatch Log Group
        logs.LogGroup(
            self,
            "ContainerInstanceLogGroup",
            log_group_name=f"/aws/ecs/container-instance/{namespace}",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create Generic Batch Job Definition
        generic_job_def = batch.CfnJobDefinition(
            self,
            "GenericBatchJobDefinition",
            job_definition_name=f"generic-batch-{namespace}",
            type="container",
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                image="amazonlinux",
                vcpus=4,
                memory=16384,
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
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="PATH",
                        value=(
                            "/opt/aws-cli/bin:/usr/local/sbin:/usr/local/bin:"
                            "/usr/sbin:/usr/bin:/sbin:/bin"
                        ),
                    )
                ],
            ),
        )

        self.on_demand_queue_arn = on_demand_queue.attr_job_queue_arn
        self.spot_queue_arn = spot_queue.attr_job_queue_arn
        self.generic_job_definition_arn = generic_job_def.ref

        # Outputs
        cdk.CfnOutput(self, "OnDemandJobQueueArn", value=self.on_demand_queue_arn)
        cdk.CfnOutput(self, "SpotJobQueueArn", value=self.spot_queue_arn)
        cdk.CfnOutput(
            self,
            "BatchSecurityGroupId",
            value=self.security_group.security_group_id,
            description="The Batch Security Group",
        )
        cdk.CfnOutput(
            self,
            "GenericJobDefinitionArn",
            value=self.generic_job_definition_arn,
            description="Generic job definition for running any container",
        )
