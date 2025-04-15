import boto3
import requests
import os
import json

TEMP_FILE_PATH = "/tmp/notification_state.json"

def lambda_handler(event, context):
    # Configuration
    WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
    SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
    ZIP_CODE = "95117"
    TEMPERATURE_THRESHOLD = 65

    # Initialize SNS client
    sns = boto3.client('sns')

    # Fetch current temperature
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?zip={ZIP_CODE},us&units=imperial&appid={WEATHER_API_KEY}"
    response = requests.get(weather_url)
    weather_data = response.json()
    current_temp = weather_data['main']['temp']

    # Load notification state from temporary storage
    try:
        with open(TEMP_FILE_PATH, 'r') as file:
            state = json.load(file)
    except FileNotFoundError:
        state = {"notified_below": False}

    last_notified_below = state.get("notified_below", False)

    if current_temp < TEMPERATURE_THRESHOLD:
        if not last_notified_below:
            # Send notification
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=f"Temperature alert! The current temperature in {ZIP_CODE} is {current_temp}°F, which is below {TEMPERATURE_THRESHOLD}°F.",
                Subject="Temperature Alert"
            )
            # Update state in temporary storage
            state["notified_below"] = True
            with open(TEMP_FILE_PATH, 'w') as file:
                json.dump(state, file)
    else:
        if last_notified_below:
            # Update state in temporary storage to allow future notifications
            state["notified_below"] = False
            with open(TEMP_FILE_PATH, 'w') as file:
                json.dump(state, file)

    return {
        'statusCode': 200,
        'body': f"Checked temperature: {current_temp}°F"
    }