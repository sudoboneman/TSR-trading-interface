import os
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
from threading import Thread

# Config
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID"))

app = Flask('')
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

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

@bot.tree.command(name="status", description="Check if the bridge is receiving signals")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Discord Bridge is online on Render.")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (Render Bridge)")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(TOKEN)