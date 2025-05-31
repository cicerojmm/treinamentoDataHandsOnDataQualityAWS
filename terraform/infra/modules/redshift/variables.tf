variable "cluster_identifier" {
  description = "Nome do cluster Redshift"
  type        = string
}

variable "database_name" {
  description = "Nome do banco de dados dentro do Redshift"
  type        = string
}

variable "master_username" {
  description = "Usuário master do Redshift"
  type        = string
}


variable "node_type" {
  description = "Tipo de instância do Redshift"
  type        = string
  default     = "dc2.large"
}

variable "cluster_type" {
  description = "Tipo de cluster (single-node ou multi-node)"
  type        = string
}

variable "number_of_nodes" {
  description = "Número de nós (somente para multi-node)"
  type        = number
  default     = 2
}

variable "publicly_accessible" {
  description = "O cluster deve ser acessível publicamente?"
  type        = bool
  default     = false
}

variable "subnet_ids" {
  description = "Lista de subnets para o Redshift"
  type        = list(string)
}

variable "vpc_id" {
  description = "ID da VPC"
  type        = string
}

variable "allowed_ips" {
  description = "Lista de IPs permitidos para acesso ao cluster"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
