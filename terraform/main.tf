provider "aws" {
  region = var.aws_region
}

# Zip the Lambda function with dependencies
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambda_temperature_notification/package"
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
      WEATHER_API_KEY   = var.weather_api_key
      SNS_TOPIC_ARN     = aws_sns_topic.temperature_notification.arn
      DYNAMODB_TABLE    = aws_dynamodb_table.temperature_notification_table.name
      SLACK_WEBHOOK_URL = var.slack_webhook_url
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

# Setup CloudWatch Event Rule to trigger Lambda every 15 minutes
resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "every-15-minutes-temperature-check"
  description         = "Trigger temperature check lambda every 15 minutes"
  schedule_expression = "cron(0/15 * * * ? *)"
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

# ========= LOTO PRICE CHECKER LAMBDA =========
# TEMPORARILY DISABLED - Currently broken and will be fixed later
/*
# Zip the Loto Price Checker Lambda function with dependencies
data "archive_file" "loto_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambda_loto_price_checker/package"
  output_path = "${path.module}/lambda_loto_price_checker.zip"
}

# Create IAM role for Loto Price Checker Lambda
resource "aws_iam_role" "loto_lambda_role" {
  name = "loto_price_checker_lambda_role"

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

# Attach policies to Loto Price Checker Lambda IAM role
resource "aws_iam_role_policy" "loto_lambda_policy" {
  name   = "loto_price_checker_lambda_policy"
  role   = aws_iam_role.loto_lambda_role.id
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
      }
    ]
  })
}

# Create Loto Price Checker Lambda function
resource "aws_lambda_function" "loto_price_checker" {
  function_name    = "loto_price_checker"
  filename         = data.archive_file.loto_lambda_zip.output_path
  source_code_hash = data.archive_file.loto_lambda_zip.output_base64sha256
  role             = aws_iam_role.loto_lambda_role.arn
  handler          = "lambda_loto_price_checker.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30  # Increased timeout for web scraping operations

  environment {
    variables = {
      SLACK_WEBHOOK_URL = var.slack_webhook_url
      API_NINJAS_KEY    = var.api_ninjas_key
    }
  }

  depends_on = [
    aws_iam_role_policy.loto_lambda_policy,
    aws_cloudwatch_log_group.loto_lambda_logs,
  ]
}

# Create CloudWatch Log Group for Loto Price Checker
resource "aws_cloudwatch_log_group" "loto_lambda_logs" {
  name              = "/aws/lambda/loto_price_checker"
  retention_in_days = 14
}

# Setup CloudWatch Event Rule to trigger Loto Price Checker Lambda daily
resource "aws_cloudwatch_event_rule" "daily_loto_check" {
  name                = "daily-loto-price-check"
  description         = "Trigger loto price checker lambda daily"
  schedule_expression = "cron(0 16 ? * * *)"  # Runs at 4:00 PM UTC every day
}

resource "aws_cloudwatch_event_target" "trigger_loto_lambda" {
  rule      = aws_cloudwatch_event_rule.daily_loto_check.name
  target_id = "loto_price_checker"
  arn       = aws_lambda_function.loto_price_checker.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_loto" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.loto_price_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_loto_check.arn
}
*/

# ========= STEAM GAME TRACKER LAMBDA =========
# Resources have been removed to start fresh