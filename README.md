# Lambda Temperature Notification

This project contains an AWS Lambda function that sends a text notification when the temperature at ZIP code 95117 goes below 65°F. The function ensures no duplicate notifications are sent unless the temperature rises above 65°F. It runs every 10 minutes using EventBridge.

## Environment Variables
To configure the Lambda function, set the following environment variables:

1. **`WEATHER_API_KEY`**: Your API key for the weather service (e.g., OpenWeatherMap).
   - Sign up at [OpenWeatherMap](https://openweathermap.org/) to get an API key.

2. **`SNS_TOPIC_ARN`**: The ARN of the SNS topic used to send notifications.
   - Create an SNS topic in AWS and subscribe your phone number to it.

## Steps to Set Up the Lambda Function

### 1. Create the Lambda Function
1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Create a new Lambda function.
3. Upload the `lambda_temperature_notification.py` file as the function code.
4. Set the runtime to **Python 3.9** or later.
5. Configure the environment variables as described above.
6. Set the execution role to include permissions for:
   - **SNS Publish** (to send notifications).
   - **S3 Read/Write** (if using S3 for state storage).

### 2. Set Up EventBridge Rule
1. Go to the [AWS EventBridge Console](https://console.aws.amazon.com/events/).
2. Create a new rule.
3. Set the rule to trigger every 10 minutes.
4. Add the Lambda function as the target.

### 3. Set Up SNS Topic
1. Go to the [AWS SNS Console](https://console.aws.amazon.com/sns/).
2. Create a new topic (e.g., `TemperatureAlerts`).
3. Subscribe your phone number to the topic.
4. Note the topic's ARN and set it as the `SNS_TOPIC_ARN` environment variable in the Lambda function.

## Optional: Using S3 for State Storage
If you prefer to use S3 for storing the notification state:
1. Create an S3 bucket.
2. Update the Lambda function code to use S3 for state storage.
3. Grant the Lambda execution role permissions to read/write to the S3 bucket.

## Testing the Function
1. Manually invoke the Lambda function from the AWS Lambda Console.
2. Verify that the notification is sent when the temperature is below 65°F.
3. Check that no duplicate notifications are sent unless the temperature rises above 65°F.

## Costs
- **Lambda**: Pay per execution (free tier available).
- **SNS**: Pay per notification sent.
- **EventBridge**: Free for the first 1 million events per month.
- **S3 (if used)**: Minimal cost for storage and requests.

For more details, refer to the [AWS Pricing Calculator](https://calculator.aws/).
