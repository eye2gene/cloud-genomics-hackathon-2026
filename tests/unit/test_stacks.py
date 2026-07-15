"""Placeholder test suite.

There is no real coverage yet — see IMPROVEMENTS.md. This smoke test just
confirms the app synthesizes and the top-level stack contains the expected
nested stacks. Run with ``pytest``.
"""

import aws_cdk as cdk
from aws_cdk import assertions

from aws_batch_squared_py.config import NextflowBatchConfig
from aws_batch_squared_py.nextflow_batch_stack import NextflowBatchStack


def _synth_template() -> assertions.Template:
    app = cdk.App(
        context={
            "createVpc": True,
            "existingBucket": False,
            "buildNextflowImage": True,
        }
    )
    config = NextflowBatchConfig.from_context(app)
    stack = NextflowBatchStack(
        app,
        "NextflowBatchStack",
        config=config,
        env=cdk.Environment(account="123456789012", region="eu-west-2"),
    )
    return assertions.Template.from_stack(stack)


def test_synthesizes_seven_nested_stacks():
    template = _synth_template()
    # VPC, S3, IAM, LaunchTemplate, Batch, Nextflow, NextflowEcr.
    template.resource_count_is("AWS::CloudFormation::Stack", 7)


def test_publishes_ssm_parameters():
    template = _synth_template()
    template.resource_count_is("AWS::SSM::Parameter", 3)


def test_validation_requires_existing_image_when_not_building():
    app = cdk.App(
        context={
            "createVpc": True,
            "existingBucket": False,
            "buildNextflowImage": False,
        }
    )
    try:
        NextflowBatchConfig.from_context(app)
    except ValueError:
        return
    raise AssertionError("expected ValueError when buildNextflowImage is false and no image given")
