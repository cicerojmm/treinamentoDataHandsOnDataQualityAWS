output "crawler_name" {
  description = "Name of the created Glue crawler"
  value       = aws_glue_crawler.this.name
}

output "crawler_arn" {
  description = "ARN of the created Glue crawler"
  value       = aws_glue_crawler.this.arn
}

output "crawler_role_arn" {
  description = "ARN of the IAM role used by the Glue crawler"
  value       = aws_iam_role.glue_crawler_role.arn
}