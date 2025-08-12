import * as cdk from "aws-cdk-lib";
import * as batch from "aws-cdk-lib/aws-batch";
import * as iam from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";

export interface NextflowStackProps extends cdk.NestedStackProps {
  namespace: string;
  groupName: string;
  nextflowImage: string;
  s3BucketParam: string;
  onDemandQueueParam: string;
  spotQueueParam: string;
  s3NextflowPrefix?: string;
  s3LogsDirPrefix?: string;
  s3WorkDirPrefix?: string;
}

export class NextflowStack extends cdk.NestedStack {
  public readonly nextflowJobRole: iam.Role;
  public readonly nextflowJobDefinition: batch.CfnJobDefinition;

  constructor(scope: Construct, id: string, props: NextflowStackProps) {
    super(scope, id, props);

    const account = cdk.Stack.of(this).account;
    const region = cdk.Stack.of(this).region;

    const s3NextflowPrefix = props.s3NextflowPrefix || "_nextflow";
    const s3LogsDirPrefix = props.s3LogsDirPrefix || "logs";
    const s3WorkDirPrefix = props.s3WorkDirPrefix || "runs";

    // Create Nextflow Job Role
    this.nextflowJobRole = new iam.Role(this, "IAMNextflowJobRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonS3ReadOnlyAccess"),
      ],
      inlinePolicies: {
        [`Nextflow-Batch-Access-${region}`]: new iam.PolicyDocument({
          statements: [
            // Batch read access
            new iam.PolicyStatement({
              sid: "BatchReadAccessAllowAll",
              effect: iam.Effect.ALLOW,
              resources: ["*"],
              actions: ["batch:List*", "batch:Describe*"],
            }),
            // Batch tagging permissions
            new iam.PolicyStatement({
              sid: "BatchTagAccess",
              effect: iam.Effect.ALLOW,
              resources: ["*"],
              actions: [
                "batch:TagResource",
                "batch:ListTagsForResource",
                "batch:UntagResource",
              ],
            }),
            // CloudWatch logs read access
            new iam.PolicyStatement({
              sid: "CloudwatchReadLogEvents",
              effect: iam.Effect.ALLOW,
              resources: [
                `arn:aws:logs:${region}:${account}:log-group:/aws/batch/job:log-stream:*`,
              ],
              actions: ["logs:GetLogEvents"],
            }),
            // Batch job submission
            new iam.PolicyStatement({
              sid: "BatchWriteAccessAllowJobSubmission",
              effect: iam.Effect.ALLOW,
              resources: [
                `{{resolve:ssm:${props.onDemandQueueParam}:1}}`,
                `{{resolve:ssm:${props.spotQueueParam}:1}}`,
                "arn:aws:batch:*:*:job-definition/nf-*:*",
              ],
              actions: ["batch:*Job"],
            }),
            // Batch job definition management
            new iam.PolicyStatement({
              sid: "BatchWriteAccessAllowJobDefinition",
              effect: iam.Effect.ALLOW,
              resources: [
                "arn:aws:batch:*:*:job-definition/nf-*",
                "arn:aws:batch:*:*:job-definition/nf-*:*",
              ],
              actions: ["batch:*JobDefinition"],
            }),
          ],
        }),
        [`Nextflow-S3Bucket-Access-${region}`]: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              resources: [
                `arn:aws:s3:::{{resolve:ssm:${props.s3BucketParam}:1}}`,
                `arn:aws:s3:::{{resolve:ssm:${props.s3BucketParam}:1}}/*`,
              ],
              actions: ["s3:*"],
            }),
          ],
        }),
        [`Nextflow-Instance-Access-${region}`]: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                "ecs:DescribeTasks",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeInstanceAttribute",
                "ecs:DescribeContainerInstances",
                "ec2:DescribeInstanceStatus",
              ],
              resources: ["*"],
            }),
          ],
        }),
      },
    });

    // Create Nextflow Job Definition
    this.nextflowJobDefinition = new batch.CfnJobDefinition(
      this,
      "BatchNextflowJobDefinition",
      {
        jobDefinitionName: `nextflow-${props.namespace}`,
        type: "container",
        timeout: {
          attemptDurationSeconds: 3600,
        },
        containerProperties: {
          memory: 16384,
          vcpus: 4,
          image: props.nextflowImage,
          jobRoleArn: this.nextflowJobRole.roleArn,
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
              // Work (child) jobs default to the Spot queue for cost savings; they are
              // retriable so Spot interruptions are tolerable. The head node itself still
              // runs on the On-Demand queue (that's the queue you submit this job to).
              // Override per-run by setting NF_JOB_QUEUE in the submit-job container env.
              name: "NF_JOB_QUEUE",
              value: `{{resolve:ssm:${props.spotQueueParam}:1}}`,
            },
            {
              name: "NF_LOGSDIR",
              value: `s3://{{resolve:ssm:${props.s3BucketParam}:1}}/${s3NextflowPrefix}/${s3LogsDirPrefix}`,
            },
            {
              name: "NF_WORKDIR",
              value: `s3://{{resolve:ssm:${props.s3BucketParam}:1}}/${s3NextflowPrefix}/${s3WorkDirPrefix}`,
            },
          ],
        },
      },
    );

    // Outputs
    new cdk.CfnOutput(this, "NextflowBucket", {
      value: `s3://{{resolve:ssm:${props.s3BucketParam}:1}}`,
      description:
        "S3 Bucket used to store Nextflow metadata (session cache, logs, and intermediate results)",
    });

    new cdk.CfnOutput(this, "LogsDir", {
      value: `s3://{{resolve:ssm:${props.s3BucketParam}:1}}/${s3NextflowPrefix}/${s3LogsDirPrefix}`,
      description: "S3 URI where nextflow session cache and logs are stored",
    });

    new cdk.CfnOutput(this, "WorkDir", {
      value: `s3://{{resolve:ssm:${props.s3BucketParam}:1}}/${s3NextflowPrefix}/${s3WorkDirPrefix}`,
      description: "S3 URI where workflow intermediate results are stored",
    });

    new cdk.CfnOutput(this, "NextflowJobDefinition", {
      value: this.nextflowJobDefinition.ref,
      description:
        "Batch Job Definition that creates a nextflow head node for running workflows",
    });

    new cdk.CfnOutput(this, "NextflowJobRole", {
      value: this.nextflowJobRole.roleArn,
      description:
        "IAM Role that allows the nextflow head node job access to S3 and Batch",
    });
  }
}
