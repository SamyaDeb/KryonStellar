---
title: WebSocket API
sidebar_position: 2
---

# WebSocket API

Channels: `orderbook:<market_id>` and `trades:<market_id>`.

## You send

```json
{ "type": "subscribe", "channels": ["orderbook:1", "trades:1"] }
{ "type": "unsubscribe", "channels": ["orderbook:1"] }
{ "type": "ping" }
```

## You receive

```json
{ "type": "subscribed", "channels": ["orderbook:1", "trades:1"] }
{ "type": "orderbook", "market_id": 1, "bids": [{ "price": "0.2050", "size": "1.0000" }], "asks": [], "timestamp": 1780061000000 }
{ "type": "trade", "market_id": 1, "price": "0.2050", "size": "1.0000", "side": "buy", "timestamp": 1780061000000 }
{ "type": "pong" }
```

Each order book message is a full snapshot. Frames are capped at 16 KB.
