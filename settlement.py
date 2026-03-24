import requests
import logging
import datetime
from dateutil import parser
from config import Config
import database
from arb_calculator import american_to_decimal

logger = logging.getLogger(__name__)

def fetch_results(dates: list):
    """
    Fetches NBA game results for a list of dates (YYYY-MM-DD) from Ball Don't Lie API.
    Returns a list of games.
    """
    if not Config.BALLDONTLIE_API_KEY or Config.BALLDONTLIE_API_KEY == "your_balldontlie_api_key_here":
        logger.warning("BALLDONTLIE_API_KEY not configured. Cannot settle bets.")
        return []
        
    url = "https://api.balldontlie.io/v1/games"
    headers = {
        "Authorization": Config.BALLDONTLIE_API_KEY
    }
    # Requests can take a list for duplicate query params (dates[]=...&dates[]=...)
    params = [("dates[]", d) for d in dates]
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching results from Ball Don't Lie API: {e}")
        return []

def match_team_names(odds_api_name: str, bdl_name: str, bdl_full_name: str) -> bool:
    """Fuzzy matching for team names between APIs."""
    odds_api_name_lower = odds_api_name.lower()
    if not bdl_name or not bdl_full_name:
        return False
    return bdl_name.lower() in odds_api_name_lower or bdl_full_name.lower() in odds_api_name_lower

def settle_open_bets():
    """
    Looks up open bets, fetches results for their dates, and settles if finished.
    Returns a list of settled bet dicts for notification purposes.
    """
    open_bets = database.get_open_bets()
    if not open_bets:
        return []
        
    # We will compute a set of dates (+/- 1 day from placed_at for all open bets)
    dates_to_check = set()
    for bet in open_bets:
        placed_date = parser.parse(bet['placed_at'])
        dates_to_check.add((placed_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        dates_to_check.add(placed_date.strftime('%Y-%m-%d'))
        dates_to_check.add((placed_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        
    results = fetch_results(list(dates_to_check))
    newly_settled = []
    
    for bet in open_bets:
        # Find matching game in results
        for game in results:
            if game.get('status') != 'Final':
                continue
                
            home_team = game.get('home_team', {})
            away_team = game.get('visitor_team', {})
            
            # Check if this game matches the bet's teams
            home_match = match_team_names(bet['home_team'], home_team.get('name', ''), home_team.get('full_name', '')) or \
                         match_team_names(bet['away_team'], home_team.get('name', ''), home_team.get('full_name', ''))
            away_match = match_team_names(bet['home_team'], away_team.get('name', ''), away_team.get('full_name', '')) or \
                         match_team_names(bet['away_team'], away_team.get('name', ''), away_team.get('full_name', ''))
                         
            if home_match and away_match:
                home_score = game.get('home_team_score', 0)
                away_score = game.get('visitor_team_score', 0)
                
                winner_name = home_team.get('full_name', '') if home_score > away_score else away_team.get('full_name', '')
                
                won_a = match_team_names(bet['outcome_a'], winner_name, winner_name)
                won_b = match_team_names(bet['outcome_b'], winner_name, winner_name)
                
                if won_a:
                    revenue = bet['stake_a'] * american_to_decimal(bet['odds_a'])
                elif won_b:
                    revenue = bet['stake_b'] * american_to_decimal(bet['odds_b'])
                else:
                    # Fallback
                    revenue = bet['stake_a'] + bet['stake_b']
                    
                total_staked = bet['stake_a'] + bet['stake_b']
                realized_profit = revenue - total_staked
                
                database.settle_bet(bet['id'], realized_profit)
                
                # Add back the returned revenue to bankroll
                current_bankroll = database.get_bankroll()
                database.update_bankroll(current_bankroll + revenue)
                
                settled_bet = dict(bet)
                settled_bet['status'] = 'SETTLED'
                settled_bet['realized_profit'] = round(realized_profit, 2)
                settled_bet['revenue'] = round(revenue, 2)
                settled_bet['winner'] = bet['outcome_a'] if won_a else (bet['outcome_b'] if won_b else 'Push')
                
                newly_settled.append(settled_bet)
                logger.info(f"Settled bet {bet['id']} for realized profit: ${realized_profit:.2f}")
                break
                
    return newly_settled
