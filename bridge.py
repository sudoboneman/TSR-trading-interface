import os
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
from datetime import datetime

# Config
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID"))

app = Flask(__name__)
# Using Intents.default() as per your original file
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@app.route('/')
def index():
    """Root endpoint for Render health checks."""
    return "TSR Discord Bridge is Online. Waiting for signals from Hugging Face.", 200

@app.route('/webhook', methods=['POST'])
def trade_notification():
    """Hugging Face calls this endpoint for trades and startup probes."""
    data = request.json
    # We use create_task to ensure the bot handles the message without blocking Flask
    bot.loop.create_task(post_trade_embed(data))
    return jsonify({"status": "received"}), 200

async def post_trade_embed(data):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Error: Could not find channel ID {CHANNEL_ID}")
        return

    ticker = data.get("ticker")
    action = data.get("action")

    # --- STARTUP PROBE LOGIC ---
    if action == "STARTUP" and ticker == "SYSTEM":
        embed = discord.Embed(
            title="🚀 TSR Engine Online",
            description="The Hugging Face 'Brain' has successfully logged in and the market scanner is now active.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Startup Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        await channel.send(embed=embed)
        return

    # --- STANDARD TRADE LOGIC ---
    color = discord.Color.green() if action == "BUY" else discord.Color.red()
    embed = discord.Embed(title=f"🚨 TRADE EXECUTED: {ticker}", color=color)
    embed.add_field(name="Action", value=action, inline=True)
    embed.add_field(name="Amount", value=data.get('amount', 0), inline=True)
    embed.add_field(name="Price", value=f"{data.get('price', 0)} TSR", inline=True)
    await channel.send(embed=embed)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✅ Render Discord Bridge Online: {bot.user}")
    except Exception as e:
        print(f"⚠️ Slash Command Sync Warning: {e}")

def run_discord_bot():
    """Starts the bot in a dedicated thread to keep Flask responsive."""
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Discord Connection Error: {e}")

# --- STARTUP LOGIC ---
if not any(thread.name == "DiscordBotThread" for thread in threading.enumerate()):
    print("🛰️ Initializing Discord Bot Thread...")
    threading.Thread(target=run_discord_bot, name="DiscordBotThread", daemon=True).start()

if __name__ == "__main__":
    # Render typically uses Gunicorn, but this is kept for your local debugging
    app.run(host='0.0.0.0', port=8080)