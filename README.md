# Lambda Temperature Notification

This project contains an AWS Lambda function that sends a text notification when the temperature at ZIP code 95117 goes below 65°F. The function ensures no duplicate notifications are sent unless the temperature rises above 65°F. It runs hourly using CloudWatch Events.

## Project Structure
- `/src/lambda_temperature_notification/` - Contains the Lambda function source code
- `/terraform/` - Contains Terraform infrastructure as code to deploy resources to AWS

## Environment Variables
To configure the Lambda function, set the following environment variables:

1. **`WEATHER_API_KEY`**: Your API key for the weather service (e.g., OpenWeatherMap).
   - Sign up at [OpenWeatherMap](https://openweathermap.org/) to get an API key.

2. **`SNS_TOPIC_ARN`**: The ARN of the SNS topic used to send notifications.

3. **`DYNAMODB_TABLE`**: The name of the DynamoDB table used to store notification state.

## Terraform Deployment

This project uses Terraform to automate the deployment of all required AWS resources. The Terraform configuration creates:

1. **Lambda Function**: Deploys the temperature notification function with all required dependencies
2. **IAM Role**: Sets up appropriate permissions for the Lambda function
3. **DynamoDB Table**: Creates a table to store notification state
4. **SNS Topic**: Sets up notifications for temperature alerts
5. **CloudWatch Event Rule**: Configures the Lambda to run on an hourly schedule
6. **CloudWatch Log Group**: Sets up logging for the Lambda function

### Steps to Deploy with Terraform

1. **Configure Variables**
   - Update `/terraform/terraform.tfvars` with your specific values:
     ```
     aws_region        = "us-east-2"  # Region for deployment
     weather_api_key   = "your-api-key"  # OpenWeatherMap API key 
     notification_email = "your-email@example.com"  # Email for notifications
     ```

2. **Initialize Terraform**
   ```
   cd terraform
   terraform init
   ```

3. **Preview Changes**
   ```
   terraform plan
   ```

4. **Apply Configuration**
   ```
   terraform apply
   ```

5. **Confirm SNS Subscription**
   - Check your email and confirm the SNS subscription to receive notifications

### Cleanup Resources
To remove all AWS resources created by this project:
```
cd terraform
terraform destroy
```

## Manual Setup (Alternative to Terraform)

If you prefer to set up resources manually instead of using Terraform, follow these steps:

### 1. Create the Lambda Function
1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Create a new Lambda function.
3. Upload the `lambda_temperature_notification.py` file as the function code.
4. Set the runtime to **Python 3.9** or later.
5. Configure the environment variables as described above.
6. Set the execution role to include permissions for:
   - **SNS Publish** (to send notifications).
   - **DynamoDB Read/Write** (to store notification state).

### 2. Set Up EventBridge Rule
1. Go to the [AWS EventBridge Console](https://console.aws.amazon.com/events/).
2. Create a new rule.
3. Set the rule to trigger every hour.
4. Add the Lambda function as the target.

### 3. Set Up SNS Topic
1. Go to the [AWS SNS Console](https://console.aws.amazon.com/sns/).
2. Create a new topic (e.g., `TemperatureAlerts`).
3. Subscribe your phone number to the topic.
4. Note the topic's ARN and set it as the `SNS_TOPIC_ARN` environment variable in the Lambda function.

## Costs
- **Lambda**: Pay per execution (free tier available)
- **DynamoDB**: Free tier includes 25GB storage and sufficient throughput for this application
- **SNS**: Pay per notification sent
- **CloudWatch Events**: Free for the first million events per month

For more details, refer to the [AWS Pricing Calculator](https://calculator.aws/).
