import requests
import logging
from config import Config

logger = logging.getLogger(__name__)

def fetch_nba_odds():
    """
    Fetches live NBA odds from The Odds API.
    Returns a list of game data or empty list if failed.
    """
    if not Config.ODDS_API_KEY or Config.ODDS_API_KEY == "your_odds_api_key_here":
        logger.warning("ODDS_API_KEY not configured. Returning empty odds list.")
        return []
        
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
    params = {
        "apiKey": Config.ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american"
    }
    
    try:
        # 10s timeout to allow polling quickly
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching odds from The Odds API: {e}")
        return []

def parse_odds_data(api_response):
    """
    Parses The Odds API response into a simplified structure.
    Returns a list of games, each dict containing available odds for home and away.
    """
    parsed_games = []
    
    if not api_response:
        return parsed_games
        
    for game in api_response:
        game_data = {
            "game_id": game.get("id"),
            "sport": "basketball_nba",
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            "commence_time": game.get("commence_time"),
            "books": []
        }
        
        for bookmaker in game.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        game_data["books"].append({
                            "book_name": bookmaker.get("title"),
                            "outcomes": outcomes, # e.g. [{"name": "Lakers", "price": -110}, {"name": "Celtics", "price": +105}]
                            "last_update": bookmaker.get("last_update")
                        })
                        
        # We need at least 2 books to find cross-book arbs
        # Actually, theoretically one book could have an arb but that's rare, 
        # still filter to games where we have *some* lines
        if len(game_data["books"]) >= 2:
            parsed_games.append(game_data)
            
    return parsed_games
