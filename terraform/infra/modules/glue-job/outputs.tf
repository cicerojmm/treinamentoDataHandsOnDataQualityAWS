output "glue_job_names" {
  description = "Nomes dos jobs do Glue criados"
  value       = { for k, v in aws_glue_job.glue_job : k => v.name }
}

output "glue_job_arns" {
  description = "ARNs dos jobs do Glue criados"
  value       = { for k, v in aws_glue_job.glue_job : k => v.arn }
}

output "glue_job_role_arn" {
  description = "ARN do IAM role usado pelos jobs do Glue"
  value       = aws_iam_role.glue_job_role.arn
}

output "glue_job_role_name" {
  description = "Nome do IAM role usado pelos jobs do Glue"
  value       = aws_iam_role.glue_job_role.name
}