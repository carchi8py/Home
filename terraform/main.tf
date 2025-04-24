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

# DynamoDB Table for Steam Game Tracker
resource "aws_dynamodb_table" "steam_game_tracker" {
  name         = "steam_game_tracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "steam_id"
  range_key    = "date"

  attribute {
    name = "steam_id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Name        = "SteamGameTracker"
    Environment = "Production"
    Application = "Gaming Analytics"
  }
}

# IAM Role for the Steam Game Tracker Lambda Function
resource "aws_iam_role" "lambda_steam_game_tracker" {
  name = "lambda_steam_game_tracker_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for DynamoDB Access
resource "aws_iam_policy" "lambda_dynamodb_access" {
  name        = "lambda_steam_game_tracker_dynamodb_access"
  description = "IAM policy for Steam Game Tracker Lambda to access DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.steam_game_tracker.arn
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_policy" "lambda_cloudwatch_access" {
  name        = "lambda_steam_game_tracker_cloudwatch_access"
  description = "IAM policy for Steam Game Tracker Lambda to access CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach the IAM policies to the role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_steam_game_tracker.name
  policy_arn = aws_iam_policy.lambda_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch" {
  role       = aws_iam_role.lambda_steam_game_tracker.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_access.arn
}

# Create a local archive of the Lambda deployment package
data "archive_file" "lambda_steam_game_tracker" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambda_steam_game_tracker/package"
  output_path = "${path.module}/lambda_steam_game_tracker.zip"
}

# Lambda function
resource "aws_lambda_function" "steam_game_tracker" {
  filename      = data.archive_file.lambda_steam_game_tracker.output_path
  function_name = "steam_game_tracker"
  role          = aws_iam_role.lambda_steam_game_tracker.arn
  handler       = "lambda_steam_game_tracker.lambda_handler"
  runtime       = "python3.9"
  timeout       = 60
  memory_size   = 256

  source_code_hash = filebase64sha256(data.archive_file.lambda_steam_game_tracker.output_path)

  environment {
    variables = {
      STEAM_API_KEY    = var.steam_api_key
      STEAM_ID         = var.steam_id
      DYNAMODB_TABLE   = aws_dynamodb_table.steam_game_tracker.name
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_dynamodb,
    aws_iam_role_policy_attachment.lambda_cloudwatch
  ]
}

# CloudWatch Event Rule to schedule Lambda at midnight every day
resource "aws_cloudwatch_event_rule" "midnight_trigger" {
  name                = "midnight-steam-tracker-trigger"
  description         = "Triggers the Steam Game Tracker Lambda function at midnight every day"
  schedule_expression = "cron(0 0 * * ? *)"
}

# CloudWatch Event Target for the Lambda function
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.midnight_trigger.name
  target_id = "steam_game_tracker"
  arn       = aws_lambda_function.steam_game_tracker.arn
}

# Lambda permission to allow CloudWatch Events to invoke the function
resource "aws_lambda_permission" "allow_cloudwatch_steam" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.steam_game_tracker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.midnight_trigger.arn
}