provider "aws" {
  region = var.aws_region
}

# Zip the Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/lambda_temperature_notification/lambda_temperature_notification.py"
  output_path = "${path.module}/lambda_temperature_notification.zip"
}

# Create IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "temperature_notification_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policies to IAM role
resource "aws_iam_role_policy" "lambda_policy" {
  name   = "temperature_notification_lambda_policy"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ],
        Resource = aws_dynamodb_table.temperature_notification_table.arn
      },
      {
        Effect = "Allow",
        Action = [
          "sns:Publish"
        ],
        Resource = aws_sns_topic.temperature_notification.arn
      }
    ]
  })
}

# Create Lambda function
resource "aws_lambda_function" "temperature_notification" {
  function_name    = "temperature_notification"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_temperature_notification.lambda_handler"
  runtime          = "python3.9"
  timeout          = 10

  environment {
    variables = {
      WEATHER_API_KEY = var.weather_api_key
      SNS_TOPIC_ARN   = aws_sns_topic.temperature_notification.arn
      DYNAMODB_TABLE  = aws_dynamodb_table.temperature_notification_table.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# Create CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/temperature_notification"
  retention_in_days = 14
}

# Create SNS Topic for notifications
resource "aws_sns_topic" "temperature_notification" {
  name = "temperature-notifications"
}

# Create SNS subscription for email
resource "aws_sns_topic_subscription" "temperature_email_subscription" {
  topic_arn = aws_sns_topic.temperature_notification.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Create DynamoDB table for storing temperature notification state
resource "aws_dynamodb_table" "temperature_notification_table" {
  name           = "temperature-notification-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "zip_code"
  
  attribute {
    name = "zip_code"
    type = "S"
  }

  tags = {
    Name = "Temperature Notification State"
  }
}

# Setup CloudWatch Event Rule to trigger Lambda on a schedule (every hour)
resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "hourly-temperature-check"
  description         = "Trigger temperature check lambda hourly"
  schedule_expression = "cron(0 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.hourly.name
  target_id = "temperature_notification"
  arn       = aws_lambda_function.temperature_notification.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.temperature_notification.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly.arn
}