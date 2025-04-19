# GitHub Copilot Instructions

## Project Overview
This project implements a temperature notification system using AWS Lambda. The system checks the current temperature for specified zip codes and sends notifications via SNS when temperatures drop below a threshold.

## Project Structure
- `/src/lambda_temperature_notification/` - Contains the Lambda function source code
- `/terraform/` - Contains Terraform infrastructure as code to deploy resources to AWS

## Key Components

### Lambda Function
- Located in `src/lambda_temperature_notification/lambda_temperature_notification.py`
- Uses OpenWeatherMap API to fetch temperature data
- Checks against notification thresholds stored in DynamoDB
- Sends notifications via SNS when temperature drops below threshold

### Terraform Infrastructure
- Deploys all necessary AWS resources:
  - Lambda function
  - IAM roles and policies
  - DynamoDB table for state management
  - SNS topic for notifications
  - CloudWatch event rules for scheduling
  - CloudWatch log group for monitoring

## Project Rules

1. **AWS Resources**
   - Always use AWS free tier options when creating AWS services
   - Configure all resources to stay within free tier limits when possible
   - Document any services that cannot use free tier with explicit justification

2. **Lambda Development**
   - Always write Lambda functions in Python
   - Target Python 3.9+ runtime for all Lambda functions
   - Include comprehensive error handling in all Lambda code
   - Optimize for cold start performance

3. **Documentation Requirements**
   - Always include detailed comments in all code files
   - Every component (Lambda function, module, etc.) must have a README.md file
   - READMEs should include purpose, configuration, usage examples, and deployment instructions
   - Document all environment variables and configuration parameters

4. **Infrastructure as Code**
   - When creating AWS services, always create Terraform files to set them up
   - Organize Terraform files by service or feature
   - Use variables for all configurable parameters
   - Include proper IAM permissions with least privilege principle
   - Include CloudWatch monitoring and logging for all resources

## Configuration Notes
- Default AWS region is us-east-2 (Ohio) for cost-efficiency
- Lambda runs on an hourly schedule by default
- Required variables:
  - `aws_region`: AWS region for resource deployment
  - `weather_api_key`: OpenWeatherMap API key
  - `notification_email`: Email to receive temperature alerts

## Common Tasks
- To modify the temperature threshold logic: Edit the Lambda function
- To change notification frequency: Update the CloudWatch event rule schedule
- To deploy infrastructure: Use `terraform init`, `terraform plan`, `terraform apply`
- To tear down infrastructure: Use `terraform destroy`