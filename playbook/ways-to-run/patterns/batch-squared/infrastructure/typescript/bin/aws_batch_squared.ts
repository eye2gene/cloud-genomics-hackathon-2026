import * as cdk from 'aws-cdk-lib';
import { NextflowBatchStack } from '../lib/nextflow-batch-stack';

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

const app = new cdk.App();

// Load configuration from context or use defaults
const config: NextflowBatchConfig = {
  namespace: app.node.tryGetContext('namespace') || 'cdk-nfbatch-eu-west-2',
  groupName: app.node.tryGetContext('groupName') || 'cdk-new1',
  createVpc: app.node.tryGetContext('createVpc') === true,
  vpcId: app.node.tryGetContext('vpcId'),
  subnetIds: app.node.tryGetContext('subnetIds'),
  s3BucketName: app.node.tryGetContext('s3BucketName'),
  existingBucket: app.node.tryGetContext('existingBucket') === true,
  buildNextflowImage: app.node.tryGetContext('buildNextflowImage') === true,
  existingNextflowImage: app.node.tryGetContext('existingNextflowImage'),
  batchComputeAmi: app.node.tryGetContext('batchComputeAmi') || '/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id',
  s3ReferencePath: app.node.tryGetContext('s3ReferencePath') || 'reference',
  // Default min vCPUs to 0 so idle compute environments scale to zero and cost nothing.
  onDemandMinCpus: app.node.tryGetContext('onDemandMinCpus') ?? 0,
  onDemandMaxCpus: app.node.tryGetContext('onDemandMaxCpus') || 500,
  spotMinCpus: app.node.tryGetContext('spotMinCpus') ?? 0,
  spotMaxCpus: app.node.tryGetContext('spotMaxCpus') || 500,
  batchOnDemandInstanceTypes: app.node.tryGetContext('batchOnDemandInstanceTypes') || 'c5,c5a,c5d,c6i,c6a,m5,m5a,m5d,m6i,m6a,r5,r5a,r5d,r6i,r6a',
  batchSpotInstanceTypes: app.node.tryGetContext('batchSpotInstanceTypes') || 'c5,c5a,c5d,c6i,c6a,m5,m5a,m5d,m6i,m6a,r5,r5a,r5d,r6i,r6a',
  // Days after which Nextflow work-dir intermediates are expired from S3 (0 disables).
  // Only applies to a newly-created bucket, and only under the Nextflow work prefix.
  workDirExpirationDays: app.node.tryGetContext('workDirExpirationDays') ?? 30,
};

// Validation
if (!config.buildNextflowImage && !config.existingNextflowImage) {
  throw new Error('When buildNextflowImage is false, existingNextflowImage must be provided');
}

if (!config.createVpc && (!config.vpcId || !config.subnetIds || config.subnetIds.length === 0)) {
  throw new Error('When createVpc is false, vpcId and subnetIds must be provided');
}

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'eu-west-2',
};

// Create the main stack that orchestrates all nested stacks
// Stack name includes groupName so multiple users can deploy independently in the same account
const stackName = `NextflowBatchStack-${config.groupName}`;
new NextflowBatchStack(app, stackName, {
  config,
  env,
  description: 'Deploys a base genomics workflow architecture for Nextflow on AWS Batch',
});