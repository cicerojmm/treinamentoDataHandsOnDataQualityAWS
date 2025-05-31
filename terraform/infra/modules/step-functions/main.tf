resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "step_functions_policy" {
  name        = "${var.project_name}-step-functions-policy"
  description = "Policy for Step Functions state machine"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ], var.additional_iam_statements)
  })
}

resource "aws_iam_role_policy_attachment" "step_functions_policy_attachment" {
  role       = aws_iam_role.step_functions_role.name
  policy_arn = aws_iam_policy.step_functions_policy.arn
}

# Adicionar políticas gerenciadas conforme necessário
resource "aws_iam_role_policy_attachment" "lambda_execution_attachment" {
  count      = var.attach_lambda_policy ? 1 : 0
  role       = aws_iam_role.step_functions_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

resource "aws_iam_role_policy_attachment" "glue_execution_attachment" {
  count      = var.attach_glue_policy ? 1 : 0
  role       = aws_iam_role.step_functions_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Ler a definição do Step Functions a partir de um arquivo JSON
data "local_file" "step_functions_definition" {
  for_each = var.state_machines
  filename = "${var.definitions_path}/${each.value.definition_file}"
}

# Substituir variáveis na definição do Step Functions
locals {
  state_machine_definitions = {
    for name, config in var.state_machines : name => replace(
      replace(
        replace(
          replace(
            data.local_file.step_functions_definition[name].content,
            "{{account_id}}", data.aws_caller_identity.current.account_id
          ),
          "{{region}}", var.region
        ),
        "{{project_name}}", var.project_name
      ),
      "{{environment}}", var.environment
    )
  }
}

# Criar o Step Functions State Machine
resource "aws_sfn_state_machine" "state_machine" {
  for_each     = var.state_machines
  name         = "${each.key}"
  role_arn     = aws_iam_role.step_functions_role.arn
  definition   = local.state_machine_definitions[each.key]
  type         = each.value.type

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions_log_group[each.key].arn}:*"
    include_execution_data = var.include_execution_data
    level                  = var.logging_level
  }

}

# Criar grupo de logs para o Step Functions
resource "aws_cloudwatch_log_group" "step_functions_log_group" {
  for_each          = var.state_machines
  name              = "/aws/states/${var.project_name}-${each.key}"
  retention_in_days = var.log_retention_days

}

data "aws_caller_identity" "current" {}