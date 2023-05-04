import pulumi
from pulumi_aws import ec2, iam

# Create a VPC
vpc = ec2.Vpc('vpc', cidr_block='10.0.0.0/16', tags={'Name': 'pulumi-vpc'})

# Create an Internet Gateway
internet_gateway = ec2.InternetGateway('internet-gateway',
                                       vpc_id=vpc.id,
                                       tags={'Name': 'pulumi-igw'})

# Create a Route Table
route_table = ec2.RouteTable('route-table',
                              vpc_id=vpc.id,
                              tags={'Name': 'pulumi-rt'})

# Create a default route pointing to the Internet Gateway
route = ec2.Route('route',
                  route_table_id=route_table.id,
                  destination_cidr_block='0.0.0.0/0',
                  gateway_id=internet_gateway.id)

# Create a subnet within the VPC
subnet = ec2.Subnet('subnet',
                    cidr_block='10.0.1.0/24',
                    vpc_id=vpc.id)

# Associate the route table with the subnet
route_table_association = ec2.RouteTableAssociation('route-table-association',
                                                    subnet_id=subnet.id,
                                                    route_table_id=route_table.id)

# Create an IAM role for the EC2 instance
instance_role = iam.Role("instance-role",
                         assume_role_policy=pulumi.Output.from_input(
                             {
                                 "Version": "2012-10-17",
                                 "Statement": [
                                     {
                                         "Action": "sts:AssumeRole",
                                         "Principal": {
                                             "Service": "ec2.amazonaws.com"
                                         },
                                         "Effect": "Allow",
                                         "Sid": ""
                                     }
                                 ]
                             }
                         ))

# Attach the AmazonSSMManagedInstanceCore policy to the IAM role
policy_attachment = iam.RolePolicyAttachment("ssm-policy-attachment",
                                             role=instance_role.name,
                                             policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")

# Create an IAM Instance Profile
instance_profile = iam.InstanceProfile("instance-profile", role=instance_role.name)

# User data to start the web server and set the index page
user_data = """
#!/bin/bash
yum -y update
yum -y install httpd
systemctl enable httpd
systemctl start httpd
echo "Hello, World from Pulumi AI!" > /var/www/html/index.html
"""

ami = ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        ec2.GetAmiFilterArgs(
            name="name",
            values=["amzn2-ami-hvm-*-x86_64-gp2"],
        ),
        ec2.GetAmiFilterArgs(
            name="architecture",
            values=["x86_64"],
        ),
    ],
)

# Create a security group that allows SSH traffic
security_group = ec2.SecurityGroup('sec-group',
                                   vpc_id=vpc.id,
                                   description='Allow SSH traffic',
                                   ingress=[
                                       ec2.SecurityGroupIngressArgs(
                                           protocol='tcp',
                                           from_port=80,
                                           to_port=80,
                                           cidr_blocks=['0.0.0.0/0']
                                    )],
                                    egress=[
                                        ec2.SecurityGroupEgressArgs(
                                            protocol='-1',  # This represents all traffic
                                            from_port=0,  # Use the port range from 0 to 65535
                                            to_port=0,
                                            cidr_blocks=['0.0.0.0/0']  # Allow traffic to all IPv4 CIDRs
                                        )
                                    ],
                                    tags={"Name": "pulumi-sg"}
                                   )

# Create an EC2 instance
instance = ec2.Instance("web-server",
                         ami=ami.id,
                         instance_type="t3.medium",
                         subnet_id=subnet.id,
                         vpc_security_group_ids=[security_group.id],
                         user_data=user_data,
                         iam_instance_profile=instance_profile.name,
                         associate_public_ip_address=True,
                         tags={"Name": "pulumi-instance-web"})

# Export the instance public IP
pulumi.export("instance_public_ip", instance.public_ip)
