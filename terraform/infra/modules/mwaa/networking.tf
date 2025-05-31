data "aws_availability_zones" "available" {}

resource "aws_vpc" "mwaa_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

}

# Internet Gateway para acesso à internet
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.mwaa_vpc.id

}

# Subnets públicas em duas AZs
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.mwaa_vpc.id
  cidr_block              = var.public_subnet_1_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.mwaa_vpc.id
  cidr_block              = var.public_subnet_2_cidr
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

}

# Subnets privadas em duas AZs (necessárias para MWAA)
resource "aws_subnet" "private_1" {
  vpc_id                  = aws_vpc.mwaa_vpc.id
  cidr_block              = var.private_subnet_1_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = false

}

resource "aws_subnet" "private_2" {
  vpc_id                  = aws_vpc.mwaa_vpc.id
  cidr_block              = var.private_subnet_2_cidr
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = false

}

# Elastic IPs para os NAT Gateways
resource "aws_eip" "nat_1" {
  domain = "vpc"
  
}

resource "aws_eip" "nat_2" {
  domain = "vpc"

}

# NAT Gateways para permitir que as subnets privadas acessem a internet
resource "aws_nat_gateway" "nat_1" {
  allocation_id = aws_eip.nat_1.id
  subnet_id     = aws_subnet.public_1.id

  depends_on = [aws_internet_gateway.igw]
}

resource "aws_nat_gateway" "nat_2" {
  allocation_id = aws_eip.nat_2.id
  subnet_id     = aws_subnet.public_2.id


  depends_on = [aws_internet_gateway.igw]
}

# Tabela de rotas para subnets públicas
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.mwaa_vpc.id

}

resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

# Associações de tabelas de rotas para subnets públicas
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# Tabelas de rotas para subnets privadas
resource "aws_route_table" "private_1" {
  vpc_id = aws_vpc.mwaa_vpc.id
}

resource "aws_route" "private_1_nat" {
  route_table_id         = aws_route_table.private_1.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_1.id
}

resource "aws_route_table" "private_2" {
  vpc_id = aws_vpc.mwaa_vpc.id
}

resource "aws_route" "private_2_nat" {
  route_table_id         = aws_route_table.private_2.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_2.id
}

# Associações de tabelas de rotas para subnets privadas
resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private_1.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private_2.id
}

# Endpoints VPC para serviços AWS (necessários para MWAA)
resource "aws_security_group" "vpc_endpoints_sg" {
  name        = "${var.environment_name}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.mwaa_vpc.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

# Endpoints VPC necessários para MWAA
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.mwaa_vpc.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private_1.id, aws_route_table.private_2.id]

}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "monitoring" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.monitoring"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

}

resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

}

# Adicionar endpoint para o serviço MWAA
resource "aws_vpc_endpoint" "airflow_api" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.airflow.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "airflow_env" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.airflow.env"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

}

resource "aws_vpc_endpoint" "airflow_ops" {
  vpc_id              = aws_vpc.mwaa_vpc.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.airflow.ops"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]
  private_dns_enabled = true

}

# Obter a região atual
data "aws_region" "current" {}