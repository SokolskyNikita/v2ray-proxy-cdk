from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    Tags,
)
from constructs import Construct


class VlessProxyStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create infrastructure
        eip, instance = self.create_infrastructure()

        # Create outputs
        self.create_outputs(eip, instance)

    def create_infrastructure(self):
        """Main method coordinating the infrastructure creation"""
        # Create all AWS infrastructure
        return self.create_aws_infrastructure()

    def create_aws_infrastructure(self):
        """Create all AWS infrastructure components"""
        # Create VPC
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,
            nat_gateways=0,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            vpc_name="reality-proxy-vpc",
        )

        # Basic security group rules
        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            description="Allow VLESS-REALITY traffic and HTTP",
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow REALITY-VLESS traffic IPv4"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP for certificate IPv4"
        )

        # Basic IAM role with SSM only
        role = iam.Role(
            self,
            "InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            # Start root shell session
            "sudo -i",
            # Install Reality proxy
            "bash <(curl -sL https://raw.githubusercontent.com/aleskxyz/reality-ezpz/master/reality-ezpz.sh)",
            "touch /tmp/reality-setup-complete",
        )

        # AMI ID lookup for Ubuntu 20.04
        ami_id = ssm.StringParameter.value_from_lookup(
            self,
            "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
        )

        # Create EC2 Instance, eligible for Free Tier
        instance = ec2.Instance(
            self,
            "Instance",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.generic_linux({self.region: ami_id}),
            vpc=vpc,
            security_group=security_group,
            role=role,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            require_imdsv2=True,
        )

        # Add tags to the EC2 instance
        Tags.of(instance).add("Name", "Reality-VLESS-Server")
        Tags.of(instance).add("Purpose", "Hardened Reality/VLESS protocol proxy server")

        # Elastic IP
        eip = ec2.CfnEIP(self, "ElasticIP")

        # Associate EIP with the EC2 instance
        ec2.CfnEIPAssociation(
            self,
            "EIPAssociation",
            allocation_id=eip.attr_allocation_id,
            instance_id=instance.instance_id,
        )

        return eip, instance

    def create_outputs(self, eip, instance):
        CfnOutput(
            self,
            "ProxyIP",
            value=eip.ref,
            description="Static IP address for your Reality proxy",
        )
        CfnOutput(
            self,
            "InstanceId",
            value=instance.instance_id,
            description="EC2 Instance ID",
        )
        CfnOutput(
            self,
            "Region",
            value=self.region,
            description="AWS Region where the proxy is deployed",
        )
        CfnOutput(
            self,
            "SessionManagerAccess",
            value=f"aws ssm start-session --target {instance.instance_id}",
            description="Use AWS Systems Manager Session Manager to access the instance",
        )
        CfnOutput(
            self,
            "ConfigInstructions",
            value="Run 'python3 fetch_config.py' to get your Reality configuration",
            description="How to get your Reality configuration",
        )
