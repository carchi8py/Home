# Lambda Loto Price Checker

This AWS Lambda function checks the current jackpot amounts for Mega Millions and Powerball lotteries. When either jackpot exceeds $250 million, it sends a notification to Slack with details about the lottery jackpot and next drawing date.

## How It Works

The Lambda function:
1. Scrapes the official Mega Millions and Powerball websites to get current jackpot amounts
2. Checks if either jackpot exceeds the threshold ($250 million)
3. Sends a notification to Slack when the threshold is met
4. Includes information about the jackpot amount and next drawing date

## Environment Variables

To configure the Lambda function, the following environment variable is required:

**`SLACK_WEBHOOK_URL`**: The webhook URL for sending notifications to Slack.

## Testing the Function

You can test the function by invoking it with a test event that includes the `test` parameter:

```json
{
  "test": true
}
```

When run in test mode, the function will:
- Send a Slack notification regardless of the actual jackpot amounts
- Clearly mark the message as a test with "[TEST]" prefix
- Include user mentions (@carchi8py) to trigger notifications

## Schedule

The function is configured to run once per day at 4:00 PM UTC (which is 9:00 AM PST / 12:00 PM EST). This schedule ensures you're notified in time to purchase a ticket when the jackpot is high.

## Manual Setup (Without Terraform)

If you prefer to set up resources manually instead of using Terraform, follow these steps:

### 1. Create the Lambda Function
1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Create a new Lambda function
3. Upload the `lambda_loto_price_checker.py` file with the following dependencies:
   - BeautifulSoup4
   - Requests
4. Set the runtime to **Python 3.9** or later
5. Configure the SLACK_WEBHOOK_URL environment variable
6. Set the timeout to 30 seconds (needed for web scraping)
7. Set the execution role to include permissions for:
   - CloudWatch Logs

### 2. Set Up EventBridge Rule
1. Go to the [AWS EventBridge Console](https://console.aws.amazon.com/events/)
2. Create a new rule
3. Set the rule to trigger daily (cron expression: `0 16 ? * * *`)
4. Add the Lambda function as the target

## Notes on Web Scraping

This function relies on web scraping to get lottery jackpot information. If the website structure of the official lottery sites changes, the selectors in the function may need to be updated:

- For Mega Millions: The function looks for `.jackpot-amount` class
- For Powerball: The function looks for `.current-jackpot` class

## Costs

- **Lambda**: Pay per execution (free tier available), running once per day
- **CloudWatch Events**: Free for the first million events per month

For more details, refer to the [AWS Pricing Calculator](https://calculator.aws/).