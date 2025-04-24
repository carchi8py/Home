import boto3
import requests
import json
import os
import time

def lambda_handler(event, context):
    # Check if this is a test invocation
    is_test = event.get('test', False)
    
    # Configuration
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
    API_KEY = os.environ.get('API_NINJAS_KEY')
    THRESHOLD_AMOUNT = 250  # $250 million
    
    if not API_KEY and not is_test:
        print("No API key provided for API-Ninjas. Set the 'API_NINJAS_KEY' environment variable.")
    
    try:
        # Get lottery data from API
        mega_millions_data = get_mega_millions_data(API_KEY)
        powerball_data = get_powerball_data(API_KEY)
        
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

def get_mega_millions_data(api_key=None):
    """Gets Mega Millions jackpot data using API-Ninjas Lottery API"""
    if api_key:
        try:
            url = "https://api.api-ninjas.com/v1/lottery?name=mega_millions"
            headers = {"X-Api-Key": api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                lottery_data = data[0]
                
                # Extract jackpot amount in millions
                # The API returns the jackpot amount as a string like "$325 Million"
                jackpot_text = lottery_data.get("jackpot", "$0")
                amount_str = jackpot_text.replace("$", "").replace(" Million", "").strip()
                try:
                    jackpot_amount = float(amount_str)
                except ValueError:
                    jackpot_amount = 0
                
                # Get next drawing date
                next_drawing = lottery_data.get("next_drawing_date", "Next drawing date not found")
                
                return {
                    "jackpot": jackpot_amount,
                    "date": next_drawing
                }
        except Exception as e:
            print(f"Error getting Mega Millions data from API: {str(e)}")
    
    # Fallback to basic data if API fails or no API key
    print("Using fallback data for Mega Millions")
    today = time.strftime("%Y-%m-%d")
    
    # Fallback to check on the official website
    try:
        fallback_url = "https://www.megamillions.com/"
        response = requests.get(fallback_url, timeout=5)
        if "jackpot" in response.text.lower() and "$" in response.text:
            # Just attempt to extract amount with basic scraping as last resort
            text = response.text
            jackpot_index = text.lower().find("jackpot")
            if jackpot_index > 0:
                # Look for $ within 100 chars of "jackpot"
                amount_section = text[jackpot_index:jackpot_index+100]
                dollars_index = amount_section.find("$")
                if dollars_index > 0:
                    amount_text = amount_section[dollars_index:dollars_index+15]
                    # Extract only digits
                    digits = ''.join(c for c in amount_text if c.isdigit() or c == '.')
                    if digits and len(digits) > 0:
                        try:
                            return {
                                "jackpot": float(digits),
                                "date": today
                            }
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Fallback attempt failed: {str(e)}")
    
    return {
        "jackpot": 0,
        "date": today
    }

def get_powerball_data(api_key=None):
    """Gets Powerball jackpot data using API-Ninjas Lottery API"""
    if api_key:
        try:
            url = "https://api.api-ninjas.com/v1/lottery?name=powerball"
            headers = {"X-Api-Key": api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                lottery_data = data[0]
                
                # Extract jackpot amount in millions
                jackpot_text = lottery_data.get("jackpot", "$0")
                amount_str = jackpot_text.replace("$", "").replace(" Million", "").strip()
                try:
                    jackpot_amount = float(amount_str)
                except ValueError:
                    jackpot_amount = 0
                
                # Get next drawing date
                next_drawing = lottery_data.get("next_drawing_date", "Next drawing date not found")
                
                return {
                    "jackpot": jackpot_amount,
                    "date": next_drawing
                }
        except Exception as e:
            print(f"Error getting Powerball data from API: {str(e)}")
    
    # Fallback to basic data if API fails or no API key
    print("Using fallback data for Powerball")
    today = time.strftime("%Y-%m-%d")
    
    # Fallback to check on the official website
    try:
        fallback_url = "https://www.powerball.com/"
        response = requests.get(fallback_url, timeout=5)
        if "jackpot" in response.text.lower() and "$" in response.text:
            # Just attempt to extract amount with basic scraping as last resort
            text = response.text
            jackpot_index = text.lower().find("jackpot")
            if jackpot_index > 0:
                # Look for $ within 100 chars of "jackpot"
                amount_section = text[jackpot_index:jackpot_index+100]
                dollars_index = amount_section.find("$")
                if dollars_index > 0:
                    amount_text = amount_section[dollars_index:dollars_index+15]
                    # Extract only digits
                    digits = ''.join(c for c in amount_text if c.isdigit() or c == '.')
                    if digits and len(digits) > 0:
                        try:
                            return {
                                "jackpot": float(digits),
                                "date": today
                            }
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Fallback attempt failed: {str(e)}")
    
    return {
        "jackpot": 0,
        "date": today
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