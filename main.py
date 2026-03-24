import logging
from config import Config
import database
import scheduler
from discord_bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing EdgeHog NBA Arbitrage Bot...")
    
    # 1. Initialize Database
    database.init_db()
    current_bankroll = database.get_bankroll()
    logger.info(f"Current Virtual Bankroll: ${current_bankroll:.2f}")
    
    # Check if bankroll is zero
    if current_bankroll <= 0:
        logger.error("Bankroll depleted. Please reset DB to run again.")
        return
        
    # 2. Start Scheduler
    app_scheduler = scheduler.get_scheduler()
    app_scheduler.start()
    logger.info("Scheduler started.")
    
    # 3. Start Discord Bot (This is a blocking call)
    logger.info("Starting Discord bot...")
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        app_scheduler.shutdown()

if __name__ == "__main__":
    main()
