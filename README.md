# V2Ray Proxy CDK Stack

This project contains the CDK required to deploy a REALITY/VLESS proxy server on AWS. It currently uses https://github.com/aleskxyz/reality-ezpz to setup the proxy server.

## What this will create

- EC2 instance (t2.micro) running **Ubuntu 22.04**. Should be eligible for the free tier in most regions, assuming this is your only instance.
- Maximally restricted VPC configuration to only allow traffic required for the proxy to operate
- No SSH access, server is only accessible via the AWS SSM Agent. **Prevents the proxy from being identified by port scanning.**
- Elastic IP enabled, provides a static IPv4 address for the proxy
- Fully automated REALITY/VLESS proxy setup via user data script

## Prerequisites

1. AWS CLI installed and configured
2. Node.js and npm installed
3. Python 3.8+ installed
4. AWS CDK CLI installed (`npm install -g aws-cdk`)
5. Required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Deployment Steps

1. Configure AWS credentials:
   ```bash
   aws configure
   ```
   You'll be prompted to enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name
   - Default output format (optional, press Enter for None)

   These will be saved in `~/.aws/credentials`

2. Set required environment variables:
   ```bash
   # Get your AWS account ID automatically
   export CDK_DEPLOY_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   # Set your desired region
   export CDK_DEPLOY_REGION="your-target-region"
   ```
   Or set them manually if you prefer:
   ```bash
   export CDK_DEPLOY_ACCOUNT="your-aws-account-id"
   export CDK_DEPLOY_REGION="your-target-region"
   ```

3. Deploy the stack:
   ```bash
   cdk bootstrap
   cdk deploy --outputs-file outputs.json
   ```
   The `--outputs-file` flag is important as it saves the instance properties for later use.

4. After deployment, you can fetch your REALITY configuration:
   ```bash
   python3 fetch-config.py
   ```

## Accessing the Instance

The instance is configured with AWS Systems Manager Session Manager for secure access without SSH keys.

### Interactive Shell Session
To get a full shell session (similar to SSH):
```bash
aws ssm start-session --target $INSTANCE_ID \
    --region $CDK_DEPLOY_REGION \   
    --document-name AWS-StartInteractiveCommand 
```

### Direct Command Execution
To run a single command:
```bash
aws ssm send-command \
    --target $INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --region $CDK_DEPLOY_REGION \
    --parameters 'commands=["your-command-here"]'
```

### Tips for Session Manager Use
1. You can find your instance ID in the AWS Console or the `outputs.json` file.
2. You can create an alias for easier access:
   ```bash
   alias proxy-shell='aws ssm start-session --target $INSTANCE_ID --region $CDK_DEPLOY_REGION --document-name AWS-StartInteractiveCommand'
   ```