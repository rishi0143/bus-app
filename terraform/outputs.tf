output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "private_subnet_1_id" {
  value = aws_subnet.private1.id
}

output "private_subnet_2_id" {
  value = aws_subnet.private2.id
}

output "ec2_public_ip" {
  value = aws_instance.bus_server.public_ip
}

output "ec2_public_dns" {
  value = aws_instance.bus_server.public_dns
}

output "rds_endpoint" {
  value = aws_db_instance.mysql.address
}

output "rds_port" {
  value = aws_db_instance.mysql.port
}

output "database_name" {
  value = aws_db_instance.mysql.db_name
}