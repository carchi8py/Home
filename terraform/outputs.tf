output "lambda_function_arn" {
  description = "The ARN of the Temperature Notification Lambda function"
  value       = aws_lambda_function.temperature_notification.arn
}

output "lambda_function_name" {
  description = "The name of the Temperature Notification Lambda function"
  value       = aws_lambda_function.temperature_notification.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for temperature notification state"
  value       = aws_dynamodb_table.temperature_notification_table.name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for temperature notifications"
  value       = aws_sns_topic.temperature_notification.arn
}

# Loto Price Checker Outputs
output "loto_lambda_function_arn" {
  description = "The ARN of the Loto Price Checker Lambda function"
  value       = aws_lambda_function.loto_price_checker.arn
}

output "loto_lambda_function_name" {
  description = "The name of the Loto Price Checker Lambda function"
  value       = aws_lambda_function.loto_price_checker.function_name
}

output "loto_cloudwatch_schedule" {
  description = "The schedule expression for the Loto Price Checker Lambda function"
  value       = aws_cloudwatch_event_rule.daily_loto_check.schedule_expression
}