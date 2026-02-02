# TODO: Test EC2 resources for aws-tagger
# Events to test: RunInstances, CreateVolume, CreateSecurityGroup, CreateVpc, CreateSubnet, CreateSnapshot, CreateImage, AllocateAddress

# EC2 Instance
resource "aws_instance" "test" {
  ami           = local.ec2.ami
  instance_type = local.ec2.instance_type

  subnet_id = aws_subnet.main.id

  tags = {
    Name = "${local.name_prefix}-ec2-instance"
  }
}

# EBS Volume
resource "aws_ebs_volume" "test" {
  availability_zone = data.aws_availability_zones.available.names[0]
  size              = local.ec2.volume_size
  type              = "gp3"

  tags = {
    Name = "${local.name_prefix}-ebs-volume"
  }
}

# Security Group
resource "aws_security_group" "test" {
  name_prefix = "${local.name_prefix}-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-security-group"
  }
}

# Subnet (replacing the one in ec2.tf since it's now in vpc.tf)
# Using the main subnet from vpc.tf

# EBS Snapshot
resource "aws_ebs_snapshot" "test" {
  volume_id = aws_ebs_volume.test.id

  tags = {
    Name = "${local.name_prefix}-snapshot"
  }
}

# Elastic IP
resource "aws_eip" "test" {
  domain = "vpc"

  tags = {
    Name = "${local.name_prefix}-eip"
  }
}
