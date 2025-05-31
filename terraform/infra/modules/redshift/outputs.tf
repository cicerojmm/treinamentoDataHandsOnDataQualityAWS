output "redshift_endpoint" {
  description = "Endpoint do cluster Redshift"
  value       = aws_redshift_cluster.redshift.endpoint
}

output "redshift_secret_arn" {
  description = "ARN do segredo armazenado no AWS Secrets Manager"
  value       = aws_secretsmanager_secret.redshift_secret.arn
}
