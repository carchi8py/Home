import boto3
import requests
import json
import os
import time
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    # Check if this is a test invocation
    is_test = event.get('test', False)
    
    # Configuration
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
    THRESHOLD_AMOUNT = 250  # $250 million
    
    # Initialize clients if using AWS services
    sns = boto3.client('sns')
    
    try:
        # Get lottery data
        mega_millions_data = get_mega_millions_data()
        powerball_data = get_powerball_data()
        
        print(f"Mega Millions jackpot: ${mega_millions_data['jackpot']} million")
        print(f"Powerball jackpot: ${powerball_data['jackpot']} million")
        
        notifications = []
        
        # Check Mega Millions threshold
        if mega_millions_data['jackpot'] >= THRESHOLD_AMOUNT or is_test:
            notifications.append({
                "name": "Mega Millions",
                "jackpot": mega_millions_data['jackpot'],
                "date": mega_millions_data['date']
            })
        
        # Check Powerball threshold
        if powerball_data['jackpot'] >= THRESHOLD_AMOUNT or is_test:
            notifications.append({
                "name": "Powerball",
                "jackpot": powerball_data['jackpot'],
                "date": powerball_data['date']
            })
        
        # Send notifications if any jackpots are above threshold
        if notifications:
            send_slack_notification(SLACK_WEBHOOK_URL, notifications, is_test)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mega_millions': mega_millions_data,
                'powerball': powerball_data,
                'notifications_sent': len(notifications) > 0,
                'is_test': is_test
            })
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'is_test': is_test
            })
        }

def get_mega_millions_data():
    """Scrapes Mega Millions jackpot data from their website"""
    url = "https://www.megamillions.com/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract jackpot amount (this selector might need adjusting based on website structure)
        jackpot_text = soup.select_one('.jackpot-amount').text.strip()
        
        # Clean up the amount and convert to number
        amount_str = jackpot_text.replace('$', '').replace(' Million', '').strip()
        jackpot_amount = float(amount_str)
        
        # Get next drawing date
        date_elem = soup.select_one('.next-drawing-date')
        drawing_date = date_elem.text.strip() if date_elem else "Next drawing date not found"
        
        return {
            "jackpot": jackpot_amount,
            "date": drawing_date
        }
    
    except Exception as e:
        print(f"Error getting Mega Millions data: {str(e)}")
        # Return a fallback value when there's an error
        return {
            "jackpot": 0,
            "date": "Unknown (Error occurred)"
        }

def get_powerball_data():
    """Scrapes Powerball jackpot data from their website"""
    url = "https://www.powerball.com/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract jackpot amount (this selector might need adjusting based on website structure)
        jackpot_text = soup.select_one('.current-jackpot').text.strip()
        
        # Clean up the amount and convert to number
        amount_str = jackpot_text.replace('$', '').replace(' Million', '').strip()
        jackpot_amount = float(amount_str)
        
        # Get next drawing date
        date_elem = soup.select_one('.next-drawing-date')
        drawing_date = date_elem.text.strip() if date_elem else "Next drawing date not found"
        
        return {
            "jackpot": jackpot_amount,
            "date": drawing_date
        }
    
    except Exception as e:
        print(f"Error getting Powerball data: {str(e)}")
        # Return a fallback value when there's an error
        return {
            "jackpot": 0,
            "date": "Unknown (Error occurred)"
        }

def send_slack_notification(webhook_url, notifications, is_test=False):
    """Sends notification to Slack webhook"""
    if not webhook_url:
        print("No Slack webhook URL provided")
        return
    
    message_prefix = "[TEST] " if is_test else ""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{message_prefix}🎰 Big Lottery Jackpot Alert!",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@carchi8py> The following lotteries have jackpots over $250 million:"
            }
        }
    ]
    
    for notification in notifications:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{notification['name']}*: ${notification['jackpot']} million\nNext drawing: {notification['date']}"
            }
        })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Consider buying a ticket! 🍀"
        }
    })
    
    if is_test:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*This is a test notification.* Normal threshold rules have been bypassed."
                }
            ]
        })
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"_Notification sent by AWS Lambda at {time.strftime('%Y-%m-%d %H:%M:%S')}_"
            }
        ]
    })
    
    slack_message = {
        "blocks": blocks
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(slack_message),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print("Successfully sent notification to Slack")
    except Exception as e:
        print(f"Failed to send Slack notification: {str(e)}")