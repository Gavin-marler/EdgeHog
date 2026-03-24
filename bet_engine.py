import datetime
import logging
from dateutil import parser
from config import Config
import database
from arb_calculator import detect_arbitrage, calculate_arb_stakes_from_max_stake

logger = logging.getLogger(__name__)

def find_best_lines(game_data: dict) -> dict:
    """
    Finds the best available odds for each outcome across all books.
    Returns a dict mapping outcome name to best book and odds.
    """
    best_lines = {} # outcome_name -> {"book": str, "odds": int, "last_update": str}
    
    for book in game_data.get("books", []):
        book_name = book.get("book_name")
        last_update = book.get("last_update")
        
        for outcome in book.get("outcomes", []):
            name = outcome.get("name")
            price = outcome.get("price")
            
            if name not in best_lines:
                best_lines[name] = {"book": book_name, "odds": price, "last_update": last_update}
            else:
                current_best_odds = best_lines[name]["odds"]
                # For American odds, higher value is better
                if price > current_best_odds:
                    best_lines[name] = {"book": book_name, "odds": price, "last_update": last_update}
                    
    return best_lines

def is_game_valid_for_betting(commence_time_str: str) -> bool:
    """Verifies that the game starts more than 30 minutes from now."""
    if not commence_time_str:
        return False
        
    try:
        commence_time = parser.parse(commence_time_str)
        now = datetime.datetime.now(datetime.timezone.utc)
        time_diff = commence_time - now
        return time_diff.total_seconds() > 1800 # 30 minutes = 1800 seconds
    except Exception as e:
        logger.error(f"Error parsing date {commence_time_str}: {e}")
        return False

def process_live_odds(parsed_games: list) -> list:
    """
    Scans games for arbs, checks constraints, and processes paper bets.
    Returns a list of dictionaries detailing the arbs placed or flagged.
    """
    new_alerts = []
    
    current_bankroll = database.get_bankroll()
    if current_bankroll <= 0:
        logger.warning("Bankroll is zero. Simulation ended.")
        return []
        
    open_bet_count = database.get_open_bet_count()
    max_stake_allowed = current_bankroll * Config.MAX_STAKE_PCT
    
    for game in parsed_games:
        if open_bet_count >= Config.MAX_OPEN_BETS:
            # We hit our concurrent max limit
            break
            
        commence_time = game.get("commence_time")
        if not is_game_valid_for_betting(commence_time):
            continue
            
        best_lines = find_best_lines(game)
        
        # We need exactly 2 outcomes for a 2-way market arb
        outcomes = list(best_lines.keys())
        if len(outcomes) != 2:
            continue
            
        team_a = outcomes[0]
        team_b = outcomes[1]
        
        odds_a = best_lines[team_a]["odds"]
        odds_b = best_lines[team_b]["odds"]
        
        is_arb, combined_prob, profit_margin = detect_arbitrage([odds_a, odds_b])
        
        if is_arb and profit_margin >= Config.MIN_PROFIT_MARGIN:
            is_suspicious = profit_margin > Config.SUSPICIOUS_PROFIT_MARGIN
            
            stake_a, stake_b, guaranteed_profit, profit_pct = calculate_arb_stakes_from_max_stake(
                odds_a, odds_b, max_stake_allowed
            )
            
            total_stake = stake_a + stake_b
            if min(stake_a, stake_b) < Config.MIN_STAKE:
                continue
                
            game_id = game.get("game_id")
            
            open_bets = database.get_open_bets()
            if any(b['game_id'] == game_id for b in open_bets):
                # Skip if we already have an open bet for this game
                continue
                
            bet_data = {
                "sport": game.get("sport"),
                "game_id": game_id,
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "market_type": "h2h",
                
                "book_a": best_lines[team_a]["book"],
                "outcome_a": team_a,
                "odds_a": odds_a,
                "stake_a": stake_a,
                
                "book_b": best_lines[team_b]["book"],
                "outcome_b": team_b,
                "odds_b": odds_b,
                "stake_b": stake_b,
                
                "guaranteed_profit": guaranteed_profit,
                "guaranteed_profit_pct": profit_pct
            }
            
            if not is_suspicious:
                # Place paper bet
                bet_id = database.save_bet(bet_data)
                
                # Deduct total matched stakes from bankroll
                new_bankroll = current_bankroll - total_stake
                database.update_bankroll(new_bankroll)
                current_bankroll = new_bankroll
                open_bet_count += 1
                
                bet_data["id"] = bet_id
                bet_data["status"] = "PLACED"
                new_alerts.append(bet_data)
                logger.info(f"Placed paper bet ID:{bet_id} on {team_a} vs {team_b}.")
            else:
                bet_data["status"] = "SUSPICIOUS_FLAGGED"
                new_alerts.append(bet_data)
                logger.warning(f"Suspicious arb detected ({profit_pct*100:.2f}%) on {team_a} vs {team_b}.")
                
    return new_alerts
