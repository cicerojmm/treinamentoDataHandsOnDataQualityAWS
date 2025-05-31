resource "aws_iam_role" "glue_job_role" {
  name = "${var.project_name}-glue-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "glue_job_policy" {
  name        = "${var.project_name}-glue-job-policy"
  description = "Policy for Glue Jobs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:AssociateKmsKey"
        ]
        Resource = [
          "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/jobs/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:*"
        ]
        Resource = [
          "*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3tables:*"
        ]
        Resource = [
          "*"
        ]
      }

    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_job_policy_attachment" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_service_policy_attachment" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_s3_object" "glue_script" {
  for_each = var.job_scripts

  bucket = var.s3_bucket_scripts
  key    = "glue_jobs_scripts/${each.key}/${each.value}"
  source = "${var.scripts_local_path}/${each.value}"
  etag   = filemd5("${var.scripts_local_path}/${each.value}")
}

resource "aws_glue_job" "glue_job" {
  for_each = var.job_scripts

  name              = "${each.key}"
  role_arn          = aws_iam_role.glue_job_role.arn
  glue_version      = "5.0"  # Usando a versão 5.0 do Glue para PySpark
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers
  timeout           = var.timeout
  max_retries       = var.max_retries

  command {
    name            = "glueetl"
    script_location = "s3://${var.s3_bucket_scripts}/glue_jobs_scripts/${each.key}/${each.value}"
    python_version  = "3"
  }

  default_arguments = merge({
    "--enable-glue-datacatalog"       = "true"
    "--enable-spark-ui"               = "true"
    "--spark-event-logs-path"         = "s3://${var.s3_bucket_scripts}/spark-logs/"
    "--enable-metrics"                = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--job-language"                  = "python"
    "--TempDir"                       = "s3://${var.s3_bucket_scripts}/glue_jobs_temp/"
    "--enable-auto-scaling"           = "true"
    "--conf"                          = "spark.sql.legacy.timeParserPolicy=LEGACY"
    "--extra-py-files"                = var.extra_py_files
    "--additional-python-modules"     = var.additional_python_modules
    "--extra-jars"                    = var.extra_jars != "" ? var.extra_jars : null
  }, var.additional_arguments)

  execution_property {
    max_concurrent_runs = var.max_concurrent_runs
  }

}

data "aws_caller_identity" "current" {}