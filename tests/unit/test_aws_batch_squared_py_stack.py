import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_batch_squared_py.aws_batch_squared_py_stack import AwsBatchSquaredPyStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_batch_squared_py/aws_batch_squared_py_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsBatchSquaredPyStack(app, "aws-batch-squared-py")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
