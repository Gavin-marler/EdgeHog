import discord
from discord.ext import commands
import logging
from config import Config
import database
import ai_layer
import scheduler as app_scheduler_module

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Discord Bot logged in as {bot.user}")
    sched = app_scheduler_module.get_scheduler()
    sched.start()
    logger.info("Scheduler started inside bot event loop.")
    
async def send_arb_alert(bet_data: dict):
    channel = bot.get_channel(Config.DISCORD_ARB_ALERTS_CHANNEL_ID)
    if not channel:
        return
        
    ai_text = ai_layer.generate_arb_alert_text(bet_data)
    
    embed = discord.Embed(
        title="🔔 Arbitrage Opportunity Detected & Placed",
        color=discord.Color.green() if bet_data.get('status') == 'PLACED' else discord.Color.red(),
        description=ai_text
    )
    embed.add_field(name="Game", value=f"{bet_data['home_team']} vs {bet_data['away_team']}", inline=False)
    embed.add_field(name="Leg 1", value=f"{bet_data['book_a']}: {bet_data['outcome_a']} ({bet_data['odds_a']})\nStake: ${bet_data['stake_a']:.2f}", inline=True)
    embed.add_field(name="Leg 2", value=f"{bet_data['book_b']}: {bet_data['outcome_b']} ({bet_data['odds_b']})\nStake: ${bet_data['stake_b']:.2f}", inline=True)
    embed.add_field(name="Guaranteed Profit", value=f"${bet_data['guaranteed_profit']:.2f} ({bet_data['guaranteed_profit_pct']*100:.2f}%)", inline=False)
    
    await channel.send(embed=embed)
    
    if bet_data.get('status') == 'PLACED':
        ob_channel = bot.get_channel(Config.DISCORD_OPEN_BETS_CHANNEL_ID)
        if ob_channel:
            await ob_channel.send(f"🟢 **New Open Bet:** {bet_data['home_team']} vs {bet_data['away_team']} - Guarantee: ${bet_data['guaranteed_profit']:.2f}")

async def send_settlement_alert(settled_bets: list):
    channel = bot.get_channel(Config.DISCORD_OPEN_BETS_CHANNEL_ID)
    if not channel or not settled_bets:
        return
        
    for bet in settled_bets:
        embed = discord.Embed(
            title="✅ Bet Settled",
            color=discord.Color.blue(),
            description=f"**{bet['home_team']} vs {bet['away_team']}** has gone final."
        )
        embed.add_field(name="Winner", value=bet.get('winner', 'Unknown'), inline=True)
        embed.add_field(name="Realized Profit", value=f"${bet['realized_profit']:.2f}", inline=True)
        await channel.send(embed=embed)

async def send_daily_pnl():
    channel = bot.get_channel(Config.DISCORD_PNL_CHANNEL_ID)
    if not channel:
        return
        
    pnl_data = database.get_daily_pnl()
    bankroll = database.get_bankroll()
    
    ai_text = ai_layer.generate_daily_pnl_summary(pnl_data, bankroll)
    
    embed = discord.Embed(
        title="📊 Daily PnL Summary",
        color=discord.Color.gold(),
        description=ai_text
    )
    embed.add_field(name="Bankroll", value=f"${bankroll:.2f}", inline=True)
    embed.add_field(name="Today's Profit", value=f"${pnl_data['profit_today']:.2f}", inline=True)
    embed.add_field(name="Settled Today", value=str(pnl_data['settled_today']), inline=True)
    
    await channel.send(embed=embed)

@bot.command(name="bankroll")
async def cmd_bankroll(ctx):
    bal = database.get_bankroll()
    await ctx.send(f"💰 Current Virtual Bankroll: **${bal:.2f}**")

@bot.command(name="openbets")
async def cmd_openbets(ctx):
    bets = database.get_open_bets()
    if not bets:
        await ctx.send("No open bets currently.")
        return
        
    msg = f"📋 **{len(bets)} Open Bets:**\n"
    for b in bets:
        msg += f"- {b['home_team']} vs {b['away_team']} | Guarantee: ${b['guaranteed_profit']:.2f}\n"
    await ctx.send(msg)

@bot.command(name="pnl")
async def cmd_pnl(ctx):
    bal = database.get_bankroll()
    profit = bal - Config.STARTING_BANKROLL
    await ctx.send(f"📈 **Running PnL:**\nStarting: ${Config.STARTING_BANKROLL:.2f}\nCurrent: ${bal:.2f}\nTotal Profit: **${profit:.2f}**")

@bot.command(name="lastbet")
async def cmd_lastbet(ctx):
    bets = database.get_recent_bets(1)
    if not bets:
        await ctx.send("No bets placed yet.")
        return
    b = bets[0]
    await ctx.send(f"🔍 **Last Bet:**\n{b['home_team']} vs {b['away_team']}\nPlaced: {b['placed_at']}\nGuarantee: ${b['guaranteed_profit']:.2f}")

@bot.command(name="status")
async def cmd_status(ctx):
    await ctx.send("✅ **EdgeHog Bot is live and polling.**")

@bot.command(name="report")
async def cmd_report(ctx):
    await ctx.send("⏳ Generating AI performance summary...")
    bal = database.get_bankroll()
    profit = bal - Config.STARTING_BANKROLL
    
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bets")
    total_bets = c.fetchone()[0]
    conn.close()
    
    stats = {
        'final_bankroll': bal,
        'total_bets': total_bets,
        'open_bets': database.get_open_bet_count(),
        'total_profit': profit,
        'roi_pct': (profit / Config.STARTING_BANKROLL) * 100
    }
    
    report_text = ai_layer.generate_weekly_report(stats)
    await ctx.send(f"📄 **Performance Report:**\n\n{report_text}")

@bot.command(name="threshold")
async def cmd_threshold(ctx):
    val = float(database.get_config('arb_threshold', Config.MIN_PROFIT_MARGIN))
    await ctx.send(f"⚙️ Current Arb Threshold: **{val*100:.2f}%**")

@bot.command(name="setthreshold")
async def cmd_setthreshold(ctx, val: float):
    if not (0.5 <= val <= 10.0):
        await ctx.send("❌ Error: Threshold must be between 0.5 and 10.0")
        return
    decimal_val = val / 100.0
    database.set_config('arb_threshold', str(decimal_val))
    await ctx.send(f"✅ Arb Threshold updated to **{val:.2f}%**")

@bot.command(name="setstake")
async def cmd_setstake(ctx, val: float):
    if not (1.0 <= val <= 25.0):
        await ctx.send("❌ Error: Max Stake must be between 1.0 and 25.0")
        return
    decimal_val = val / 100.0
    database.set_config('max_stake_pct', str(decimal_val))
    await ctx.send(f"✅ Max Stake % updated to **{val:.2f}%** of current bankroll")

@bot.command(name="pause")
async def cmd_pause(ctx):
    database.set_config('polling_paused', 'true')
    await ctx.send("⏸️ **Polling paused**. Will not check for new arbs until resumed.")

@bot.command(name="resume")
async def cmd_resume(ctx):
    database.set_config('polling_paused', 'false')
    await ctx.send("▶️ **Polling resumed**.")

def run_bot():
    if not Config.DISCORD_BOT_TOKEN or Config.DISCORD_BOT_TOKEN == "your_discord_bot_token_here":
        logger.error("Discord bot token not configured.")
        return
    bot.run(Config.DISCORD_BOT_TOKEN, log_handler=None)
