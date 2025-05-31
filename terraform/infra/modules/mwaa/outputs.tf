output "mwaa_environment_arn" {
  description = "ARN do ambiente MWAA"
  value       = aws_mwaa_environment.mwaa_env.arn
}

output "mwaa_webserver_url" {
  description = "URL do webserver do Airflow"
  value       = aws_mwaa_environment.mwaa_env.webserver_url
}

output "mwaa_security_group_id" {
  description = "ID do security group do MWAA"
  value       = aws_security_group.mwaa_sg.id
}

output "vpc_id" {
  description = "ID da VPC criada para MWAA"
  value       = aws_vpc.mwaa_vpc.id
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas para MWAA"
  value       = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "nat_gateway_ips" {
  description = "IPs públicos dos NAT Gateways"
  value       = [aws_eip.nat_1.public_ip, aws_eip.nat_2.public_ip]
}