output "instance_id" {
  description = "ID of the created EC2 instance"
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Public IP of the created EC2 instance"
  value       = aws_instance.this.public_ip
}

output "private_ip" {
  description = "Private IP of the created EC2 instance"
  value       = aws_instance.this.private_ip
}

output "security_group_id" {
  description = "ID of the created Security Group"
  value       = aws_security_group.this.id
}
