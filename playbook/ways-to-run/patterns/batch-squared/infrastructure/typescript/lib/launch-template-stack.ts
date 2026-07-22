import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import type { Construct } from "constructs";

export interface LaunchTemplateStackProps extends cdk.NestedStackProps {
  namespace: string;
  groupName: string;
  batchComputeAmi: string;
  s3BucketName: string;
  s3ReferencePath: string;
  dockerStorageVolumeSize?: number;
}

export class LaunchTemplateStack extends cdk.NestedStack {
  public readonly launchTemplate: ec2.LaunchTemplate;
  public readonly launchTemplateId: string;

  constructor(scope: Construct, id: string, props: LaunchTemplateStackProps) {
    super(scope, id, props);

    const dockerStorageVolumeSize = props.dockerStorageVolumeSize || 500;

    // Create user data script
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      "MIME-Version: 1.0",
      'Content-Type: multipart/mixed; boundary="==BOUNDARY=="',
      "",
      "--==BOUNDARY==",
      'Content-Type: text/cloud-config; charset="us-ascii"',
      "",
      "#cloud-config",
      "repo_update: true",
      "repo_upgrade: security",
      "",
      "packages:",
      "- jq",
      "- btrfs-progs",
      "- sed",
      "- git",
      "- amazon-ssm-agent",
      "- unzip",
      "- amazon-cloudwatch-agent",
      "- zlib",
      "",
      "write_files:",
      "- permissions: '0644'",
      "  path: /opt/aws/amazon-cloudwatch-agent/etc/config.json",
      "  content: |",
      "    {",
      '      "agent": {',
      '        "logfile": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log"',
      "      },",
      '      "logs": {',
      '        "logs_collected": {',
      '          "files": {',
      '            "collect_list": [',
      "              {",
      '                "file_path": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/amazon-cloudwatch-agent.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/cloud-init.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/cloud-init.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/cloud-init-output.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/cloud-init-output.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/ecs/ecs-init.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/ecs-init.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/ecs/ecs-agent.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/ecs-agent.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/ecs/ecs-volume-plugin.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/ecs-volume-plugin.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/ebs-autoscale-install.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/ebs-autoscale-install.log"`,
      "              },",
      "              {",
      '                "file_path": "/var/log/ebs-autoscale.log",',
      `                "log_group_name": "/aws/ecs/container-instance/${props.namespace}",`,
      `                "log_stream_name": "/aws/ecs/container-instance/${props.namespace}/{instance_id}/ebs-autoscale.log"`,
      "              }",
      "            ]",
      "          }",
      "        }",
      "      }",
      "    }",
      "",
      "runcmd:",
      "# start the amazon-cloudwatch-agent",
      "- /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json",
      "",
      "# Create swap space to prevent 'Cannot allocate memory' errors during large S3 downloads",
      "- fallocate -l 16G /swapfile",
      "- chmod 600 /swapfile",
      "- mkswap /swapfile",
      "- swapon /swapfile",
      "- echo '/swapfile swap swap defaults 0 0' >> /etc/fstab",
      "",
      "# install aws-cli v2 and copy the static binary in an easy to find location for bind-mounts into containers",
      '- curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"',
      "- unzip -q /tmp/awscliv2.zip -d /tmp",
      "- /tmp/aws/install -b /usr/bin",
      "",
      "# check that the aws-cli was actually installed. if not shutdown (terminate) the instance",
      "- command -v aws || shutdown -P now",
      "",
      "- mkdir -p /opt/aws-cli/bin",
      "- cp -a $(dirname $(find /usr/local/aws-cli -name 'aws' -type f))/. /opt/aws-cli/bin/",
      "",
      "# Install AWS Mountpoint for Amazon S3",
      "- curl -L https://s3.amazonaws.com/mountpoint-s3-release/latest/x86_64/mount-s3.rpm -o /tmp/mount-s3.rpm",
      "- yum install -y /tmp/mount-s3.rpm",
      "- rm -f /tmp/mount-s3.rpm",
      "",
      "# Create mount directory for S3 reference data",
      "- mkdir -p /mnt/s3-reference",
      "",
      "# Mount S3 reference data",
      `- mount-s3 --allow-other s3://${props.s3BucketName}/${props.s3ReferencePath}/ /mnt/s3-reference || echo "S3 mount failed - reference data may not be available"`,
      "",
      "# Added below logic for collecting the ecs logs on s3 for troubleshooting",
      "- sudo /opt/ecs-additions/ecs-logs-collector.sh",
      `- aws s3 cp /opt/ecs-additions/collect-i*tgz s3://${props.s3BucketName}/ecs-instance-logs/`,
      "--==BOUNDARY==--",
    );

    // Create Launch Template
    this.launchTemplate = new ec2.LaunchTemplate(this, "EC2LaunchTemplate", {
      launchTemplateName: `${props.namespace}-launch-template`,
      machineImage: ec2.MachineImage.fromSsmParameter(props.batchComputeAmi),
      userData,
      blockDevices: [
        {
          // Single root volume — Docker data-root lives here by default on ECS-optimized AL2
          // 500 GB gp3 with 250 MB/s throughput for WGS FASTQ processing
          deviceName: "/dev/xvda",
          volume: ec2.BlockDeviceVolume.ebs(dockerStorageVolumeSize, {
            deleteOnTermination: true,
            volumeType: ec2.EbsDeviceVolumeType.GP3,
            throughput: 250,
          }),
        },
      ],
    });

    this.launchTemplateId = this.launchTemplate.launchTemplateId!;

    // Outputs
    new cdk.CfnOutput(this, "LaunchTemplateId", {
      value: this.launchTemplateId,
      description:
        "EC2 Launch Template ID to use when creating AWS Batch compute environments for genomics workflows",
    });

    new cdk.CfnOutput(this, "LaunchTemplateLatestVersion", {
      value: this.launchTemplate.latestVersionNumber,
      description: "Latest version number of the launch template",
    });
  }
}
