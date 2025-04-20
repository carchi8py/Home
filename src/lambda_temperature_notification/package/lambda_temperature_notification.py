import boto3
import requests
import json
import os
import time
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    # Check if this is a test invocation
    is_test = event.get('test', False)
    
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

    # Logic for sending notification
    should_send = (current_temp < TEMPERATURE_THRESHOLD and not last_notified_below) or is_test

    if should_send:
        # Prepare Slack message
        message_prefix = "[TEST] " if is_test else ""
        slack_message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{message_prefix}🌡️ Temperature Alert!",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@carchi8py> The current temperature in ZIP code *{ZIP_CODE}* is *{current_temp}°F*" + 
                               (f", which is below the threshold of {TEMPERATURE_THRESHOLD}°F." if current_temp < TEMPERATURE_THRESHOLD else ".")
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Notification sent by AWS Lambda {message_prefix}at {time.strftime('%Y-%m-%d %H:%M:%S')}_"
                        }
                    ]
                }
            ]
        }
        
        # Add test information if this is a test
        if is_test:
            slack_message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*This is a test notification.* <@carchi8py> Normal temperature threshold rules have been bypassed."
                }
            })
        
        # Send to Slack directly
        try:
            slack_response = requests.post(
                SLACK_WEBHOOK_URL,
                data=json.dumps(slack_message),
                headers={'Content-Type': 'application/json'}
            )
            slack_response.raise_for_status()
            print("Successfully sent notification to Slack")
        except Exception as e:
            print(f"Failed to send Slack notification: {str(e)}")
        
        # Also publish to SNS for redundancy
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps({
                "default": f"{message_prefix}Temperature alert! @carchi8py The current temperature in {ZIP_CODE} is {current_temp}°F" +
                         (f", which is below {TEMPERATURE_THRESHOLD}°F." if current_temp < TEMPERATURE_THRESHOLD else ".")
            }),
            MessageStructure='json'
        )
        
        # Only update state in DynamoDB for real (non-test) notifications
        if not is_test and current_temp < TEMPERATURE_THRESHOLD:
            table.put_item(Item={'zip_code': ZIP_CODE, 'notified_below': True})
    
    # Update state to allow future notifications if temperature rises above threshold
    elif current_temp >= TEMPERATURE_THRESHOLD and last_notified_below:
        table.put_item(Item={'zip_code': ZIP_CODE, 'notified_below': False})

    return {
        'statusCode': 200,
        'body': f"{'[TEST] ' if is_test else ''}Checked temperature: {current_temp}°F",
        'is_test': is_test,
        'sent_notification': should_send
    }