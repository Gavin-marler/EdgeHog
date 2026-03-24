import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

import odds_poller
import bet_engine
import settlement
from discord_bot import send_arb_alert, send_settlement_alert, send_daily_pnl

logger = logging.getLogger(__name__)

async def poll_odds_job():
    logger.info("Polling odds...")
    try:
        raw_odds = odds_poller.fetch_nba_odds()
        parsed_games = odds_poller.parse_odds_data(raw_odds)
        
        new_bets = bet_engine.process_live_odds(parsed_games)
        
        for bet in new_bets:
            await send_arb_alert(bet)
    except Exception as e:
        logger.error(f"Error in poll_odds_job: {e}")

async def settle_bets_job():
    logger.info("Checking for settled bets...")
    try:
        settled_bets = settlement.settle_open_bets()
        if settled_bets:
            await send_settlement_alert(settled_bets)
    except Exception as e:
        logger.error(f"Error in settle_bets_job: {e}")

async def daily_pnl_job():
    logger.info("Sending daily PnL...")
    try:
        await send_daily_pnl()
    except Exception as e:
        logger.error(f"Error in daily_pnl_job: {e}")

def get_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("America/Chicago"))
    
    # Poll odds every 5 minutes from 18:00 to 23:59
    scheduler.add_job(
        poll_odds_job,
        CronTrigger(hour='18-23', minute='*/5'),
        id="poll_odds_job"
    )
    
    # Settle bets every hour or so, and maybe right after midnight. 
    # Let's just run it every 30 minutes to be safe.
    scheduler.add_job(
        settle_bets_job,
        CronTrigger(minute='*/30'),
        id="settle_bets_job"
    )
    
    # Daily PnL at 8:00 AM CT
    scheduler.add_job(
        daily_pnl_job,
        CronTrigger(hour=8, minute=0),
        id="daily_pnl_job"
    )
    
    return scheduler
