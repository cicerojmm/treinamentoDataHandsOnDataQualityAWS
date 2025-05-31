
variable "environment_name" {
  description = "Nome do ambiente para uso em tags e identificadores"
  type        = string
  default     = "mwaa-environment"
}

variable "s3_bucket_arn" {
  description = "ARN do bucket S3 para armazenar DAGs"
  type        = string
}

variable "airflow_version" {
  description = "Versão do Apache Airflow"
  type        = string
  default     = "2.5.1"
}

variable "environment_class" {
  description = "Classe do ambiente MWAA"
  type        = string
  default     = "mw1.medium"
}

variable "min_workers" {
  description = "Número mínimo de workers"
  type        = number
  default     = 1
}

variable "max_workers" {
  description = "Número máximo de workers"
  type        = number
  default     = 5
}

variable "webserver_access_mode" {
  description = "Modo de acesso ao WebServer"
  type        = string
  default     = "PUBLIC_ONLY"
}

variable "vpc_cidr" {
  description = "CIDR block para a VPC"
  type        = string
  default     = "10.192.0.0/16"
}

variable "public_subnet_1_cidr" {
  description = "CIDR block para a primeira subnet pública"
  type        = string
  default     = "10.192.10.0/24"
}

variable "public_subnet_2_cidr" {
  description = "CIDR block para a segunda subnet pública"
  type        = string
  default     = "10.192.11.0/24"
}

variable "private_subnet_1_cidr" {
  description = "CIDR block para a primeira subnet privada"
  type        = string
  default     = "10.192.20.0/24"
}

variable "private_subnet_2_cidr" {
  description = "CIDR block para a segunda subnet privada"
  type        = string
  default     = "10.192.21.0/24"
}