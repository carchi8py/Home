# Lambda Temperature Notification

This AWS Lambda function sends a text notification when the temperature at ZIP code 95117 goes below 65°F. The function ensures no duplicate notifications are sent unless the temperature rises above 65°F. It runs every 15 minutes using CloudWatch Events.

## How It Works

The Lambda function:
1. Fetches the current temperature from OpenWeatherMap API
2. Checks if the temperature is below the threshold (65°F)
3. Verifies the last notification state in DynamoDB to prevent duplicate alerts
4. Sends notifications via Slack and SNS when conditions are met

## Environment Variables

To configure the Lambda function, the following environment variables are required:

1. **`WEATHER_API_KEY`**: Your API key for OpenWeatherMap.
   - Sign up at [OpenWeatherMap](https://openweathermap.org/) to get an API key.

2. **`SNS_TOPIC_ARN`**: The ARN of the SNS topic used to send notifications.

3. **`DYNAMODB_TABLE`**: The name of the DynamoDB table used to store notification state.

4. **`SLACK_WEBHOOK_URL`**: The webhook URL for sending notifications to Slack.

## Testing the Function

You can test the function by invoking it with a test event that includes the `test` parameter:

```json
{
  "test": true
}
```

When run in test mode, the function will:
- Send a Slack notification regardless of the current temperature
- Clearly mark the message as a test with "[TEST]" prefix
- Include user mentions (@carchi8py) to trigger notifications
- Not affect the normal notification state tracking in DynamoDB

## Manual Setup (Without Terraform)

If you prefer to set up resources manually instead of using Terraform, follow these steps:

### 1. Create the Lambda Function
1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Create a new Lambda function.
3. Upload the `lambda_temperature_notification.py` file with all its dependencies.
4. Set the runtime to **Python 3.9** or later.
5. Configure the environment variables as described above.
6. Set the execution role to include permissions for:
   - **SNS Publish** (to send notifications).
   - **DynamoDB Read/Write** (to store notification state).

### 2. Set Up EventBridge Rule
1. Go to the [AWS EventBridge Console](https://console.aws.amazon.com/events/).
2. Create a new rule.
3. Set the rule to trigger every 15 minutes.
4. Add the Lambda function as the target.

### 3. Set Up SNS Topic
1. Go to the [AWS SNS Console](https://console.aws.amazon.com/sns/).
2. Create a new topic (e.g., `TemperatureAlerts`).
3. Note the topic's ARN and set it as the `SNS_TOPIC_ARN` environment variable in the Lambda function.

## Costs
- **Lambda**: Pay per execution (free tier available)
- **DynamoDB**: Free tier includes 25GB storage and sufficient throughput for this application
- **SNS**: Pay per notification sent
- **CloudWatch Events**: Free for the first million events per month

For more details, refer to the [AWS Pricing Calculator](https://calculator.aws/).