import os
from groq import Groq
import logging
from config import Config

logger = logging.getLogger(__name__)

client = None
if Config.GROQ_API_KEY and Config.GROQ_API_KEY != "your_groq_api_key_here":
    try:
        client = Groq(api_key=Config.GROQ_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

def _generate_text(prompt: str) -> str:
    if not client:
        return "AI generation unavailable. Please configure GROQ_API_KEY."
        
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are PicoClaw, an expert sports betting arbitrage AI. Provide concise, clear, and professional summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return "AI generation failed."

def generate_arb_alert_text(bet_data: dict) -> str:
    """Generates a plain English alert for a new arbitrage bet."""
    if bet_data.get('status') == 'SUSPICIOUS_FLAGGED':
        return f"🚨 SUSPICIOUS ARB FLAGGED: {bet_data['guaranteed_profit_pct']*100:.2f}% margin on {bet_data['home_team']} vs {bet_data['away_team']}. Did not place bet."
        
    prompt = f"""
    Generate a single, punchy sentence explaining this arbitrage paper bet I just placed.
    Do not add extra commentary. Give exact numbers.
    Game: {bet_data['home_team']} vs {bet_data['away_team']}
    Stake A: ${bet_data['stake_a']:.2f} on {bet_data['outcome_a']} ({bet_data['odds_a']}) at {bet_data['book_a']}
    Stake B: ${bet_data['stake_b']:.2f} on {bet_data['outcome_b']} ({bet_data['odds_b']}) at {bet_data['book_b']}
    Guaranteed Profit: ${bet_data['guaranteed_profit']:.2f}
    Return Percentage: {bet_data['guaranteed_profit_pct']*100:.2f}%
    
    Example format: Bet $52.00 on Lakers -110 at DraftKings and $48.00 on Celtics +115 at FanDuel for a guaranteed $4.20 profit — 0.84% return.
    """
    ai_response = _generate_text(prompt)
    if ai_response.startswith("AI generation"):
        return f"Bet ${bet_data['stake_a']:.2f} on {bet_data['outcome_a']} ({bet_data['odds_a']}) at {bet_data['book_a']} and ${bet_data['stake_b']:.2f} on {bet_data['outcome_b']} ({bet_data['odds_b']}) at {bet_data['book_b']} for a guaranteed ${bet_data['guaranteed_profit']:.2f} profit — {bet_data['guaranteed_profit_pct']*100:.2f}% return."
    return ai_response

def generate_daily_pnl_summary(pnl_data: dict, bankroll: float) -> str:
    """Generates a narrative context for the daily PnL."""
    prompt = f"""
    Generate a short 2-3 sentence daily summary for an NBA arbitrage trading bot.
    Today's Settled Bets: {pnl_data['settled_today']}
    Today's Profit: ${pnl_data['profit_today']:.2f}
    Current Virtual Bankroll: ${bankroll:.2f}
    
    Add a tiny bit of professional sports betting flair.
    """
    ai_response = _generate_text(prompt)
    if ai_response.startswith("AI generation"):
        return f"Today ended with {pnl_data['settled_today']} settled bets and a daily profit of ${pnl_data['profit_today']:.2f}. Total bankroll stands at ${bankroll:.2f}."
    return ai_response

def generate_weekly_report(stats: dict) -> str:
    """Generates a final week report."""
    prompt = f"""
    Generate a 1-paragraph final weekly report for our NBA arbitrage paper trading simulation.
    Starting Bankroll: $1000.00
    Final Bankroll: ${stats.get('final_bankroll'):.2f}
    Total Bets Placed: {stats.get('total_bets')}
    Total Open Bets: {stats.get('open_bets', 0)}
    Total Profit: ${stats.get('total_profit'):.2f}
    ROI: {stats.get('roi_pct'):.2f}%
    
    Summarize the performance of the perfect arbitrage strategy over this past week.
    """
    ai_response = _generate_text(prompt)
    if ai_response.startswith("AI generation"):
        return f"Weekly Report: We placed {stats.get('total_bets')} bets resulting in a total profit of ${stats.get('total_profit'):.2f}. The ending bankroll is ${stats.get('final_bankroll'):.2f} (ROI: {stats.get('roi_pct'):.2f}%)."
    return ai_response
