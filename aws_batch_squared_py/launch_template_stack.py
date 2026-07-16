"""Launch template nested stack — EC2 launch template for Batch compute.

Ported from ``lib/launch-template-stack.ts``. Builds a multipart-MIME cloud-init
user-data payload that installs the CloudWatch agent, AWS CLI v2, and Mountpoint
for S3, then mounts the reference-data prefix.
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class LaunchTemplateStack(cdk.NestedStack):
    launch_template: ec2.LaunchTemplate
    launch_template_id: str

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        namespace: str,
        group_name: str,
        batch_compute_ami: str,
        s3_bucket_name: str,
        s3_reference_path: str,
        root_volume_size: int = 100,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create user data script (multipart MIME cloud-config + runcmd).
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
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
            # AL2023 package set: jq/git/unzip for the bootstrap + CloudWatch agent.
            # Dropped vs AL2: btrfs-progs & the /dev/xvdcz docker device are AL2
            # devicemapper-era (AL2023 uses overlay2 on root); sed & amazon-ssm-agent
            # are preinstalled on AL2023; the `zlib` package is not present under that
            # name on AL2023 (and the flat /opt/aws-cli bundle ships its own libs).
            "packages:",
            "- jq",
            "- git",
            "- unzip",
            "- amazon-cloudwatch-agent",
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
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/amazon-cloudwatch-agent.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/cloud-init.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/cloud-init.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/cloud-init-output.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/cloud-init-output.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/ecs/ecs-init.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/ecs-init.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/ecs/ecs-agent.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/ecs-agent.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/ecs/ecs-volume-plugin.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/ecs-volume-plugin.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/ebs-autoscale-install.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/ebs-autoscale-install.log"',
            "              },",
            "              {",
            '                "file_path": "/var/log/ebs-autoscale.log",',
            f'                "log_group_name": "/aws/ecs/container-instance/{namespace}",',
            f'                "log_stream_name": "/aws/ecs/container-instance/{namespace}/{{instance_id}}/ebs-autoscale.log"',
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
            f'- mount-s3 --allow-other s3://{s3_bucket_name}/{s3_reference_path}/ /mnt/s3-reference || echo "S3 mount failed - reference data may not be available"',
            "",
            "# Collect ECS logs to S3 for troubleshooting (best-effort: the ecs-additions"
            "# path may not exist on all AMI families, so never let it fail bootstrap).",
            "- sudo /opt/ecs-additions/ecs-logs-collector.sh || true",
            f"- aws s3 cp /opt/ecs-additions/collect-i*tgz s3://{s3_bucket_name}/ecs-instance-logs/ || true",
            "--==BOUNDARY==--",
        )

        # Create Launch Template
        self.launch_template = ec2.LaunchTemplate(
            self,
            "EC2LaunchTemplate",
            launch_template_name=f"{namespace}-launch-template",
            machine_image=ec2.MachineImage.from_ssm_parameter(batch_compute_ami),
            user_data=user_data,
            # AL2023 ECS-optimized uses overlay2 on the root volume — a single gp3
            # root disk covers the OS, container images, and writable layers. (AL2
            # needed the extra /dev/xvdcz devicemapper volume; not so here.) The root
            # device name for the AL2023 ECS AMI is /dev/xvda.
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        root_volume_size,
                        delete_on_termination=True,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                    ),
                ),
            ],
        )

        self.launch_template_id = self.launch_template.launch_template_id

        # Outputs
        cdk.CfnOutput(
            self,
            "LaunchTemplateId",
            value=self.launch_template_id,
            description=(
                "EC2 Launch Template ID to use when creating AWS Batch compute "
                "environments for genomics workflows"
            ),
        )
        cdk.CfnOutput(
            self,
            "LaunchTemplateLatestVersion",
            value=self.launch_template.latest_version_number,
            description="Latest version number of the launch template",
        )
