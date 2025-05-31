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
  default     = "us-east-1"
}

variable "s3_bucket_scripts" {
  description = "Nome do bucket S3 onde os scripts do Glue serão armazenados"
  type        = string
}

variable "s3_bucket_data" {
  description = "Nome do bucket S3 onde os dados de entrada/saída serão armazenados"
  type        = string
}

variable "scripts_local_path" {
  description = "Caminho local onde os scripts do Glue estão armazenados"
  type        = string
  default     = "scripts"
}

variable "job_scripts" {
  description = "Mapa de scripts do Glue no formato {nome_job = nome_arquivo_script}"
  type        = map(string)
}

variable "worker_type" {
  description = "Tipo de worker do Glue (G.1X, G.2X, etc.)"
  type        = string
  default     = "G.1X"
}

variable "number_of_workers" {
  description = "Número de workers para o job do Glue"
  type        = number
  default     = 2
}

variable "timeout" {
  description = "Timeout do job em minutos"
  type        = number
  default     = 60
}

variable "max_retries" {
  description = "Número máximo de tentativas em caso de falha"
  type        = number
  default     = 0
}

variable "max_concurrent_runs" {
  description = "Número máximo de execuções concorrentes"
  type        = number
  default     = 5
}

variable "additional_python_modules" {
  description = "Lista de módulos Python adicionais para instalar, separados por vírgula"
  type        = string
  default     = "pandas==1.5.3"
}

variable "extra_py_files" {
  description = "Arquivos Python extras para incluir no job"
  type        = string
  default     = ""
}

variable "extra_jars" {
  description = "Arquivos JAR extras para incluir no job (caminho S3)"
  type        = string
  default     = ""
}

variable "additional_arguments" {
  description = "Argumentos adicionais para o job do Glue"
  type        = map(string)
  default     = {}
}