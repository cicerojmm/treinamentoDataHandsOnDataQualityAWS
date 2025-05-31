variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

variable "description" {
  description = "Description of the EventBridge rule"
  type        = string
  default     = ""
}

variable "event_pattern" {
  description = "Event pattern for the EventBridge rule in JSON format"
  type        = string
}

variable "target_lambda_arn" {
  description = "ARN of the Lambda function to target"
  type        = string
}

variable "target_lambda_name" {
  description = "Name of the Lambda function to target"
  type        = string
}