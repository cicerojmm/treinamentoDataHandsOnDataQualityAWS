#terraform apply -var-file=envs/develop.tfvars -auto-approve
#terraform init -backend-config="backends/develop.hcl"

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

###############################################################################
#########             VPC E SUBNETS                               #############
###############################################################################
module "vpc_public" {
  source                = "./modules/vpc"
  project_name          = "data-handson-mds"
  vpc_name              = "data-handson-mds-vpc-${var.environment}"
  vpc_cidr              = "10.0.0.0/16"
  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs  = ["10.0.3.0/24", "10.0.4.0/24"]
  availability_zones    = ["us-east-2a", "us-east-2b"]
}

###############################################################################
#########             REDSHIFT                                    #############
###############################################################################
module "redshift" {
  source              = "./modules/redshift"

  cluster_identifier  = "data-handson-mds"
  database_name       = "datahandsonmds"
  master_username     = "admin"
  node_type           = "ra3.large"
  cluster_type        = "single-node"
  number_of_nodes     = 1
  publicly_accessible = true
  subnet_ids          = module.vpc_public.public_subnet_ids
  vpc_id              = module.vpc_public.vpc_id
  allowed_ips         = ["0.0.0.0/0"]
}

##############################################################################
########             INSTANCIAS EC2                              #############
##############################################################################
module "ec2_instance" {
  source             =  "./modules/ec2"
  ami_id              = "ami-04b4f1a9cf54c11d0"
  instance_type       = "t3a.2xlarge"
  subnet_id           = module.vpc_public.public_subnet_ids[0]
  vpc_id              = module.vpc_public.vpc_id
  key_name            = "cjmm-datahandson-cb"
  associate_public_ip = true
  instance_name       = "data-handson-mds-ec2-${var.environment}"
  
  user_data = templatefile("${path.module}/scripts/bootstrap/ec2_bootstrap.sh", {})

  ingress_rules = [
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}


##############################################################################
########             AIRFLOW - MWAA                              #############
##############################################################################
module "mwaa" {
  source                = "./modules/mwaa"
  environment_name      = "datahandson-mds-mwaa"
  s3_bucket_arn         = "arn:aws:s3:::cjmm-mds-lake-mwaa"
  airflow_version       = "2.10.3"
  environment_class     = "mw1.small"
  min_workers           = 1
  max_workers           = 2
  webserver_access_mode = "PUBLIC_ONLY"
}

###############################################################################
#########            GLUE JOBS                                   #############
###############################################################################
module "glue_jobs_soda" {
  source = "./modules/glue-job"

  project_name      = "data-handson-dq-soda"
  environment       = var.environment
  region            = var.region
  s3_bucket_scripts = var.s3_bucket_scripts
  s3_bucket_data    = var.s3_bucket_raw
  scripts_local_path = "scripts/glue_etl/soda"
  
  job_scripts = {
    "data-hands-on-dq-soda-tests-amazonsales" = "data-hands-on-dq-soda-tests-amazonsales.py",
    "data-hands-on-dq-soda-tests-amazonsales-obt" = "data-hands-on-dq-soda-tests-amazonsales-obt.py",
  }
  
  worker_type       = "G.1X"
  number_of_workers = 3
  timeout           = 60
  max_retries       = 1
  
  additional_python_modules = "soda-core-spark-df,delta-spark==3.2.1,python-dotenv"
  
  additional_arguments = {
    "--enable-glue-datacatalog" = "true"
    "--conf"                    = "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.delta.logStore.class=org.apache.spark.sql.delta.storage.S3SingleDriverLogStore"
    "--datalake-formats"        = "delta"
  }
}

module "glue_jobs_gx" {
  source = "./modules/glue-job"

  project_name      = "data-handson-dq-gx"
  environment       = var.environment
  region            = var.region
  s3_bucket_scripts = var.s3_bucket_scripts
  s3_bucket_data    = var.s3_bucket_raw
  scripts_local_path = "scripts/glue_etl/great_expectations"
  
  job_scripts = {
    "data-hands-on-dq-amazonsales-gx-tests" = "data-hands-on-dq-amazonsales-gx-tests.py",
    "data-hands-on-dq-gx-tests-amazonsales-obt" = "data-hands-on-dq-gx-tests-amazonsales-obt.py",
  }
  
  worker_type       = "G.1X"
  number_of_workers = 3
  timeout           = 60
  max_retries       = 1
  
  additional_python_modules = "great_expectations[spark]==0.16.5,delta-spark==3.2.1"
  
  additional_arguments = {
    "--enable-glue-datacatalog" = "true"
    "--conf"                    = "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.delta.logStore.class=org.apache.spark.sql.delta.storage.S3SingleDriverLogStore"
    "--datalake-formats"        = "delta"
  }
}

module "glue_jobs_dgq" {
  source = "./modules/glue-job"

  project_name      = "data-handson-dq-gdq"
  environment       = var.environment
  region            = var.region
  s3_bucket_scripts = var.s3_bucket_scripts
  s3_bucket_data    = var.s3_bucket_raw
  scripts_local_path = "scripts/glue_etl/glue_data_quality"
  
  job_scripts = {
    "data-hands-on-dq-amazonsales-dw-table-stg" = "data-hands-on-dq-amazonsales-dw-table-stg.py",
    "data-hands-on-dq-amazonsales-dw-dim-product" = "data-hands-on-dq-amazonsales-dw-dim-product.py",
    "data-hands-on-dq-amazonsales-dw-dim-rating" = "data-hands-on-dq-amazonsales-dw-dim-rating.py",
    "data-hands-on-dq-amazonsales-dw-dim-user" = "data-hands-on-dq-amazonsales-dw-dim-user.py",
    "data-hands-on-dq-amazonsales-dw-dims-gdq" = "data-hands-on-dq-amazonsales-dw-dims-gdq.py",
    "data-hands-on-dq-amazonsales-dw-fact-product-rating" = "data-hands-on-dq-amazonsales-dw-fact-product-rating.py",
    "data-hands-on-dq-amazonsales-dw-fact-sales-category" = "data-hands-on-dq-amazonsales-dw-fact-sales-category.py",
    "data-hands-on-dq-amazonsales-dw-facts-gdq" = "data-hands-on-dq-amazonsales-dw-facts-gdq.py",
  }
  
  worker_type       = "G.1X"
  number_of_workers = 3
  timeout           = 60
  max_retries       = 1
  
  additional_python_modules = "delta-spark==3.2.1"
  
  additional_arguments = {
    "--enable-glue-datacatalog" = "true"
    "--conf"                    = "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.delta.logStore.class=org.apache.spark.sql.delta.storage.S3SingleDriverLogStore"
    "--datalake-formats"        = "delta"
  }
}

module "glue_jobs_gdq_s3tables" {
  source = "./modules/glue-job"

  project_name      = "data-handson-dq-s3-tablesgdq"
  environment       = var.environment
  region            = var.region
  s3_bucket_scripts = var.s3_bucket_scripts
  s3_bucket_data    = var.s3_bucket_raw
  scripts_local_path = "scripts/glue_etl/glue_data_quality_s3tables"
  
  job_scripts = {
    "data-hands-on-dq-amazonsales-dw-table-stg-s3tables" = "data-hands-on-dq-amazonsales-dw-table-stg-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-dim-product-s3tables" = "data-hands-on-dq-amazonsales-dw-dim-product-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-dim-rating-s3tables" = "data-hands-on-dq-amazonsales-dw-dim-rating-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-dim-user-s3tables" = "data-hands-on-dq-amazonsales-dw-dim-user-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-dims-s3tables-gdq" = "data-hands-on-dq-amazonsales-dw-dims-s3tables-gdq.py",
    "data-hands-on-dq-amazonsales-dw-fact-product-rating-s3tables" = "data-hands-on-dq-amazonsales-dw-fact-product-rating-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-fact-sales-category-s3tables" = "data-hands-on-dq-amazonsales-dw-fact-sales-category-s3tables.py",
    "data-hands-on-dq-amazonsales-dw-facts-s3tables-gdq" = "data-hands-on-dq-amazonsales-dw-facts-s3tables-gdq.py",
  }
  
  worker_type       = "G.1X"
  number_of_workers = 3
  timeout           = 60
  max_retries       = 0
  
  extra_jars = "s3://cjmm-mds-lake-configs/jars/s3-tables-catalog-for-iceberg-0.1.7.jar"

  
  additional_arguments = {
    "--enable-glue-datacatalog" = "true"
    "--user-jars-first"         = "true"
    "--datalake-formats"        = "iceberg"
  }
}

###############################################################################
#########            GLUE CRAWLER                                #############
###############################################################################
module "glue_crawler_data_quality_results" {
  source = "./modules/glue-crawler"

  name_prefix    = "data-handson-dq"
  environment    = var.environment
  database_name  = "data_quality_results"
  s3_target_path = "s3://${var.s3_bucket_curated}/mds_data_quality_results/"
  
  # Optional: Configure a schedule for the crawler
  #crawler_schedule = "cron(0 1 * * ? *)"  # Runs daily at 1:00 AM UTC
  
  # Optional: Prefix for the tables created by the crawler
  table_prefix   = "dq_"
}

###############################################################################
#########            LAMBDA FUNCTIONS                            #############
###############################################################################
module "lambda_alert_dataquality" {
  source = "./modules/lambda"

  project_name    = "data-handson-dq"
  environment     = var.environment
  function_name   = "alert-dataquality-sqs-discord"
  description     = "Lambda function to send data quality alerts from SNS to Discord"
  handler         = "alert-dataquality-sqs-discord.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 128
  source_code_file = "alert-dataquality-sqs-discord.py"
  
  environment_variables = {
    DISCORD_WEBHOOK_URL = ""
  }
  
  # Subscribe to the SNS topic
  sns_topic_arn = module.sns_data_quality_alerts.sns_topic_arn
}

module "lambda_glue_dq_error_handler" {
  source = "./modules/lambda"

  project_name    = "data-handson-dq"
  environment     = var.environment
  function_name   = "glue-dq-error-handler"
  description     = "Lambda function to handle Glue Data Quality error events"
  handler         = "glue-dq-error-handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 128
  source_code_file = "glue-dq-error-handler.py"
  
  environment_variables = {
    SNS_TOPIC_ARN = module.sns_data_quality_alerts.sns_topic_arn
  }
  
  # Add permissions to publish to SNS
  additional_policy_arns = ["arn:aws:iam::aws:policy/AmazonSNSFullAccess"]
}

###############################################################################
#########            EVENTBRIDGE RULES                           #############
###############################################################################
module "eventbridge_glue_dq_errors" {
  source = "./modules/eventbridge"

  project_name    = "data-handson-dq"
  environment     = var.environment
  rule_name       = "glue-dq-errors"
  description     = "Capture Glue Data Quality error events"
  
  event_pattern   = jsonencode({
    source      = ["aws.glue-dataquality"]
    detail-type = ["Data Quality Evaluation Results Available"]
    detail      = {
      state    = ["FAILED"]
    }
  })
  
  target_lambda_arn  = module.lambda_glue_dq_error_handler.lambda_function_arn
  target_lambda_name = module.lambda_glue_dq_error_handler.lambda_function_name
}

###############################################################################
#########            SNS TOPICS                                  #############
###############################################################################
module "sns_data_quality_alerts" {
  source = "./modules/sns"

  project_name    = "data-handson-dq"
  environment     = var.environment
  topic_name      = "data-handson-dq-alerts"
  display_name    = "Data Quality Alerts"
  
  # Allow all accounts in your organization to publish to this topic
  publisher_principals = ["*"]
}

###############################################################################
#########            STEP FUNCTIONS                               #############
###############################################################################
module "step_functions" {
  source = "./modules/step-functions"

  project_name = "data-handson-dq"
  environment  = var.environment
  region       = var.region
  
  # Definições das máquinas de estado
  state_machines = {
    "datahandson-dq-amazonsales-soda" = {
      definition_file = "sfn_definition_soda.json"
      type            = "STANDARD"
    },
    "datahandson-dq-amazonsales-gx" = {
      definition_file = "sfn_definition_gx.json"
      type            = "STANDARD"
    },
    "datahandson-dq-amazonsales-gdq" = {
      definition_file = "sfn_definition_gdq.json"
      type            = "STANDARD"
    },
    "datahandson-dq-amazonsales-s3tables-gdq" = {
      definition_file = "sfn_definition_s3tables_gdq.json"
      type            = "STANDARD"
    }
  }
  
  # Permissões adicionais para o Step Functions
  additional_iam_statements = [
    {
      Effect = "Allow"
      Action = [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:BatchStopJobRun"
      ]
      Resource = "*"
    }
  ]
  
  # Anexar políticas gerenciadas
  attach_glue_policy = true
  
  # Configurações de logging
  log_retention_days = 30
  include_execution_data = true
  logging_level = "ALL"
}