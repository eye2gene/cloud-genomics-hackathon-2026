"""VPC nested stack — creates a new VPC or imports an existing one.

Ported from ``lib/vpc-stack.ts``.
"""

from typing import List, Optional

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VpcStack(cdk.NestedStack):
    vpc: ec2.IVpc
    subnets: List[ec2.ISubnet]

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        create_vpc: bool,
        existing_vpc_id: Optional[str] = None,
        existing_subnet_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if create_vpc:
            # Create new VPC
            vpc = ec2.Vpc(
                self,
                "VPC",
                ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                max_azs=2,
                nat_gateways=2,
                subnet_configuration=[
                    ec2.SubnetConfiguration(
                        cidr_mask=24,
                        name=f"{namespace}-public",
                        subnet_type=ec2.SubnetType.PUBLIC,
                    ),
                    ec2.SubnetConfiguration(
                        cidr_mask=24,
                        name=f"{namespace}-private",
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    ),
                ],
                enable_dns_hostnames=True,
                enable_dns_support=True,
            )

            cdk.Tags.of(vpc).add("Name", f"{namespace}-vpc")

            self.vpc = vpc
            self.subnets = vpc.private_subnets
        else:
            # Use existing VPC
            if not existing_vpc_id or not existing_subnet_ids:
                raise ValueError(
                    "existingVpcId and existingSubnetIds are required when createVpc is false"
                )

            self.vpc = ec2.Vpc.from_lookup(self, "ExistingVpc", vpc_id=existing_vpc_id)

            self.subnets = [
                ec2.Subnet.from_subnet_id(self, f"ExistingSubnet{index}", subnet_id)
                for index, subnet_id in enumerate(existing_subnet_ids)
            ]

        # Outputs
        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        cdk.CfnOutput(
            self,
            "SubnetIds",
            value=",".join(s.subnet_id for s in self.subnets),
        )
