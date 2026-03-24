# EdgeHog - NBA Arbitrage Paper Trading Bot

An autonomous sports betting arbitrage paper trading system for NBA games. Detects arbitrage opportunities, automatically places paper trades, tracks performance, and communicates through a Discord bot.

## Features
- Polls live NBA odds during smart windows (6pm–midnight CT)
- Analyzes 2-way and 3-way markets for arbitrage opportunities (>= 1.5% profit)
- Places paper bets adhering to stake rules and max open bets
- Settles bets automatically using Ball Don't Lie API
- Comprehensive Discord bot for alerts, tracking, and PnL reporting
- Uses Groq AI to generate natural language explanations and summaries

## Environment Variables
See `.env.example` to set up your `.env` file containing necessary API keys.

## Deployment
Use `deploy.sh` to install dependencies and install the `edgehog` systemd service to run in the background on a Raspberry Pi.
