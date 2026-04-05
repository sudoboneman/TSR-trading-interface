import os
import discord
from flask import Flask, request, jsonify
import threading
import asyncio
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN")
# Ensure we convert the channel ID to an integer securely
try:
    CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID", 0))
except ValueError:
    CHANNEL_ID = 0

# --- INITIALIZE APPS ---
app = Flask(__name__)
bot = discord.Client(intents=discord.Intents.default())

# --- FLASK WEB ROUTES ---
@app.route('/')
def index():
    return "TSR Discord Bridge is Online.", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Check if the bot is actually connected before trying to send
    if not bot.is_ready():
        print("Webhook received, but Discord Bot is not ready yet.")
        return jsonify({"error": "bot_offline"}), 503

    # CRITICAL FIX: Thread-safe cross-communication
    # This safely pushes the task from the Flask thread into the Discord thread
    asyncio.run_coroutine_threadsafe(send_discord_alert(data), bot.loop)
    
    return jsonify({"status": "queued"}), 200


# --- DISCORD ASYNC LOGIC ---
async def send_discord_alert(data):
    """Handles the actual sending of the message to Discord."""
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print(f"❌ CRITICAL ERROR: Bot cannot resolve channel ID {CHANNEL_ID}")
        return

    ticker = data.get("ticker", "UNKNOWN")
    action = data.get("action", "UNKNOWN")
    amount = data.get("amount", 0)

    try:
        # 1. Startup Probe Logic
        if action == "STARTUP" and ticker == "SYSTEM":
            embed = discord.Embed(
                title="📡 Market Online",
                description="The AGENT has successfully logged in and is scanning.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Boot sequence completed at {datetime.now().strftime('%H:%M:%S')}")
            await channel.send(embed=embed)
            print("Startup notification delivered.")
            
        # 2. Hourly Heartbeat Logic (RESTORED)
        elif action == "HEARTBEAT" and ticker == "SYSTEM":
            # We MAP the mismatched labels here:
            cash_value = data.get("amount", "0")   # 'amount' actually holds our cash
            uptime_str = data.get("price", "0h 0m") # 'price' actually holds our uptime string
            
            embed = discord.Embed(title="💓 Agent Status Report", color=discord.Color.blue())
            embed.description = "The market scanner is online and actively monitoring."
            
            # Use str() to ensure the uptime string doesn't break the embed
            embed.add_field(name="Uptime", value=str(uptime_str), inline=True)
            embed.add_field(name="Available Cash", value=f"{cash_value} TSR", inline=True)
            
            await channel.send(embed=embed)
            
        # 3. Standard Trade Alert Logic
        else:
            color = discord.Color.green() if action == "BUY" else discord.Color.red()
            embed = discord.Embed(title=f"🚨 TRADE EXECUTED: {ticker}", color=color)
            embed.add_field(name="Action", value=action, inline=True)
            embed.add_field(name="Amount", value=str(amount), inline=True)
            
            if 'price' in data:
                embed.add_field(name="Price", value=f"{data['price']} TSR", inline=True)
                
            await channel.send(embed=embed)
            print(f"Trade alert for {ticker} delivered.")
            
    except Exception as e:
        print(f"Discord API Delivery Error: {e}")


# --- STARTUP SEQUENCE ---
@bot.event
async def on_ready():
    print(f"Discord Bot Connected as {bot.user}")

def run_flask():
    """Runs the Flask server, binding to Render's required port 8080."""
    # Debug is False to prevent Flask from spawning duplicate workers
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    # 1. Start Flask in a background thread
    print("Booting Flask Web Server thread...")
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Start Discord in the Main Thread (This blocks the script and keeps it alive)
    print("Booting Discord connection...")
    bot.run(TOKEN)