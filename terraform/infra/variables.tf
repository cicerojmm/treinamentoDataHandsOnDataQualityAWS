variable "environment" {
  description = "Ambiente de implantação (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-2"
}

variable "s3_bucket_raw" {
  description = "Nome do bucket S3 para armazenar dados brutos"
  type        = string
}

variable "s3_bucket_scripts" {
  description = "Nome do bucket S3 para armazenar scripts"
  type        = string
}

variable "s3_bucket_curated" {
  description = "Nome do bucket S3 para armazenar dados processados"
  type        = string
  default     = ""
}

variable "discord_webhook_url" {
  description = "Discord webhook URL for data quality alerts"
  type        = string
  default     = "https://discord.com/api/webhooks/1354503644946628769/bjvMnt1ZpcsMTt67nAe_vFwK6A1yVq6p0sUNRxNJNK1TJz8Gd4WgSxCAQHRToCf1itIj"
  sensitive   = true
}

variable "data_quality_alerts_sns_topic_arn" {
  description = "ARN of the SNS topic for data quality alerts"
  type        = string
  default     = ""
}