# TSR-trading-interface

A Discord notification bridge for the TSR trading agent ecosystem. Receives webhook payloads from trading bots and relays them as richly formatted Discord embeds to a configured alert channel.

## How it works

The service runs two components in a single process:

- **Flask web server** (port 8080) — accepts `POST /webhook` JSON payloads from trading agents
- **Discord bot** — authenticates with the Discord API and sends messages to a designated channel

When a webhook arrives, the Flask handler pushes the message task onto the Discord bot's async event loop, ensuring thread-safe delivery without blocking either component.

## Webhook Payload

All alerts use the same endpoint: `POST /webhook`

```json
{
  "ticker": "COIN",
  "action": "BUY | SELL | HEARTBEAT | STARTUP",
  "amount": 100,
  "price": 12.50
}
```

### Alert types

| Action | Ticker | Behaviour |
|---|---|---|
| `STARTUP` | `SYSTEM` | Blue embed — agent online notification |
| `HEARTBEAT` | `SYSTEM` | Blue embed with uptime + available cash fields |
| `BUY` | any ticker | Green embed — trade executed |
| `SELL` | any ticker | Red embed — trade executed |

## Deployment

Designed for [Render](https://render.com) Web Service.

### Required environment variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Discord bot token |
| `ALERT_CHANNEL_ID` | Discord channel ID to post alerts to |

### Render setup

- **Start command**: `python bridge.py`
- **Port**: 8080 (hardcoded in bridge.py, Render auto-maps $PORT)
- **Health check**: `GET /` returns 200 when running

The Flask server runs in a background thread while the Discord client occupies the main thread. Gunicorn is included in requirements.txt as a fallback but the service is designed to run standalone via `python bridge.py`.

### Local testing

```
pip install -r requirements.txt
export DISCORD_TOKEN=your_token
export ALERT_CHANNEL_ID=your_channel_id
python bridge.py
```
