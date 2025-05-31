resource "aws_security_group" "mwaa_sg" {
  name_prefix = "mwaa-sg-"
  description = "Security Group para MWAA"
  vpc_id      = aws_vpc.mwaa_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Permitir tráfego interno entre os componentes do MWAA
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Permitir acesso ao webserver quando o modo é PUBLIC_ONLY
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS access to webserver"
  }
}

resource "aws_iam_role" "mwaa_role" {
  name = "MWAA-Execution-Role-${var.environment_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "airflow-env.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "mwaa_execution_policy" {
  name        = "MWAA-Execution-Policy-${var.environment_name}"
  description = "Política de execução para o ambiente MWAA"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "airflow:PublishMetrics"
        ]
        Resource = [
          "arn:aws:airflow:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:environment/${var.environment_name}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*",
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${split(":", var.s3_bucket_arn)[5]}",
          "arn:aws:s3:::${split(":", var.s3_bucket_arn)[5]}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:CreateLogGroup",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:GetLogRecord",
          "logs:GetLogGroupFields",
          "logs:GetQueryResults",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:DescribeSubscriptionFilters"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ChangeMessageVisibility",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
          "sqs:SendMessage",
          "sqs:CreateQueue",
          "sqs:ListQueues"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey*",
          "kms:Encrypt"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "mwaa_custom_policy" {
  name        = "MWAA-Custom-Policy-${var.environment_name}"
  description = "Permissões personalizadas para MWAA acessar S3, EMR e Glue"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "glue:*"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = [
          "elasticmapreduce:ListInstances",
          "elasticmapreduce:DescribeCluster",
          "elasticmapreduce:ListSteps",
          "elasticmapreduce:AddJobFlowSteps",
          "elasticmapreduce:RunJobFlow",
          "elasticmapreduce:TerminateJobFlows"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = [
          "iam:PassRole"
        ]
        Resource = ["*"]
        Condition = {
          StringLike = {
            "iam:PassedToService": [
              "glue.amazonaws.com",
              "airflow.amazonaws.com",
              "airflow-env.amazonaws.com",
              "elasticmapreduce.amazonaws.com"
            ]
          }
        }
      }
    ]
  })
}

# Anexar políticas ao role do MWAA
resource "aws_iam_role_policy_attachment" "mwaa_execution_policy_attachment" {
  policy_arn = aws_iam_policy.mwaa_execution_policy.arn
  role       = aws_iam_role.mwaa_role.name
}

resource "aws_iam_role_policy_attachment" "mwaa_custom_policy_attachment" {
  policy_arn = aws_iam_policy.mwaa_custom_policy.arn
  role       = aws_iam_role.mwaa_role.name
}

# Anexar política gerenciada para CloudWatch Logs
resource "aws_iam_role_policy_attachment" "mwaa_cloudwatch_logs_policy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  role       = aws_iam_role.mwaa_role.name
}

# Anexar política gerenciada para Amazon S3 FullAccess
resource "aws_iam_role_policy_attachment" "mwaa_s3_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.mwaa_role.name
}

# Obter a identidade da conta atual
data "aws_caller_identity" "current" {}

resource "aws_mwaa_environment" "mwaa_env" {
  name                   = var.environment_name
  airflow_version        = var.airflow_version
  environment_class      = var.environment_class
  execution_role_arn     = aws_iam_role.mwaa_role.arn
  source_bucket_arn      = var.s3_bucket_arn
  dag_s3_path            = "dags/"
  requirements_s3_path   = "requirements/requirements.txt"
  startup_script_s3_path = "requirements/startup-script.sh"
  min_workers            = var.min_workers
  max_workers            = var.max_workers
  webserver_access_mode  = var.webserver_access_mode

  network_configuration {
    security_group_ids = [aws_security_group.mwaa_sg.id]
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  }

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "INFO"
    }
    scheduler_logs {
      enabled   = true
      log_level = "INFO"
    }
    task_logs {
      enabled   = true
      log_level = "INFO"
    }
    webserver_logs {
      enabled   = true
      log_level = "INFO"
    }
    worker_logs {
      enabled   = true
      log_level = "INFO"
    }
  }

  # Aguardar a criação dos endpoints VPC necessários
  depends_on = [
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ecr_api,
    aws_vpc_endpoint.ecr_dkr,
    aws_vpc_endpoint.logs,
    aws_vpc_endpoint.monitoring,
    aws_vpc_endpoint.sqs
  ]
}