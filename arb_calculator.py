import logging

logger = logging.getLogger(__name__)

def american_to_decimal(american_odds: int) -> float:
    """Converts American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100.0) + 1.0
    elif american_odds < 0:
        return (100.0 / abs(american_odds)) + 1.0
    return 1.0

def american_to_implied(american_odds: int) -> float:
    """Converts American odds to implied probability."""
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    elif american_odds < 0:
        return abs(american_odds) / (abs(american_odds) + 100.0)
    return 1.0

def detect_arbitrage(odds_list: list) -> tuple:
    """
    Detects if an arbitrage opportunity exists given a list of American odds.
    Works for 2-way and 3-way markets.
    Returns (is_arb_exists, combined_prob, profit_margin)
    """
    try:
        implied_probs = [american_to_implied(odds) for odds in odds_list]
        combined_prob = sum(implied_probs)
        
        if combined_prob < 1.0:
            profit_margin = (1.0 / combined_prob) - 1.0
            return True, combined_prob, profit_margin
        return False, combined_prob, 0.0
    except Exception as e:
        logger.error(f"Error calculating arbitrage: {e}")
        return False, 1.0, 0.0

def calculate_arb_stakes_from_max_stake(odds_a: int, odds_b: int, max_stake_allowed: float):
    """
    Calculates stakes for a 2-way arbitrage by scaling up until 
    the maximum stake hits max_stake_allowed.
    Ensures equal profit regardless of outcome.
    
    Returns (stake_a, stake_b, guaranteed_profit, profit_pct)
    """
    dec_a = american_to_decimal(odds_a)
    dec_b = american_to_decimal(odds_b)
    
    # Assume stake_a is max_stake_allowed
    stake_b_if_a_max = max_stake_allowed * (dec_a / dec_b)
    
    # Assume stake_b is max_stake_allowed
    stake_a_if_b_max = max_stake_allowed * (dec_b / dec_a)
    
    if stake_b_if_a_max <= max_stake_allowed:
        stake_a = max_stake_allowed
        stake_b = stake_b_if_a_max
    else:
        stake_b = max_stake_allowed
        stake_a = stake_a_if_b_max
        
    total_investment = stake_a + stake_b
    return_amount = stake_a * dec_a
    profit = return_amount - total_investment
    profit_pct = profit / total_investment
    
    return round(stake_a, 2), round(stake_b, 2), round(profit, 2), round(profit_pct, 4)

def calculate_3way_arb_stakes_from_max_stake(odds_a: int, odds_b: int, odds_c: int, max_stake_allowed: float):
    """
    Calculates stakes for a 3-way arbitrage.
    
    Returns (stake_a, stake_b, stake_c, guaranteed_profit, profit_pct)
    """
    dec_a = american_to_decimal(odds_a)
    dec_b = american_to_decimal(odds_b)
    dec_c = american_to_decimal(odds_c)
    
    inv_a = 1 / dec_a
    inv_b = 1 / dec_b
    inv_c = 1 / dec_c
    
    r = max_stake_allowed / max(inv_a, inv_b, inv_c)
    
    stake_a = r * inv_a
    stake_b = r * inv_b
    stake_c = r * inv_c
    
    total_investment = stake_a + stake_b + stake_c
    profit = r - total_investment
    profit_pct = profit / total_investment
    
    return round(stake_a, 2), round(stake_b, 2), round(stake_c, 2), round(profit, 2), round(profit_pct, 4)
