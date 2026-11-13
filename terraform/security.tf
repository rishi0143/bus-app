# EC2 Security Group

resource "aws_security_group" "ec2_sg" {

  name = "${var.project_name}-ec2-sg"

  description = "Allow SSH and Flask access"

  vpc_id = aws_vpc.main.id

  # SSH

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [var.ssh_cidr]
  }

  # Flask Application

  ingress {
    from_port = 5000
    to_port   = 5000
    protocol  = "tcp"

    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound Traffic

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}


# RDS Security Group

resource "aws_security_group" "rds_sg" {

  name = "${var.project_name}-rds-sg"

  description = "Allow MySQL from EC2 only"

  vpc_id = aws_vpc.main.id

  ingress {

    from_port = 3306

    to_port = 3306

    protocol = "tcp"

    security_groups = [
      aws_security_group.ec2_sg.id
    ]
  }

  egress {

    from_port = 0

    to_port = 0

    protocol = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}