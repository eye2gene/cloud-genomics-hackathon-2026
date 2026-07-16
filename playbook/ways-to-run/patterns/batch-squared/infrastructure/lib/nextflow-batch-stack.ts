import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';
import { VpcStack } from './vpc-stack';
import { S3Stack } from './s3-stack';
import { IamStack } from './iam-stack';
import { LaunchTemplateStack } from './launch-template-stack';
import { BatchStack } from './batch-stack';
import { NextflowStack } from './nextflow-stack';
import { NextflowEcrStack } from './nextflow-ecr-stack';

export interface NextflowBatchConfig {
  namespace: string;
  groupName: string;
  createVpc: boolean;
  vpcId?: string;
  subnetIds?: string[];
  s3BucketName?: string;
  existingBucket: boolean;
  buildNextflowImage: boolean;
  existingNextflowImage?: string;
  batchComputeAmi?: string;
  s3ReferencePath?: string;
  onDemandMinCpus?: number;
  onDemandMaxCpus?: number;
  spotMinCpus?: number;
  spotMaxCpus?: number;
  batchOnDemandInstanceTypes?: string;
  batchSpotInstanceTypes?: string;
  workDirExpirationDays?: number;
}

export interface NextflowBatchStackProps extends cdk.StackProps {
  config: NextflowBatchConfig;
}

export class NextflowBatchStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: NextflowBatchStackProps) {
    super(scope, id, props);

    const { config } = props;

    // Create VPC Stack (or use existing)
    const vpcStack = new VpcStack(this, 'VpcStack', {
      namespace: config.namespace,
      createVpc: config.createVpc,
      existingVpcId: config.vpcId,
      existingSubnetIds: config.subnetIds,
    });

    // Create S3 Stack
    const s3Stack = new S3Stack(this, 'S3Stack', {
      namespace: config.namespace,
      groupName: config.groupName,
      bucketName: config.s3BucketName,
      existingBucket: config.existingBucket,
      workDirExpirationDays: config.workDirExpirationDays,
    });

    // Create IAM Stack
    const iamStack = new IamStack(this, 'IamStack', {
      s3BucketName: s3Stack.bucketName,
    });
    iamStack.addDependency(s3Stack);

    // Create Launch Template Stack
    const launchTemplateStack = new LaunchTemplateStack(this, 'LaunchTemplateStack', {
      namespace: config.namespace,
      groupName: config.groupName,
      batchComputeAmi: config.batchComputeAmi!,
      s3BucketName: s3Stack.bucketName,
      s3ReferencePath: config.s3ReferencePath!,
    });

    // Create Batch Stack
    const batchStack = new BatchStack(this, 'BatchStack', {
      namespace: config.namespace,
      vpc: vpcStack.vpc,
      subnets: vpcStack.subnets,
      launchTemplateId: launchTemplateStack.launchTemplateId,
      batchServiceRole: iamStack.batchServiceRole,
      instanceProfile: iamStack.batchInstanceProfile,
      spotFleetRole: iamStack.batchSpotFleetRole,
      onDemandMinCpus: config.onDemandMinCpus!,
      onDemandMaxCpus: config.onDemandMaxCpus!,
      spotMinCpus: config.spotMinCpus!,
      spotMaxCpus: config.spotMaxCpus!,
      batchOnDemandInstanceTypes: config.batchOnDemandInstanceTypes!,
      batchSpotInstanceTypes: config.batchSpotInstanceTypes!,
    });
    batchStack.addDependency(iamStack);
    batchStack.addDependency(launchTemplateStack);
    batchStack.addDependency(vpcStack);

    // Build Nextflow image if needed
    let nextflowImageUri: string;
    if (config.buildNextflowImage) {
      const nextflowEcrStack = new NextflowEcrStack(this, 'NextflowEcrStack', {
        namespace: config.namespace,
      });
      nextflowImageUri = nextflowEcrStack.imageUri;
    } else {
      if (!config.existingNextflowImage) {
        throw new Error('existingNextflowImage must be provided when buildNextflowImage is false');
      }
      nextflowImageUri = config.existingNextflowImage;
    }

    // Create SSM Parameters
    const s3BucketParam = new ssm.StringParameter(this, 'ParamS3Bucket', {
      parameterName: `/${config.groupName}/${config.namespace}/s3-bucket`,
      stringValue: s3Stack.bucketName,
      description: 'S3 Bucket',
    });

    const onDemandQueueParam = new ssm.StringParameter(this, 'ParamOnDemandJobQueue', {
      parameterName: `/${config.groupName}/${config.namespace}/job-queue/on-demand`,
      stringValue: batchStack.onDemandQueueArn,
      description: 'On-Demand AWS Batch Job Queue',
    });

    const spotQueueParam = new ssm.StringParameter(this, 'ParamSpotJobQueue', {
      parameterName: `/${config.groupName}/${config.namespace}/job-queue/spot`,
      stringValue: batchStack.spotQueueArn,
      description: 'Spot AWS Batch Job Queue',
    });

    // Create Nextflow Stack
    const nextflowStack = new NextflowStack(this, 'NextflowStack', {
      namespace: config.namespace,
      groupName: config.groupName,
      nextflowImage: nextflowImageUri,
      s3BucketParam: s3BucketParam.parameterName,
      onDemandQueueParam: onDemandQueueParam.parameterName,
      spotQueueParam: spotQueueParam.parameterName,
    });
    nextflowStack.addDependency(batchStack);
    nextflowStack.node.addDependency(s3BucketParam);
    nextflowStack.node.addDependency(onDemandQueueParam);
    nextflowStack.node.addDependency(spotQueueParam);

    // Outputs
    new cdk.CfnOutput(this, 'S3BucketName', {
      value: s3Stack.bucketName,
    });

    new cdk.CfnOutput(this, 'BatchJobRoleArn', {
      value: iamStack.batchJobRole.roleArn,
    });

    new cdk.CfnOutput(this, 'OnDemandJobQueueArn', {
      value: batchStack.onDemandQueueArn,
    });

    new cdk.CfnOutput(this, 'SpotJobQueueArn', {
      value: batchStack.spotQueueArn,
    });
  }
}