import os
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading

# Config
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID"))

app = Flask(__name__)
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@app.route('/')
def index():
    """Root endpoint for Render health checks."""
    return "TSR Discord Bridge is Online. Waiting for signals from Hugging Face.", 200

@app.route('/webhook', methods=['POST'])
def trade_notification():
    """Hugging Face calls this endpoint when a trade is confirmed."""
    data = request.json
    bot.loop.create_task(post_trade_embed(data))
    return jsonify({"status": "received"}), 200

async def post_trade_embed(data):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        color = discord.Color.green() if data['action'] == "BUY" else discord.Color.red()
        embed = discord.Embed(title=f"🚨 TRADE EXECUTED: {data['ticker']}", color=color)
        embed.add_field(name="Action", value=data['action'], inline=True)
        embed.add_field(name="Amount", value=data['amount'], inline=True)
        embed.add_field(name="Price", value=f"{data['price']} TSR", inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Render Discord Bridge Online: {bot.user}")

def run_discord_bot():
    """Starts the bot.run() in a dedicated thread."""
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Discord Connection Error: {e}")

# --- STARTUP LOGIC ---
# This ensures the bot starts only once when Gunicorn loads the app
if not any(thread.name == "DiscordBotThread" for thread in threading.enumerate()):
    print("🛰️ Initializing Discord Bot Thread...")
    threading.Thread(target=run_discord_bot, name="DiscordBotThread", daemon=True).start()

if __name__ == "__main__":
    # For local debugging
    app.run(host='0.0.0.0', port=8080)