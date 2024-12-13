from aws_cdk import App, Environment
import os
from cdk_proxy_stack import VlessProxyStack

app = App()
env = Environment(
    account=os.environ["CDK_DEPLOY_ACCOUNT"], region=os.environ["CDK_DEPLOY_REGION"]
)

VlessProxyStack(app, "VlessProxyStack", env=env)
app.synth()
