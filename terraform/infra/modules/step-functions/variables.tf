variable "project_name" {
  description = "Nome do projeto para uso em tags e identificadores"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-2"
}

variable "definitions_path" {
  description = "Caminho para o diretório contendo as definições JSON do Step Functions"
  type        = string
  default     = "scripts/step-functions-definitions"
}

variable "state_machines" {
  description = "Mapa de máquinas de estado a serem criadas"
  type = map(object({
    definition_file = string
    type            = string
  }))
}

variable "additional_iam_statements" {
  description = "Declarações IAM adicionais para a política do Step Functions"
  type        = list(any)
  default     = []
}

variable "attach_lambda_policy" {
  description = "Se deve anexar a política de execução do Lambda ao role do Step Functions"
  type        = bool
  default     = false
}

variable "attach_glue_policy" {
  description = "Se deve anexar a política de execução do Glue ao role do Step Functions"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "Número de dias para reter os logs do CloudWatch"
  type        = number
  default     = 14
}

variable "include_execution_data" {
  description = "Se deve incluir dados de execução nos logs"
  type        = bool
  default     = true
}

variable "logging_level" {
  description = "Nível de logging para o Step Functions"
  type        = string
  default     = "ALL"
}