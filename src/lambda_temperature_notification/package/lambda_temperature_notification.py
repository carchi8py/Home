import boto3
import requests
import json
import os
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    # Configuration
    WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
    SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
    DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
    SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
    ZIP_CODE = "95117"
    TEMPERATURE_THRESHOLD = 65

    # Initialize clients
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    sns = boto3.client('sns')

    # Fetch current temperature
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?zip={ZIP_CODE},us&units=imperial&appid={WEATHER_API_KEY}"
    response = requests.get(weather_url)
    weather_data = response.json()
    current_temp = weather_data['main']['temp']

    # Check last notification state in DynamoDB
    state = table.get_item(Key={'zip_code': ZIP_CODE})
    last_notified_below = state.get('Item', {}).get('notified_below', False)

    if current_temp < TEMPERATURE_THRESHOLD:
        if not last_notified_below:
            # Prepare Slack message
            slack_message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🌡️ Temperature Alert!",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"The current temperature in ZIP code *{ZIP_CODE}* is *{current_temp}°F*, which is below the threshold of {TEMPERATURE_THRESHOLD}°F."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_Notification sent by AWS Lambda at {weather_data.get('dt', 'N/A')}_"
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack directly
            try:
                slack_response = requests.post(
                    SLACK_WEBHOOK_URL,
                    data=json.dumps(slack_message),
                    headers={'Content-Type': 'application/json'}
                )
                slack_response.raise_for_status()
            except Exception as e:
                print(f"Failed to send Slack notification: {str(e)}")
            
            # Also publish to SNS for redundancy
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({
                    "default": f"Temperature alert! The current temperature in {ZIP_CODE} is {current_temp}°F, which is below {TEMPERATURE_THRESHOLD}°F.",
                }),
                MessageStructure='json'
            )
            
            # Update state in DynamoDB
            table.put_item(Item={'zip_code': ZIP_CODE, 'notified_below': True})
    else:
        if last_notified_below:
            # Update state in DynamoDB to allow future notifications
            table.put_item(Item={'zip_code': ZIP_CODE, 'notified_below': False})

    return {
        'statusCode': 200,
        'body': f"Checked temperature: {current_temp}°F"
    }