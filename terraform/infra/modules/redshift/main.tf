# Gerando uma senha aleatória para o Redshift
resource "random_password" "redshift_password" {
  length           = 16
  special          = false
  min_numeric      = 1
  min_upper        = 1
  min_lower        = 1
  override_special = "!@#%^&*()-_=+[]{}<>?"
}

# Criando um segredo no AWS Secrets Manager
resource "aws_secretsmanager_secret" "redshift_secret" {
  name = "${var.cluster_identifier}-redshift-credentials"
}

# Armazenando a senha gerada no Secrets Manager
resource "aws_secretsmanager_secret_version" "redshift_secret_version" {
  secret_id     = aws_secretsmanager_secret.redshift_secret.id
  secret_string = jsonencode({
    username = var.master_username
    password = random_password.redshift_password.result
    host     = aws_redshift_cluster.redshift.endpoint
    port     = 5439
    dbname   = var.database_name
  })
}

#security
resource "aws_security_group" "redshift_sg" {
  name_prefix = "${var.cluster_identifier}-redshift-sg"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = var.allowed_ips
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

resource "aws_redshift_subnet_group" "redshift_subnet_group" {
  name       = "${var.cluster_identifier}-redshift-subnet-group"
  description = "Subnet group for Redshift cluster"
  
  subnet_ids = var.subnet_ids

}


#Cluster
resource "aws_redshift_cluster" "redshift" {
  cluster_identifier        = var.cluster_identifier
  database_name             = var.database_name
  master_username           = var.master_username
  master_password           = random_password.redshift_password.result
  node_type                 = var.node_type
  cluster_type              = var.cluster_type
  number_of_nodes           = var.cluster_type == "multi-node" ? var.number_of_nodes : null
  publicly_accessible       = var.publicly_accessible
  encrypted                 = true
  skip_final_snapshot       = true
  vpc_security_group_ids    = [aws_security_group.redshift_sg.id]
  cluster_subnet_group_name = aws_redshift_subnet_group.redshift_subnet_group.name
}

