import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    # Parse integers safely
    def _parse_int(val):
        try:
            return int(val) if val else 0
        except ValueError:
            return 0
            
    DISCORD_GUILD_ID = _parse_int(os.getenv("DISCORD_GUILD_ID"))
    DISCORD_ARB_ALERTS_CHANNEL_ID = _parse_int(os.getenv("DISCORD_ARB_ALERTS_CHANNEL_ID"))
    DISCORD_OPEN_BETS_CHANNEL_ID = _parse_int(os.getenv("DISCORD_OPEN_BETS_CHANNEL_ID"))
    DISCORD_PNL_CHANNEL_ID = _parse_int(os.getenv("DISCORD_PNL_CHANNEL_ID"))
    BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY")
    
    # Static parameters
    DATABASE_PATH = "edgehog.db"
    STARTING_BANKROLL = 1000.0
    MIN_PROFIT_MARGIN = 0.015 # 1.5%
    MIN_STAKE = 20.0
    MAX_STAKE_PCT = 0.10 # 10% of current bankroll
    MAX_OPEN_BETS = 5
    SUSPICIOUS_PROFIT_MARGIN = 0.04 # 4%
