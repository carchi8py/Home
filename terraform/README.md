# Temperature Notification Lambda Terraform Configuration

This directory contains Terraform configuration files to deploy the temperature notification Lambda function and all required AWS resources.

## Resources Created

- Lambda function for temperature notifications
- IAM role with necessary permissions for the Lambda
- DynamoDB table to store notification state
- SNS topic for sending notifications
- CloudWatch Event Rule to trigger the Lambda on a schedule
- CloudWatch Log Group for Lambda logs

## Prerequisites

1. AWS CLI installed and configured
2. Terraform installed
3. OpenWeatherMap API key

## Deployment Instructions

1. Create a `terraform.tfvars` file with your configuration values:

```
aws_region        = "us-west-1"  # Change to your preferred region
weather_api_key   = "your-openweathermap-api-key"
notification_email = "your-email@example.com"
```

2. Initialize Terraform:
```
terraform init
```

3. Review the planned changes:
```
terraform plan
```

4. Apply the configuration:
```
terraform apply
```

5. Confirm the SNS subscription by clicking the link in the email you receive.

## Customization

You can modify `variables.tf` to add additional configuration options or change defaults.

The Lambda function gets triggered hourly by default. To change the schedule, modify the `schedule_expression` in the `aws_cloudwatch_event_rule` resource in `main.tf`.

## Cleanup

To remove all created resources:
```
terraform destroy
```