#!/usr/bin/env python3
import requests
import json
import sys
import os
# Import configuration with API key and Steam ID
try:
    from config import API_KEY, STEAM_ID
except ImportError:
    print("Config file not found. You can provide API key and Steam ID as command line arguments.")
    API_KEY = None
    STEAM_ID = None

def get_recently_played_games(api_key, steam_id):
    """
    Fetch recently played games from the Steam API for a specific user.
    
    Args:
        api_key (str): Your Steam API key
        steam_id (str): The Steam ID of the user
        
    Returns:
        dict: JSON response from the Steam API containing recently played games
    """
    url = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
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
        print(f"Error fetching data from Steam API: {e}")
        return None

def display_games(games_data):
    """
    Display formatted information about recently played games.
    
    Args:
        games_data (dict): JSON response from the Steam API
    """
    if not games_data or 'response' not in games_data:
        print("No valid data returned from Steam API")
        return
    
    games = games_data['response'].get('games', [])
    total_count = games_data['response'].get('total_count', 0)
    
    print(f"\nTotal recently played games: {total_count}\n")
    
    if games:
        # Sort games by playtime in last two weeks (descending)
        games.sort(key=lambda x: x.get('playtime_2weeks', 0), reverse=True)
        
        # Display the recently played games
        print("Recently Played Games:")
        print("-" * 80)
        print(f"{'Game Name':<35} {'Last 2 Weeks (hours)':<20} {'Total (hours)':<20}")
        print("-" * 80)
        
        for i, game in enumerate(games, 1):
            name = game.get('name', f"Unknown Game ({game.get('appid', 'N/A')})")
            playtime_2weeks = round(game.get('playtime_2weeks', 0) / 60, 2)
            playtime_total = round(game.get('playtime_forever', 0) / 60, 2)
            print(f"{i}. {name:<33} {playtime_2weeks:<20} {playtime_total:<20}")

def main():
    """Main function to execute the script."""
    # Use config values or command-line arguments
    api_key = API_KEY
    steam_id = STEAM_ID
    
    # Override with command line arguments if provided
    if len(sys.argv) >= 3:
        api_key = sys.argv[1]
        steam_id = sys.argv[2]
    elif not api_key or not steam_id:
        print("API key and Steam ID not found in config.py.")
        print("Usage: python steam_game_tracker.py <api_key> <steam_id>")
        print("Example: python steam_game_tracker.py XXXXXXXXXXXXXXXXXXXX 76561197960434622")
        return
    
    print(f"Fetching recently played games for Steam ID: {steam_id}")
    games_data = get_recently_played_games(api_key, steam_id)
    
    if games_data:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(output_dir, 'steam_recent_games_data.json')
        
        # Save the full response to a JSON file
        with open(output_file, 'w') as f:
            json.dump(games_data, f, indent=2)
        print(f"Full data saved to {output_file}")
        
        # Display formatted game information
        display_games(games_data)

if __name__ == "__main__":
    main()