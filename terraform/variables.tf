variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-west-1"  # Change this to your preferred region
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