import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import type { Construct } from "constructs";

export interface S3StackProps extends cdk.NestedStackProps {
  namespace: string;
  groupName: string;
  bucketName?: string;
  existingBucket: boolean;
  /** Days after which Nextflow work-dir intermediates expire (0/undefined disables). */
  workDirExpirationDays?: number;
}

// Must match the Nextflow work-dir prefix defaults in NextflowStack
// (`${s3NextflowPrefix}/${s3WorkDirPrefix}` = `_nextflow/runs`). Keep in sync.
const NEXTFLOW_WORKDIR_PREFIX = "_nextflow/runs/";

export class S3Stack extends cdk.NestedStack {
  public readonly bucket: s3.IBucket;
  public readonly bucketName: string;
  public readonly bucketArn: string;

  constructor(scope: Construct, id: string, props: S3StackProps) {
    super(scope, id, props);

    if (props.existingBucket) {
      if (props.bucketName === undefined) {
        throw new Error("bucketName is required when existingBucket is true");
      }
      this.bucket = s3.Bucket.fromBucketName(
        this,
        "ExistingBucket",
        props.bucketName,
      );
      this.bucketName = props.bucketName;
      this.bucketArn = this.bucket.bucketArn;
    } else {
      // Generate bucket name if not provided
      const bucketName =
        props.bucketName ||
        `${props.groupName}-${props.namespace}-${cdk.Stack.of(this).account}`;

      // Always abort dangling multipart uploads; optionally expire Nextflow work-dir
      // intermediates (which dominate storage for genomics runs). Results/logs under
      // other prefixes are never touched.
      const lifecycleRules: s3.LifecycleRule[] = [
        {
          id: "abort-incomplete-multipart-uploads",
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
        },
      ];
      if (props.workDirExpirationDays && props.workDirExpirationDays > 0) {
        lifecycleRules.push({
          id: "expire-nextflow-workdir",
          prefix: NEXTFLOW_WORKDIR_PREFIX,
          expiration: cdk.Duration.days(props.workDirExpirationDays),
        });
      }

      this.bucket = new s3.Bucket(this, "S3Bucket", {
        bucketName,
        encryption: s3.BucketEncryption.S3_MANAGED,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        autoDeleteObjects: false,
        lifecycleRules,
      });

      this.bucketName = this.bucket.bucketName;
      this.bucketArn = this.bucket.bucketArn;
    }

    // Outputs
    new cdk.CfnOutput(this, "BucketName", {
      value: this.bucketName,
    });

    new cdk.CfnOutput(this, "BucketArn", {
      value: this.bucketArn,
    });
  }
}
