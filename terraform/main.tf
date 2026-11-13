# VPC

resource "aws_vpc" "main" {

  cidr_block = var.vpc_cidr

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway

resource "aws_internet_gateway" "igw" {

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnet

resource "aws_subnet" "public" {

  vpc_id = aws_vpc.main.id

  cidr_block = var.public_subnet_cidr

  availability_zone = "ap-south-1a"

  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# Private Subnet 1

resource "aws_subnet" "private1" {

  vpc_id = aws_vpc.main.id

  cidr_block = var.private_subnet_1_cidr

  availability_zone = "ap-south-1a"

  tags = {
    Name = "${var.project_name}-private-subnet-1"
  }
}

# Private Subnet 2

resource "aws_subnet" "private2" {

  vpc_id = aws_vpc.main.id

  cidr_block = var.private_subnet_2_cidr

  availability_zone = "ap-south-1b"

  tags = {
    Name = "${var.project_name}-private-subnet-2"
  }
}

# Public Route Table

resource "aws_route_table" "public" {

  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"

    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Public Route Table Association

resource "aws_route_table_association" "public_assoc" {

  subnet_id = aws_subnet.public.id

  route_table_id = aws_route_table.public.id
}

# Private Route Table

resource "aws_route_table" "private" {

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

# Private Subnet Associations

resource "aws_route_table_association" "private1_assoc" {

  subnet_id = aws_subnet.private1.id

  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private2_assoc" {

  subnet_id = aws_subnet.private2.id

  route_table_id = aws_route_table.private.id
}

# Ubuntu AMI

data "aws_ami" "ubuntu" {

  most_recent = true

  owners = ["099720109477"]

  filter {
    name = "name"

    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name = "virtualization-type"

    values = ["hvm"]
  }
}

# EC2 Instance

resource "aws_instance" "bus_server" {

  ami = data.aws_ami.ubuntu.id

  instance_type = var.instance_type

  subnet_id = aws_subnet.public.id

  vpc_security_group_ids = [
    aws_security_group.ec2_sg.id
  ]

  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git
  EOF

  tags = {
    Name = "${var.project_name}-ec2"
  }
}