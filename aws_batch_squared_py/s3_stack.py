"""S3 nested stack — creates the workflow bucket or imports an existing one.

Ported from ``lib/s3-stack.ts``.
"""

from typing import List, Optional

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct


# Must match the Nextflow work-dir prefix defaults in NextflowStack
# (`${s3NextflowPrefix}/${s3WorkDirPrefix}` = `_nextflow/runs`). Keep in sync.
NEXTFLOW_WORKDIR_PREFIX = "_nextflow/runs/"


class S3Stack(cdk.NestedStack):
    bucket: s3.IBucket
    bucket_name: str
    bucket_arn: str

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        group_name: str,
        existing_bucket: bool,
        bucket_name: Optional[str] = None,
        work_dir_expiration_days: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if existing_bucket:
            if bucket_name is None:
                raise ValueError("bucketName is required when existingBucket is true")
            self.bucket = s3.Bucket.from_bucket_name(self, "ExistingBucket", bucket_name)
            self.bucket_name = bucket_name
            self.bucket_arn = self.bucket.bucket_arn
        else:
            # Generate bucket name if not provided
            resolved_bucket_name = (
                bucket_name
                or f"{group_name}-{namespace}-{cdk.Stack.of(self).account}"
            )

            # Always abort dangling multipart uploads; optionally expire Nextflow work-dir
            # intermediates (which dominate storage for genomics runs). Results/logs under
            # other prefixes are never touched.
            lifecycle_rules: List[s3.LifecycleRule] = [
                s3.LifecycleRule(
                    id="abort-incomplete-multipart-uploads",
                    abort_incomplete_multipart_upload_after=cdk.Duration.days(7),
                ),
            ]
            if work_dir_expiration_days and work_dir_expiration_days > 0:
                lifecycle_rules.append(
                    s3.LifecycleRule(
                        id="expire-nextflow-workdir",
                        prefix=NEXTFLOW_WORKDIR_PREFIX,
                        expiration=cdk.Duration.days(work_dir_expiration_days),
                    )
                )

            self.bucket = s3.Bucket(
                self,
                "S3Bucket",
                bucket_name=resolved_bucket_name,
                encryption=s3.BucketEncryption.S3_MANAGED,
                removal_policy=cdk.RemovalPolicy.RETAIN,
                auto_delete_objects=False,
                lifecycle_rules=lifecycle_rules,
            )

            self.bucket_name = self.bucket.bucket_name
            self.bucket_arn = self.bucket.bucket_arn

        # Outputs
        cdk.CfnOutput(self, "BucketName", value=self.bucket_name)
        cdk.CfnOutput(self, "BucketArn", value=self.bucket_arn)
