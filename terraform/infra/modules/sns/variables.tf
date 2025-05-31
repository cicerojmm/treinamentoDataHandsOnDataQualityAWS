variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string
}

variable "display_name" {
  description = "Display name of the SNS topic"
  type        = string
  default     = ""
}

variable "publisher_principals" {
  description = "List of AWS principals allowed to publish to the SNS topic"
  type        = list(string)
  default     = ["*"]
}