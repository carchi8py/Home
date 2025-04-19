output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.temperature_notification.arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
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