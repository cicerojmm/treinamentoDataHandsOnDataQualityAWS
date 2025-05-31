resource "aws_glue_crawler" "this" {
  name          = "${var.name_prefix}-crawler-${var.environment}"
  database_name = var.database_name
  role          = aws_iam_role.glue_crawler_role.arn
  
  s3_target {
    path = var.s3_target_path
  }
  
  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
  
  schedule       = var.crawler_schedule
  table_prefix   = var.table_prefix
}