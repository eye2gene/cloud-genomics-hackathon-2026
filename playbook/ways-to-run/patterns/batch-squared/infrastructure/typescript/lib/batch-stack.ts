import * as cdk from "aws-cdk-lib";
import * as batch from "aws-cdk-lib/aws-batch";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import type * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import type { Construct } from "constructs";

export interface BatchStackProps extends cdk.NestedStackProps {
  namespace: string;
  vpc: ec2.IVpc;
  subnets: ec2.ISubnet[];
  launchTemplateId: string;
  batchServiceRole: iam.Role;
  instanceProfile: iam.InstanceProfile;
  spotFleetRole: iam.Role;
  onDemandMinCpus: number;
  onDemandMaxCpus: number;
  spotMinCpus: number;
  spotMaxCpus: number;
  batchOnDemandInstanceTypes: string;
  batchSpotInstanceTypes: string;
}

export class BatchStack extends cdk.NestedStack {
  public readonly onDemandQueueArn: string;
  public readonly spotQueueArn: string;
  public readonly securityGroup: ec2.SecurityGroup;
  public readonly genericJobDefinitionArn: string;

  constructor(scope: Construct, id: string, props: BatchStackProps) {
    super(scope, id, props);

    // Create Security Group
    this.securityGroup = new ec2.SecurityGroup(this, "SecurityGroup", {
      vpc: props.vpc,
      description: "SG for genomics workflows on Batch",
      allowAllOutbound: true,
    });

    // Allow all TCP traffic within the security group
    this.securityGroup.addIngressRule(
      this.securityGroup,
      ec2.Port.allTcp(),
      "Allow all TCP traffic within security group",
    );

    // Parse instance types
    const onDemandInstanceTypes =
      props.batchOnDemandInstanceTypes === "optimal"
        ? ["optimal"]
        : props.batchOnDemandInstanceTypes.split(",").map((t) => t.trim());

    const spotInstanceTypes =
      props.batchSpotInstanceTypes === "optimal"
        ? ["optimal"]
        : props.batchSpotInstanceTypes.split(",").map((t) => t.trim());

    // Create Spot Compute Environment using CfnComputeEnvironment for more control
    const spotComputeEnv = new batch.CfnComputeEnvironment(
      this,
      "SpotComputeEnv",
      {
        computeEnvironmentName: `spot-${props.namespace}-v4`,
        serviceRole: props.batchServiceRole.roleArn,
        type: "MANAGED",
        state: "ENABLED",
        computeResources: {
          type: "SPOT",
          // Optimizes for both price and interruption-resistance (vs plain capacity-optimized).
          allocationStrategy: "SPOT_PRICE_CAPACITY_OPTIMIZED",
          ec2Configuration: [
            {
              imageType: "ECS_AL2",
            },
          ],
          launchTemplate: {
            launchTemplateId: props.launchTemplateId,
            version: "$Latest",
          },
          instanceRole: props.instanceProfile.instanceProfileArn,
          instanceTypes: spotInstanceTypes,
          minvCpus: props.spotMinCpus,
          maxvCpus: props.spotMaxCpus,
          securityGroupIds: [this.securityGroup.securityGroupId],
          spotIamFleetRole: props.spotFleetRole.roleArn,
          subnets: props.subnets.map((s) => s.subnetId),
          tags: {
            Name: `${props.namespace}-compute-instance`,
          },
        },
      },
    );

    // Create On-Demand Compute Environment
    const onDemandComputeEnv = new batch.CfnComputeEnvironment(
      this,
      "OnDemandComputeEnv",
      {
        computeEnvironmentName: `ondemand-${props.namespace}-v4`,
        serviceRole: props.batchServiceRole.roleArn,
        type: "MANAGED",
        state: "ENABLED",
        computeResources: {
          type: "EC2",
          // Progressive fall-through to other instance types when the preferred type has no
          // capacity, instead of wedging jobs in RUNNABLE (the failure mode of plain BEST_FIT).
          allocationStrategy: "BEST_FIT_PROGRESSIVE",
          ec2Configuration: [
            {
              imageType: "ECS_AL2",
            },
          ],
          launchTemplate: {
            launchTemplateId: props.launchTemplateId,
            version: "$Latest",
          },
          instanceRole: props.instanceProfile.instanceProfileArn,
          instanceTypes: onDemandInstanceTypes,
          minvCpus: props.onDemandMinCpus,
          maxvCpus: props.onDemandMaxCpus,
          securityGroupIds: [this.securityGroup.securityGroupId],
          subnets: props.subnets.map((s) => s.subnetId),
          tags: {
            Name: `${props.namespace}-compute-instance`,
          },
        },
      },
    );

    // Create Job Queues
    const onDemandQueue = new batch.CfnJobQueue(this, "OnDemandQueue", {
      jobQueueName: `OnDemand-${props.namespace}`,
      priority: 1000,
      state: "ENABLED",
      computeEnvironmentOrder: [
        {
          order: 1,
          computeEnvironment: onDemandComputeEnv.ref,
        },
      ],
    });

    const spotQueue = new batch.CfnJobQueue(this, "SpotQueue", {
      jobQueueName: `Spot-${props.namespace}`,
      priority: 1,
      state: "ENABLED",
      computeEnvironmentOrder: [
        {
          order: 1,
          computeEnvironment: spotComputeEnv.ref,
        },
      ],
    });

    // Create CloudWatch Log Group
    new logs.LogGroup(this, "ContainerInstanceLogGroup", {
      logGroupName: `/aws/ecs/container-instance/${props.namespace}`,
      retention: logs.RetentionDays.ONE_WEEK,
    });

    // Create Generic Batch Job Definition
    const genericJobDef = new batch.CfnJobDefinition(
      this,
      "GenericBatchJobDefinition",
      {
        jobDefinitionName: `generic-batch-${props.namespace}`,
        type: "container",
        containerProperties: {
          image: "amazonlinux",
          vcpus: 4,
          memory: 16384,
          mountPoints: [
            {
              sourceVolume: "aws-cli",
              containerPath: "/opt/aws-cli",
              readOnly: true,
            },
          ],
          volumes: [
            {
              name: "aws-cli",
              host: {
                sourcePath: "/opt/aws-cli",
              },
            },
          ],
          environment: [
            {
              name: "PATH",
              value:
                "/opt/aws-cli/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            },
          ],
        },
      },
    );

    this.onDemandQueueArn = onDemandQueue.attrJobQueueArn;
    this.spotQueueArn = spotQueue.attrJobQueueArn;
    this.genericJobDefinitionArn = genericJobDef.ref;

    // Outputs
    new cdk.CfnOutput(this, "OnDemandJobQueueArn", {
      value: this.onDemandQueueArn,
    });

    new cdk.CfnOutput(this, "SpotJobQueueArn", {
      value: this.spotQueueArn,
    });

    new cdk.CfnOutput(this, "BatchSecurityGroupId", {
      value: this.securityGroup.securityGroupId,
      description: "The Batch Security Group",
    });

    new cdk.CfnOutput(this, "GenericJobDefinitionArn", {
      value: this.genericJobDefinitionArn,
      description: "Generic job definition for running any container",
    });
  }
}
