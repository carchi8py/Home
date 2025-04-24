# Steam Game Tracker Lambda

This AWS Lambda function tracks your Steam gaming activity daily. It runs at midnight, compares yesterday's playtime with today's playtime for each game, and stores the daily playtime data in a DynamoDB table.

## Features

- Automatically runs at midnight every day
- Fetches recently played games from the Steam API
- Calculates how many hours were played for each game during the past day
- Stores daily gaming statistics in DynamoDB for historical tracking
- Identifies which games were played each day and for how long
- Handles cases where games are played for the first time

## Prerequisites

- AWS Account
- Steam API Key (get one [here](https://steamcommunity.com/dev/apikey))
- Your Steam ID (find it using [SteamID.io](https://steamid.io/))

## Setup

### DynamoDB Table

Create a DynamoDB table with the following schema:

- Table name: `steam_game_tracker` (configurable via environment variable)
- Partition key: `steam_id` (String)
- Sort key: `date` (String) - format: YYYY-MM-DD

### Lambda Environment Variables

Configure the following environment variables for the Lambda function:

- `STEAM_API_KEY`: Your Steam API key
- `STEAM_ID`: Your Steam ID
- `DYNAMODB_TABLE`: DynamoDB table name (default: `steam_game_tracker`)

### Required IAM Permissions

The Lambda execution role needs the following permissions:

- DynamoDB: `GetItem`, `PutItem` permissions on the DynamoDB table
- CloudWatch: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`

Example IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/steam_game_tracker"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

## Deployment

1. Install dependencies in the `package` directory:
   ```
   pip install requests boto3 -t package/
   ```

2. Copy the Lambda function to the package directory:
   ```
   cp lambda_steam_game_tracker.py package/
   ```

3. Create a deployment package:
   ```
   cd package && zip -r ../lambda_steam_game_tracker.zip . && cd ..
   ```

4. Deploy using Terraform (see terraform configuration in the project) or directly in the AWS Management Console

## CloudWatch Event Rule

Set up a CloudWatch Event Rule to trigger the Lambda function at midnight every day:

```
cron(0 0 * * ? *)
```

## Output Format in DynamoDB

Each daily record contains:
- `steam_id`: Your Steam ID
- `date`: Date in YYYY-MM-DD format
- `total_daily_minutes`: Total minutes played across all games on this day
- `total_daily_hours`: Total hours played across all games on this day
- `games_count`: Number of games played on this day
- `games`: JSON object with details of each game played
- `raw_data`: Raw processed data from the Steam API
- `top_game`: Name of the most played game of the day
- `timestamp`: ISO format timestamp of when the record was created

## Example

Sample DynamoDB entry:

```json
{
  "steam_id": "76561198004823756",
  "date": "2025-04-23",
  "total_daily_minutes": 180,
  "total_daily_hours": 3.0,
  "games_count": 2,
  "games": {
    "1091500": {
      "app_id": "1091500",
      "name": "Cyberpunk 2077",
      "playtime_minutes": 120,
      "playtime_hours": 2.0,
      "total_playtime_minutes": 8640,
      "total_playtime_hours": 144.0
    },
    "377160": {
      "app_id": "377160",
      "name": "Fallout 4",
      "playtime_minutes": 60,
      "playtime_hours": 1.0,
      "total_playtime_minutes": 8470,
      "total_playtime_hours": 141.17
    }
  },
  "top_game": "Cyberpunk 2077",
  "timestamp": "2025-04-23T00:00:01.123456"
}
```

This record shows that on April 23, 2025, you played Cyberpunk 2077 for 2 hours and Fallout 4 for 1 hour, with Cyberpunk being your most played game of the day.