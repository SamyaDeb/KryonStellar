---
title: Configuration
sidebar_position: 2
---

# Configuration

Templates live in `client/.env.local.example` and `client/.env.testnet.example`. Never put a secret in a `NEXT_PUBLIC_` variable.

## Network and contracts

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_STELLAR_NETWORK` | `testnet` |
| `NEXT_PUBLIC_STELLAR_RPC_URL`, `NEXT_PUBLIC_STELLAR_HORIZON_URL` | Endpoints |
| `NEXT_PUBLIC_CONTRACT_*` | Override any contract address |
| `NEXT_PUBLIC_ACTIVE_MARKETS` | Markets to serve, comma separated |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL |

## App

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL |
| `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Rate limiting, required in production |

## Service keys

| Variable | Service |
| --- | --- |
| `MATCHER_OPERATOR_SECRET` | Matcher, reconciler |
| `ORACLE_PUBLISHER_SECRET` | Oracle keeper |
| `LIQUIDATOR_SECRET` | Liquidation keeper |
| `FUNDING_KEEPER_SECRET` | Funding keeper |
| `TTL_KEEPER_SECRET` | TTL keeper |

## Tuning

| Variable | Default |
| --- | --- |
| `ORACLE_MIN_SOURCES` | 2 |
| `ORACLE_MAX_SOURCE_DEVIATION_BPS` | 200 |
| `PUBLISH_DEVIATION_BPS`, `PUBLISH_HEARTBEAT_SECS` | 30, 60 |
| `USDC_DEPEG_HALT_BPS` | 100 |
| `REFLECTOR_DIVERGENCE_HALT_BPS` | 300 |
| `LIQUIDATION_INTERVAL_MS` | 5000 |
| `FUNDING_INTERVAL_MS` | 900000 |
| `ALERT_WEBHOOK_URL` | where the monitor sends alerts |

Every layer, from the browser bundle to the keepers, must point at the same contracts.
