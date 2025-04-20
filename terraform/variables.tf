variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-2"  # Using Ohio region as preferred in tfvars
}

variable "weather_api_key" {
  description = "API key for OpenWeatherMap"
  type        = string
  sensitive   = true
}

variable "notification_email" {
  description = "Email address to receive temperature notifications"
  type        = string
}

variable "slack_webhook_url" {
  description = "Webhook URL for Slack notifications"
  type        = string
  sensitive   = true
  default     = "https://hooks.slack.com/services/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"
}