
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.37"

  # EKS Cluster Configuration
  cluster_name    = "gobus-eks-cluster"
  cluster_version = "1.34"

  # Existing VPC
  vpc_id = aws_vpc.main.id

  # Existing Private Subnets
  subnet_ids = [
    aws_subnet.private1.id,
    aws_subnet.private2.id
  ]

  # Cluster API Access
  cluster_endpoint_public_access       = true
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access_cidrs = [var.ssh_cidr]

  enable_cluster_creator_admin_permissions = true

  # EKS Addons
  cluster_addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni    = {}
  }

  # EKS Worker Nodes
  eks_managed_node_groups = {
    gobus_nodes = {
      name           = "gobus-worker-nodes"
      instance_types = ["t3.small"]
      capacity_type  = "ON_DEMAND"

      # Existing Public Subnets
      subnet_ids = [
        aws_subnet.public.id,
        aws_subnet.public_subnet_2.id
      ]

      min_size     = 2
      max_size     = 4
      desired_size = 2
    }
  }

  tags = {
    Project     = "GoBus"
    Environment = "Dev"
  }
}

# Allow EKS Worker Nodes to access RDS MySQL
resource "aws_security_group_rule" "eks_to_rds" {
  type = "ingress"

  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = module.eks.node_security_group_id

  from_port = 3306
  to_port   = 3306
  protocol  = "tcp"

  description = "Allow EKS worker nodes to access RDS"
}
