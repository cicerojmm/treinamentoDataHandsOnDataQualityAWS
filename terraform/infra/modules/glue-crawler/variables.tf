variable "name_prefix" {
  description = "Prefix for the crawler name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue database where tables will be created"
  type        = string
}

variable "s3_target_path" {
  description = "S3 path to crawl (e.g., s3://bucket-name/prefix/)"
  type        = string
}

variable "crawler_schedule" {
  description = "Cron expression for crawler schedule"
  type        = string
  default     = null
}

variable "table_prefix" {
  description = "Prefix for the tables created by the crawler"
  type        = string
  default     = ""
}