---
title: REST API
sidebar_position: 1
---

# REST API

Same origin as the app, JSON in and out. Write routes are authorised by a signature in the body. Bodies are capped at 4 KB.

| Method | Path | Limit / min |
| --- | --- | --- |
| POST | `/api/orders` | 30 |
| POST | `/api/orders/cancel` | 60 |
| POST | `/api/orders/cancel-all` | 30 |
| GET | `/api/orders/list` | 120 |
| GET | `/api/markets` | |
| GET | `/api/markets/:id` | |
| GET | `/api/markets/:id/orderbook` | |
| GET | `/api/markets/:id/trades` | |
| GET | `/api/markets/:id/candles` | |
| GET | `/api/fills` | 120 |
| GET | `/api/time` | |
| GET | `/api/health`, `/api/ready` | |

## POST /api/orders

```json
{
  "owner": "G...",
  "market_id": 1,
  "is_long": true,
  "size": "10000000",
  "limit_price": "205000000000000000",
  "reduce_only": false,
  "nonce": "1780061000000",
  "expiry_ts": "1780064600",
  "signature": "<base64>"
}
```

Returns `{ "ok": true }`, or `{ "ok": false, "error": "..." }` with 400, 413, 429 or 500.

## POST /api/orders/cancel

```json
{ "owner": "G...", "nonce": "1780061000000", "signature": "<base64>" }
```

## POST /api/orders/cancel-all

```json
{ "owner": "G...", "market_id": 1, "issued_at": "1780061000", "signature": "<base64>" }
```

Returns `{ "ok": true, "cancelled": 2, "nonces": ["..."] }`. Leave out `market_id` to cancel everywhere.

## GET /api/orders/list

`?address=G...&status=open|all&market_id=1&limit=100`

```json
{ "address": "G...", "status": "open", "count": 1, "orders": [{
  "id": "G...:1780061000000", "market_id": 1, "is_long": true,
  "size": "10000000", "limit_price": "205000000000000000",
  "filled_size": "0", "remaining_size": "10000000", "reduce_only": false,
  "nonce": "1780061000000", "expiry_ts": "1780064600",
  "cancelled": false, "expired": false, "created_at": 1780061000123 }] }
```

## GET /api/markets

```json
{ "network": "testnet", "price_precision": "1000000000000000000", "amount_precision": "10000000",
  "markets": [{ "market_id": 1, "symbol": "XLM-PERP", "active": true,
    "last_price": "205000000000000000", "last_oracle_price": "203800000000000000",
    "long_open_interest": "0", "short_open_interest": "0",
    "funding_long_index": "0", "funding_short_index": "0",
    "price_decimals": 4, "size_decimals": 4, "tick_sizes": [0.0001, 0.001, 0.01, 0.1],
    "max_leverage_bps": 100000, "initial_margin_bps": 1000, "maintenance_margin_bps": 500 }] }
```

## Market data

| Route | Returns |
| --- | --- |
| `/api/markets/:id/orderbook` | `{ bids: [{ price, size }], asks, timestamp }` |
| `/api/markets/:id/trades?limit=50` | `[{ price, size, side, timestamp }]`, newest first |
| `/api/markets/:id/candles?tf=3600&limit=600` | `[{ time, open, high, low, close, volume }]`, oldest first |
| `/api/fills?address=G...&since=<ms>&limit=20` | `[{ id, marketId, isMaker, price, size, txHash, createdAt }]` |
| `/api/time` | `{ unix_ms, unix_seconds, iso, min_ttl_seconds, max_ttl_seconds }` |
| `/api/ready` | `{ ok, network, markets, websocketConfigured, timestamp }` |

Order book, trades and fills use human units with 4 decimals. Everything else uses raw integers. See [Units](units-and-precision.md).
