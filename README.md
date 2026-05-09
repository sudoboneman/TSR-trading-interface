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

Designed for [Render](https://render.com). Set the following environment variables:

```
DISCORD_TOKEN=<discord bot token>
ALERT_CHANNEL_ID=<discord channel ID>
```

Start with:
```
python bridge.py
```
