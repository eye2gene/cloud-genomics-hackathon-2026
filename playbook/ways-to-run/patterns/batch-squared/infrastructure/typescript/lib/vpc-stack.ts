import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import type { Construct } from "constructs";

export interface VpcStackProps extends cdk.NestedStackProps {
  namespace: string;
  createVpc: boolean;
  existingVpcId?: string;
  existingSubnetIds?: string[];
}

export class VpcStack extends cdk.NestedStack {
  public readonly vpc: ec2.IVpc;
  public readonly subnets: ec2.ISubnet[];

  constructor(scope: Construct, id: string, props: VpcStackProps) {
    super(scope, id, props);

    if (props.createVpc) {
      // Create new VPC
      const vpc = new ec2.Vpc(this, "VPC", {
        ipAddresses: ec2.IpAddresses.cidr("10.0.0.0/16"),
        maxAzs: 2,
        natGateways: 2,
        subnetConfiguration: [
          {
            cidrMask: 24,
            name: `${props.namespace}-public`,
            subnetType: ec2.SubnetType.PUBLIC,
          },
          {
            cidrMask: 24,
            name: `${props.namespace}-private`,
            subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          },
        ],
        enableDnsHostnames: true,
        enableDnsSupport: true,
      });

      cdk.Tags.of(vpc).add("Name", `${props.namespace}-vpc`);

      // S3 Gateway Endpoint — routes S3 traffic directly, bypassing NAT (free, no data charges)
      vpc.addGatewayEndpoint("S3Endpoint", {
        service: ec2.GatewayVpcEndpointAwsService.S3,
      });

      this.vpc = vpc;
      this.subnets = vpc.privateSubnets;
    } else {
      // Use existing VPC
      if (!props.existingVpcId || !props.existingSubnetIds) {
        throw new Error(
          "existingVpcId and existingSubnetIds are required when createVpc is false",
        );
      }

      this.vpc = ec2.Vpc.fromLookup(this, "ExistingVpc", {
        vpcId: props.existingVpcId,
      });

      this.subnets = props.existingSubnetIds.map((subnetId, index) =>
        ec2.Subnet.fromSubnetId(this, `ExistingSubnet${index}`, subnetId),
      );
    }

    // Outputs
    new cdk.CfnOutput(this, "VpcId", {
      value: this.vpc.vpcId,
    });

    new cdk.CfnOutput(this, "SubnetIds", {
      value: this.subnets.map((s) => s.subnetId).join(","),
    });
  }
}
