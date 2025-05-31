output "state_machine_arns" {
  description = "ARNs das máquinas de estado do Step Functions criadas"
  value       = { for name, machine in aws_sfn_state_machine.state_machine : name => machine.arn }
}

output "state_machine_names" {
  description = "Nomes das máquinas de estado do Step Functions criadas"
  value       = { for name, machine in aws_sfn_state_machine.state_machine : name => machine.name }
}

output "step_functions_role_arn" {
  description = "ARN do IAM role usado pelo Step Functions"
  value       = aws_iam_role.step_functions_role.arn
}

output "step_functions_role_name" {
  description = "Nome do IAM role usado pelo Step Functions"
  value       = aws_iam_role.step_functions_role.name
}

output "log_group_arns" {
  description = "ARNs dos grupos de log do CloudWatch criados para o Step Functions"
  value       = { for name, log_group in aws_cloudwatch_log_group.step_functions_log_group : name => log_group.arn }
}