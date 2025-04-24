#!/usr/bin/env python3
import json
import boto3
import requests
from datetime import datetime, timedelta
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Steam API credentials - to be set as Lambda environment variables
API_KEY = os.environ.get('STEAM_API_KEY')
STEAM_ID = os.environ.get('STEAM_ID')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

# DynamoDB table name
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'steam_game_tracker')

def get_recently_played_games(api_key, steam_id):
    """
    Fetch recently played games from the Steam API for a specific user.
    
    Args:
        api_key (str): Steam API key
        steam_id (str): Steam ID of the user
        
    Returns:
        dict: JSON response from the Steam API containing recently played games
    """
    url = "http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
    params = {
        'key': api_key,
        'steamid': steam_id,
        'format': 'json',
        'count': 100  # Maximum number of games to return
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Steam API: {e}")
        return None

def get_previous_data(dynamodb_client, table_name, steam_id, date_str=None):
    """
    Get the previous day's data from DynamoDB
    
    Args:
        dynamodb_client: boto3 DynamoDB client
        table_name (str): DynamoDB table name
        steam_id (str): Steam ID of the user
        date_str (str): Date string in YYYY-MM-DD format. If None, yesterday's date is used.
        
    Returns:
        dict: Previous day's game data or empty dict if not found
    """
    if date_str is None:
        # Default to yesterday
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={
                'steam_id': {'S': steam_id},
                'date': {'S': date_str}
            }
        )
        
        item = response.get('Item')
        if item:
            # Convert DynamoDB format to regular dict
            games = json.loads(item.get('games', {}).get('S', '{}'))
            return games
        return {}
    except Exception as e:
        logger.error(f"Error retrieving data from DynamoDB: {e}")
        return {}

def calculate_daily_playtime(today_data, yesterday_data):
    """
    Calculate how much time was played for each game today
    
    Args:
        today_data (dict): Today's game data with total playtime
        yesterday_data (dict): Yesterday's game data with total playtime
        
    Returns:
        dict: Game playtime for today only
    """
    daily_playtime = {}
    
    # Go through today's games
    for game_id, today_game in today_data.items():
        yesterday_game = yesterday_data.get(game_id, {})
        
        # Calculate playtime difference
        today_minutes = today_game.get('playtime_forever', 0)
        yesterday_minutes = yesterday_game.get('playtime_forever', 0)
        daily_minutes = today_minutes - yesterday_minutes
        
        # Only include games that were played today
        if daily_minutes > 0:
            daily_playtime[game_id] = {
                'app_id': game_id,
                'name': today_game.get('name', f'Unknown Game ({game_id})'),
                'playtime_minutes': daily_minutes,
                'playtime_hours': round(daily_minutes / 60, 2),
                'total_playtime_minutes': today_minutes,
                'total_playtime_hours': round(today_minutes / 60, 2)
            }
    
    return daily_playtime

def process_games_data(games_data):
    """
    Process the API response and convert to a more usable format
    
    Args:
        games_data (dict): Response from Steam API
        
    Returns:
        dict: Processed game data keyed by app_id
    """
    processed_data = {}
    
    if not games_data or 'response' not in games_data:
        logger.warning("No valid data returned from Steam API")
        return processed_data
    
    games = games_data['response'].get('games', [])
    
    for game in games:
        app_id = str(game.get('appid'))  # Convert to string for DynamoDB compatibility
        processed_data[app_id] = {
            'name': game.get('name', f'Unknown Game ({app_id})'),
            'playtime_forever': game.get('playtime_forever', 0),
            'playtime_2weeks': game.get('playtime_2weeks', 0)
        }
    
    return processed_data

def send_slack_notification(webhook_url, message_blocks):
    """
    Send a notification to Slack using the webhook URL
    
    Args:
        webhook_url (str): Slack webhook URL
        message_blocks (list): Message blocks in Slack Block Kit format
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not webhook_url:
        logger.warning("Slack webhook URL not provided, skipping notification")
        return False
        
    payload = {
        "blocks": message_blocks
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info("Slack notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return False

def format_slack_message(daily_playtime, today_str, is_test=False):
    """
    Format a Slack message with daily gameplay statistics
    
    Args:
        daily_playtime (dict): Data about daily gameplay
        today_str (str): Date string in YYYY-MM-DD format
        is_test (bool): Whether this is a test run
        
    Returns:
        list: Formatted message blocks for Slack
    """
    # Sort games by playtime
    sorted_games = sorted(
        daily_playtime.values(),
        key=lambda x: x.get('playtime_minutes', 0),
        reverse=True
    )
    
    # Calculate total playtime
    total_minutes = sum(game.get('playtime_minutes', 0) for game in daily_playtime.values())
    total_hours = round(total_minutes / 60, 2)
    
    # Create header text
    if is_test:
        header_text = f"🎮 *STEAM TRACKER TEST* 🎮"
        subheader = f"Test run on {today_str}"
    else:
        header_text = f"🎮 *STEAM DAILY GAMING REPORT* 🎮"
        subheader = f"Gaming activity for {today_str}"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": subheader
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add summary section
    if len(daily_playtime) > 0:
        summary_text = (
            f"*Total Gaming Time:* {total_hours} hours\n"
            f"*Games Played:* {len(daily_playtime)}\n"
            f"*Most Played:* {sorted_games[0]['name'] if sorted_games else 'None'}"
        )
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary_text
            }
        })
        
        # Add game details section
        game_details = ""
        for i, game in enumerate(sorted_games[:5], 1):
            game_details += f"{i}. *{game['name']}*: {game['playtime_hours']} hours\n"
        
        if game_details:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Games:*\n{game_details}"
                }
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "No games were played during this period."
            }
        })
    
    # Add footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "Steam Game Tracker | Auto-generated report"
            }
        ]
    })
    
    return blocks

def save_to_dynamodb(dynamodb_client, table_name, steam_id, daily_data, raw_data):
    """
    Save the processed game data to DynamoDB
    
    Args:
        dynamodb_client: boto3 DynamoDB client
        table_name (str): DynamoDB table name
        steam_id (str): Steam ID of the user
        daily_data (dict): Processed daily playtime data
        raw_data (dict): Raw processed data from today
        
    Returns:
        bool: True if successful, False otherwise
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Sort games by daily playtime for easier access
        sorted_games = sorted(
            daily_data.values(), 
            key=lambda x: x.get('playtime_minutes', 0),
            reverse=True
        )
        
        # Calculate total playtime across all games
        total_daily_minutes = sum(game.get('playtime_minutes', 0) for game in daily_data.values())
        total_daily_hours = round(total_daily_minutes / 60, 2)
        
        # Create item to store in DynamoDB
        item = {
            'steam_id': {'S': steam_id},
            'date': {'S': today_str},
            'total_daily_minutes': {'N': str(total_daily_minutes)},
            'total_daily_hours': {'N': str(total_daily_hours)},
            'games_count': {'N': str(len(daily_data))},
            'games': {'S': json.dumps(daily_data)},
            'raw_data': {'S': json.dumps(raw_data)},
            'top_game': {'S': sorted_games[0]['name'] if sorted_games else 'None'},
            'timestamp': {'S': datetime.now().isoformat()}
        }
        
        dynamodb_client.put_item(
            TableName=table_name,
            Item=item
        )
        
        logger.info(f"Saved data to DynamoDB for {today_str}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to DynamoDB: {e}")
        return False

def lambda_handler(event, context):
    """
    Main Lambda function handler
    """
    # Check if this is a test run
    is_test = event.get('test', False) if isinstance(event, dict) else False
    
    # Check if required environment variables are set
    if not API_KEY or not STEAM_ID:
        error_msg = "Missing required environment variables: STEAM_API_KEY or STEAM_ID"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }
    
    # Create DynamoDB client
    dynamodb = boto3.client('dynamodb')
    
    # Get today's game data from Steam API
    logger.info(f"Fetching recently played games for Steam ID: {STEAM_ID}")
    games_data = get_recently_played_games(API_KEY, STEAM_ID)
    
    if not games_data:
        error_msg = "Failed to retrieve data from Steam API"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }
    
    # Process today's data
    today_processed_data = process_games_data(games_data)
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if is_test:
        logger.info("Running in test mode - will send Slack notification but skip DynamoDB operations")
        # For test mode, we'll just use the current data as "daily playtime" to show recent activity
        test_playtime = {}
        
        # Convert 2-week playtime to daily playtime for demonstration
        for game_id, game_data in today_processed_data.items():
            playtime_2weeks = game_data.get('playtime_2weeks', 0)
            if playtime_2weeks > 0:
                test_playtime[game_id] = {
                    'app_id': game_id,
                    'name': game_data.get('name', f'Unknown Game ({game_id})'),
                    'playtime_minutes': playtime_2weeks,
                    'playtime_hours': round(playtime_2weeks / 60, 2),
                    'total_playtime_minutes': game_data.get('playtime_forever', 0),
                    'total_playtime_hours': round(game_data.get('playtime_forever', 0) / 60, 2)
                }
        
        # Send test results to Slack
        if SLACK_WEBHOOK_URL:
            message_blocks = format_slack_message(test_playtime, today_str, is_test=True)
            send_slack_notification(SLACK_WEBHOOK_URL, message_blocks)
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Test completed successfully',
                'games_processed': len(today_processed_data),
                'recent_games': len(test_playtime),
                'slack_notification': bool(SLACK_WEBHOOK_URL)
            })
        }
    
    # Standard execution flow for scheduled runs
    # Get yesterday's data from DynamoDB
    yesterday_processed_data = get_previous_data(dynamodb, DYNAMODB_TABLE, STEAM_ID)
    
    # Calculate daily playtime
    daily_playtime = calculate_daily_playtime(today_processed_data, yesterday_processed_data)
    
    # Save today's data to DynamoDB
    success = save_to_dynamodb(
        dynamodb, 
        DYNAMODB_TABLE, 
        STEAM_ID, 
        daily_playtime, 
        today_processed_data
    )
    
    if success:
        # Log a summary of daily playtime
        if daily_playtime:
            sorted_games = sorted(
                daily_playtime.values(), 
                key=lambda x: x.get('playtime_minutes', 0),
                reverse=True
            )
            total_minutes = sum(game.get('playtime_minutes', 0) for game in daily_playtime.values())
            
            logger.info(f"Total playtime today: {round(total_minutes / 60, 2)} hours")
            logger.info(f"Games played today: {len(daily_playtime)}")
            
            # Log top 3 games if available
            for i, game in enumerate(sorted_games[:3], 1):
                logger.info(f"{i}. {game['name']}: {game['playtime_hours']} hours")
            
            # Send daily report to Slack if webhook URL is configured
            if SLACK_WEBHOOK_URL:
                message_blocks = format_slack_message(daily_playtime, today_str)
                send_slack_notification(SLACK_WEBHOOK_URL, message_blocks)
        else:
            logger.info("No games were played today")
            
            # Send "no games played" notification to Slack
            if SLACK_WEBHOOK_URL:
                message_blocks = format_slack_message({}, today_str)
                send_slack_notification(SLACK_WEBHOOK_URL, message_blocks)
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed and saved daily playtime data',
                'games_played': len(daily_playtime),
                'date': today_str,
                'slack_notification': bool(SLACK_WEBHOOK_URL)
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to save data to DynamoDB'})
        }

if __name__ == "__main__":
    # For local testing only
    os.environ['STEAM_API_KEY'] = "YOUR_API_KEY_HERE"
    os.environ['STEAM_ID'] = "YOUR_STEAM_ID_HERE"
    os.environ['SLACK_WEBHOOK_URL'] = "YOUR_SLACK_WEBHOOK_URL_HERE"
    # Test mode - set to True to run a test
    test_event = {"test": True}
    lambda_handler(test_event, None)