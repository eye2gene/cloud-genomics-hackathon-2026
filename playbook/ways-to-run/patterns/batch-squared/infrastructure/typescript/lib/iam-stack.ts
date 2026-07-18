import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";

export interface IamStackProps extends cdk.NestedStackProps {
  s3BucketName: string;
}

export class IamStack extends cdk.NestedStack {
  public readonly batchJobRole: iam.Role;
  public readonly batchInstanceRole: iam.Role;
  public readonly batchInstanceProfile: iam.InstanceProfile;
  public readonly batchSpotFleetRole: iam.Role;
  public readonly batchServiceRole: iam.Role;

  constructor(scope: Construct, id: string, props: IamStackProps) {
    super(scope, id, props);

    const region = cdk.Stack.of(this).region;

    // Batch Job Role
    this.batchJobRole = new iam.Role(this, "BatchJobRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      inlinePolicies: {
        [`S3Bucket-Access-${region}`]: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.DENY,
              resources: [`arn:aws:s3:::${props.s3BucketName}`],
              actions: ["s3:Delete*", "s3:PutBucket*"],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              resources: [`arn:aws:s3:::${props.s3BucketName}`],
              actions: ["s3:ListBucket*"],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              resources: [`arn:aws:s3:::${props.s3BucketName}/*`],
              actions: ["s3:*"],
            }),
          ],
        }),
        // Read access to public data buckets used by nf-core pipelines
        "PublicDataBuckets-ReadOnly": new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: "AllowListPublicDataBuckets",
              effect: iam.Effect.ALLOW,
              resources: [
                "arn:aws:s3:::pgp10-fastqs",
                "arn:aws:s3:::ngi-igenomes",
                "arn:aws:s3:::1000genomes",
              ],
              actions: ["s3:ListBucket*"],
            }),
            new iam.PolicyStatement({
              sid: "AllowGetPublicDataObjects",
              effect: iam.Effect.ALLOW,
              resources: [
                "arn:aws:s3:::pgp10-fastqs/*",
                "arn:aws:s3:::ngi-igenomes/*",
                "arn:aws:s3:::1000genomes/*",
              ],
              actions: ["s3:GetObject", "s3:GetObjectVersion"],
            }),
          ],
        }),
      },
    });

    // Batch Instance Role
    this.batchInstanceRole = new iam.Role(this, "BatchInstanceRole", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AmazonEC2ContainerServiceforEC2Role",
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonS3ReadOnlyAccess"),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "AmazonSSMManagedInstanceCore",
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "CloudWatchAgentServerPolicy",
        ),
      ],
      inlinePolicies: {
        [`S3Bucket-Access-${region}`]: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: "S3BucketAllowAllObjectOps",
              effect: iam.Effect.ALLOW,
              resources: [
                `arn:aws:s3:::${props.s3BucketName}`,
                `arn:aws:s3:::${props.s3BucketName}/*`,
              ],
              actions: ["s3:*"],
            }),
            new iam.PolicyStatement({
              sid: "DenyDeleteBucket",
              effect: iam.Effect.DENY,
              resources: [`arn:aws:s3:::${props.s3BucketName}`],
              actions: ["s3:DeleteBucket*", "s3:CreateBucket"],
            }),
          ],
        }),
      },
    });

    // Batch Instance Profile
    this.batchInstanceProfile = new iam.InstanceProfile(
      this,
      "BatchInstanceProfile",
      {
        role: this.batchInstanceRole,
      },
    );

    // Batch Spot Fleet Role
    this.batchSpotFleetRole = new iam.Role(this, "BatchSpotFleetRole", {
      assumedBy: new iam.ServicePrincipal("spotfleet.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AmazonEC2SpotFleetTaggingRole",
        ),
      ],
    });

    // Batch Service Role
    this.batchServiceRole = new iam.Role(this, "BatchServiceRole", {
      assumedBy: new iam.ServicePrincipal("batch.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSBatchServiceRole",
        ),
      ],
    });

    // Outputs
    new cdk.CfnOutput(this, "BatchJobRoleArn", {
      value: this.batchJobRole.roleArn,
    });

    new cdk.CfnOutput(this, "BatchServiceRoleArn", {
      value: this.batchServiceRole.roleArn,
    });

    new cdk.CfnOutput(this, "BatchSpotFleetRoleArn", {
      value: this.batchSpotFleetRole.roleArn,
    });

    new cdk.CfnOutput(this, "BatchInstanceProfileArn", {
      value: this.batchInstanceProfile.instanceProfileArn,
    });
  }
}
