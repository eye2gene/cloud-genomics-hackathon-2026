"""Nextflow ECR nested stack — builds the head-node image via CodeBuild.

Ported from ``lib/nextflow-ecr-stack.ts``. Creates an ECR repo, a CodeBuild
project that builds and pushes the Nextflow head-node image, and a custom
resource (backed by a Lambda) that triggers the build on create/update. A
content hash of the Dockerfile + entrypoint forces a rebuild whenever either
changes.
"""

import hashlib
import os
from typing import Optional

import aws_cdk as cdk
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import custom_resources as cr
from constructs import Construct


# Inline handler for the build-trigger Lambda (kept verbatim from the TS source).
_TRIGGER_LAMBDA_CODE = """
import boto3
import json

def handler(event, context):
    try:
        codebuild = boto3.client('codebuild')
        project_name = event['ResourceProperties']['ProjectName']

        if event['RequestType'] in ['Create', 'Update']:
            response = codebuild.start_build(projectName=project_name)
            build_id = response['build']['id']
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': build_id,
                'Data': {'BuildId': build_id}
            }
        else:
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': event.get('PhysicalResourceId', 'none')
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'Status': 'FAILED',
            'Reason': str(e),
            'PhysicalResourceId': event.get('PhysicalResourceId', 'none')
        }
"""


class NextflowEcrStack(cdk.NestedStack):
    repository: ecr.Repository
    image_uri: str

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        nextflow_version: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        nextflow_version = nextflow_version or "latest"

        self.repository = ecr.Repository(
            self,
            "NextflowECRRepository",
            repository_name=f"nextflow-head-{namespace}",
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.MUTABLE,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                ),
            ],
        )

        # Create CodeBuild Role
        build_role = iam.Role(
            self,
            "NextflowImageBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            inline_policies={
                "NextflowImageBuildPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:"
                                "log-group:/aws/codebuild/*"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:PutImage",
                                "ecr:InitiateLayerUpload",
                                "ecr:UploadLayerPart",
                                "ecr:CompleteLayerUpload",
                            ],
                            resources=[self.repository.repository_arn],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["ecr:GetAuthorizationToken"],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject", "s3:ListBucket"],
                            resources=[
                                f"arn:aws:s3:::{self.account}-{self.region}-"
                                "cloudformation-templates",
                                f"arn:aws:s3:::{self.account}-{self.region}-"
                                "cloudformation-templates/*",
                            ],
                        ),
                    ]
                ),
            },
        )

        # Custom entrypoint that configures the AWS Batch executor at runtime from the
        # NF_JOB_QUEUE / NF_WORKDIR / NF_LOGSDIR env vars the head-node job definition
        # provides, then runs `nextflow run`. Without this the container falls back to
        # Nextflow's local executor and cannot use the S3 work-dir.
        entrypoint_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "docker",
            "nextflow-head",
            "nextflow.aws.sh",
        )
        with open(entrypoint_path, "r", encoding="utf-8") as f:
            entrypoint_script = f.read()

        # Create Dockerfile content. `aws` (v2) and `git` are needed by the entrypoint
        # for S3 session-cache staging and git-based project checkouts respectively.
        # Raw string preserves the `\` shell line-continuations verbatim.
        dockerfile_content = r"""
FROM amazoncorretto:17
RUN yum install -y procps-ng which unzip git tar gzip && \
    curl -s https://get.nextflow.io | bash && \
    mv nextflow /usr/local/bin/ && \
    chmod +x /usr/local/bin/nextflow && \
    nextflow -version && \
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install -b /usr/bin && \
    rm -rf /tmp/aws* && \
    aws --version
COPY nextflow.aws.sh /opt/bin/nextflow.aws.sh
RUN chmod +x /opt/bin/nextflow.aws.sh
WORKDIR /opt/work
ENTRYPOINT ["/opt/bin/nextflow.aws.sh"]
"""

        # Content hash of everything that defines the image. Passing this as a custom
        # resource property forces a CloudFormation Update (and thus a CodeBuild rebuild)
        # whenever the Dockerfile or entrypoint changes.
        image_source_hash = hashlib.sha256(
            dockerfile_content.encode("utf-8") + entrypoint_script.encode("utf-8")
        ).hexdigest()

        # Create CodeBuild Project
        build_project = codebuild.Project(
            self,
            "NextflowImageBuildProject",
            project_name=f"nextflow-image-build-{namespace}",
            role=build_role,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
                environment_variables={
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                        value=self.region
                    ),
                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value=self.account
                    ),
                    "IMAGE_REPO_NAME": codebuild.BuildEnvironmentVariable(
                        value=self.repository.repository_name
                    ),
                    "NEXTFLOW_VERSION": codebuild.BuildEnvironmentVariable(
                        value=nextflow_version
                    ),
                },
            ),
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "pre_build": {
                            "commands": [
                                "echo Logging in to Amazon ECR...",
                                "aws ecr get-login-password --region $AWS_DEFAULT_REGION "
                                "| docker login --username AWS --password-stdin "
                                "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com",
                            ],
                        },
                        "build": {
                            "commands": [
                                "echo Build started on `date`",
                                f"echo '{dockerfile_content}' > Dockerfile",
                                # Write the entrypoint verbatim via a quoted heredoc so shell
                                # metacharacters ($, backticks, quotes) in the script are
                                # preserved.
                                "cat > nextflow.aws.sh <<'NF_AWS_ENTRYPOINT_EOF'\n"
                                + entrypoint_script
                                + "\nNF_AWS_ENTRYPOINT_EOF",
                                "docker build --build-arg VERSION=$NEXTFLOW_VERSION "
                                "-t $IMAGE_REPO_NAME:$NEXTFLOW_VERSION .",
                                "docker tag $IMAGE_REPO_NAME:$NEXTFLOW_VERSION "
                                "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
                                "/$IMAGE_REPO_NAME:$NEXTFLOW_VERSION",
                                "docker tag $IMAGE_REPO_NAME:$NEXTFLOW_VERSION "
                                "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
                                "/$IMAGE_REPO_NAME:latest",
                            ],
                        },
                        "post_build": {
                            "commands": [
                                "echo Build completed on `date`",
                                "echo Pushing the Docker images...",
                                "docker push $AWS_ACCOUNT_ID.dkr.ecr."
                                "$AWS_DEFAULT_REGION.amazonaws.com"
                                "/$IMAGE_REPO_NAME:$NEXTFLOW_VERSION",
                                "docker push $AWS_ACCOUNT_ID.dkr.ecr."
                                "$AWS_DEFAULT_REGION.amazonaws.com"
                                "/$IMAGE_REPO_NAME:latest",
                            ],
                        },
                    },
                }
            ),
        )

        # Create Lambda function to trigger the build
        trigger_build_function = lambda_.Function(
            self,
            "NextflowImageBuildFunction",
            function_name=f"nextflow-image-build-trigger-{namespace}",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline(_TRIGGER_LAMBDA_CODE),
            timeout=cdk.Duration.seconds(60),
        )

        # Grant the Lambda function permission to start builds
        trigger_build_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["codebuild:StartBuild"],
                resources=[build_project.project_arn],
            )
        )

        # Create Custom Resource to trigger the build
        provider = cr.Provider(
            self,
            "NextflowImageBuildProvider",
            on_event_handler=trigger_build_function,
        )

        cdk.CustomResource(
            self,
            "NextflowImageBuildTrigger",
            service_token=provider.service_token,
            properties={
                "ProjectName": build_project.project_name,
                # Changing this on any image-definition edit triggers a CloudFormation
                # Update, which makes the trigger Lambda start a fresh CodeBuild run.
                "SourceHash": image_source_hash,
            },
        )

        self.image_uri = (
            f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/"
            f"{self.repository.repository_name}:latest"
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "NextflowImageUri",
            value=self.image_uri,
            description="URI of the built Nextflow container image",
        )
        cdk.CfnOutput(
            self,
            "NextflowRepositoryUri",
            value=self.repository.repository_uri,
            description="URI of the ECR repository",
        )
