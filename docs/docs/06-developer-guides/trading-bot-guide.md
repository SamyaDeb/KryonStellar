---
title: Trading bots
sidebar_position: 4
---

# Trading bots

Kryon is easy to automate: sign an order once and the matcher settles it, even if your bot has gone offline.

## Fund an account

1. Fund a keypair with XLM from Friendbot.
2. Add a trustline to USDC, issuer `GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5`.
3. Deposit USDC with `vault.deposit`. See [Contract calls](../07-api-reference/contract-invocation.md).

## On start-up

1. `GET /api/time` to measure clock drift.
2. `GET /api/markets` for markets and precision.
3. `GET /api/orders/list?address=...&status=all` to recover your nonces and open orders.
4. Read your positions and health from the contracts.

## The loop

1. Read the book and the oracle price.
2. Skip if the book is crossed.
3. Sign and post orders within 10 % of the oracle, expiring in 5 s to 7 days.
4. Watch `GET /api/fills` and confirm with `gateway.filled(owner, nonce)`.
5. Cancel with the API, or on-chain when you need it enforced.

Cancel everything with `POST /api/orders/cancel-all` before you exit.

## Limits

| Endpoint | Per minute |
| --- | --- |
| `POST /api/orders` | 30 |
| `POST /api/orders/cancel` | 60 |
| `POST /api/orders/cancel-all` | 30 |
| Account reads | 120 |

Re-quote on price moves rather than on a timer.
