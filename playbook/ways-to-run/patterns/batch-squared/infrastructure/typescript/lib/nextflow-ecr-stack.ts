import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";

import * as cdk from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as codebuild from "aws-cdk-lib/aws-codebuild";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as cr from "aws-cdk-lib/custom-resources";
import type { Construct } from "constructs";

export interface NextflowEcrStackProps extends cdk.NestedStackProps {
  namespace: string;
  nextflowVersion?: string;
}

export class NextflowEcrStack extends cdk.NestedStack {
  public readonly repository: ecr.Repository;
  public readonly imageUri: string;

  constructor(scope: Construct, id: string, props: NextflowEcrStackProps) {
    super(scope, id, props);

    const nextflowVersion = props.nextflowVersion || "latest";

    this.repository = new ecr.Repository(this, "NextflowECRRepository", {
      repositoryName: `nextflow-head-${props.namespace}`,
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
      lifecycleRules: [
        {
          description: "Keep last 10 images",
          maxImageCount: 10,
        },
      ],
    });

    // Create CodeBuild Role
    const buildRole = new iam.Role(this, "NextflowImageBuildRole", {
      assumedBy: new iam.ServicePrincipal("codebuild.amazonaws.com"),
      inlinePolicies: {
        NextflowImageBuildPolicy: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
              ],
              resources: [
                `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/codebuild/*`,
              ],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
              ],
              resources: [this.repository.repositoryArn],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ["ecr:GetAuthorizationToken"],
              resources: ["*"],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ["s3:GetObject", "s3:ListBucket"],
              resources: [
                `arn:aws:s3:::${this.account}-${this.region}-cloudformation-templates`,
                `arn:aws:s3:::${this.account}-${this.region}-cloudformation-templates/*`,
              ],
            }),
          ],
        }),
      },
    });

    // Custom entrypoint that configures the AWS Batch executor at runtime from the
    // NF_JOB_QUEUE / NF_WORKDIR / NF_LOGSDIR env vars the head-node job definition
    // provides, then runs `nextflow run`. Without this the container falls back to
    // Nextflow's local executor and cannot use the S3 work-dir.
    const entrypointScript = fs.readFileSync(
      path.join(__dirname, "..", "docker", "nextflow-head", "nextflow.aws.sh"),
      "utf8",
    );

    // Create Dockerfile content. `aws` (v2) and `git` are needed by the entrypoint
    // for S3 session-cache staging and git-based project checkouts respectively.
    const dockerfileContent = `
FROM amazoncorretto:17
RUN yum install -y procps-ng which unzip git tar gzip && \\
    curl -s https://get.nextflow.io | bash && \\
    mv nextflow /usr/local/bin/ && \\
    chmod +x /usr/local/bin/nextflow && \\
    nextflow -version && \\
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \\
    unzip -q /tmp/awscliv2.zip -d /tmp && \\
    /tmp/aws/install -b /usr/bin && \\
    rm -rf /tmp/aws* && \\
    aws --version
COPY nextflow.aws.sh /opt/bin/nextflow.aws.sh
RUN chmod +x /opt/bin/nextflow.aws.sh
WORKDIR /opt/work
ENTRYPOINT ["/opt/bin/nextflow.aws.sh"]
`;

    // Content hash of everything that defines the image. Passing this as a custom
    // resource property forces a CloudFormation Update (and thus a CodeBuild rebuild)
    // whenever the Dockerfile or entrypoint changes.
    const imageSourceHash = crypto
      .createHash("sha256")
      .update(dockerfileContent)
      .update(entrypointScript)
      .digest("hex");

    // Create CodeBuild Project
    const buildProject = new codebuild.Project(
      this,
      "NextflowImageBuildProject",
      {
        projectName: `nextflow-image-build-${props.namespace}`,
        role: buildRole,
        environment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
          privileged: true,
          environmentVariables: {
            AWS_DEFAULT_REGION: { value: this.region },
            AWS_ACCOUNT_ID: { value: this.account },
            IMAGE_REPO_NAME: { value: this.repository.repositoryName },
            NEXTFLOW_VERSION: { value: nextflowVersion },
          },
        },
        buildSpec: codebuild.BuildSpec.fromObject({
          version: "0.2",
          phases: {
            pre_build: {
              commands: [
                "echo Logging in to Amazon ECR...",
                "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com",
              ],
            },
            build: {
              commands: [
                "echo Build started on `date`",
                `echo '${dockerfileContent}' > Dockerfile`,
                // Write the entrypoint verbatim via a quoted heredoc so shell
                // metacharacters ($, backticks, quotes) in the script are preserved.
                "cat > nextflow.aws.sh <<'NF_AWS_ENTRYPOINT_EOF'\n" +
                  entrypointScript +
                  "\nNF_AWS_ENTRYPOINT_EOF",
                "docker build --build-arg VERSION=$NEXTFLOW_VERSION -t $IMAGE_REPO_NAME:$NEXTFLOW_VERSION .",
                "docker tag $IMAGE_REPO_NAME:$NEXTFLOW_VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$NEXTFLOW_VERSION",
                "docker tag $IMAGE_REPO_NAME:$NEXTFLOW_VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest",
              ],
            },
            post_build: {
              commands: [
                "echo Build completed on `date`",
                "echo Pushing the Docker images...",
                "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$NEXTFLOW_VERSION",
                "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest",
              ],
            },
          },
        }),
      },
    );

    // Create Lambda function to trigger the build
    const triggerBuildFunction = new lambda.Function(
      this,
      "NextflowImageBuildFunction",
      {
        functionName: `nextflow-image-build-trigger-${props.namespace}`,
        runtime: lambda.Runtime.PYTHON_3_9,
        handler: "index.handler",
        code: lambda.Code.fromInline(`
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
`),
        timeout: cdk.Duration.seconds(60),
      },
    );

    // Grant the Lambda function permission to start builds
    triggerBuildFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["codebuild:StartBuild"],
        resources: [buildProject.projectArn],
      }),
    );

    // Create Custom Resource to trigger the build
    const provider = new cr.Provider(this, "NextflowImageBuildProvider", {
      onEventHandler: triggerBuildFunction,
    });

    new cdk.CustomResource(this, "NextflowImageBuildTrigger", {
      serviceToken: provider.serviceToken,
      properties: {
        ProjectName: buildProject.projectName,
        // Changing this on any image-definition edit triggers a CloudFormation
        // Update, which makes the trigger Lambda start a fresh CodeBuild run.
        SourceHash: imageSourceHash,
      },
    });

    this.imageUri = `${this.account}.dkr.ecr.${this.region}.amazonaws.com/${this.repository.repositoryName}:latest`;

    // Outputs
    new cdk.CfnOutput(this, "NextflowImageUri", {
      value: this.imageUri,
      description: "URI of the built Nextflow container image",
    });

    new cdk.CfnOutput(this, "NextflowRepositoryUri", {
      value: this.repository.repositoryUri,
      description: "URI of the ECR repository",
    });
  }
}
