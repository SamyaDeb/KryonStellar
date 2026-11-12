---
title: Markets
sidebar_position: 10
---

# Markets

| Market | ID | Max leverage | Price decimals | Size decimals | Tick |
| --- | --- | --- | --- | --- | --- |
| XLM-PERP | 1 | 10x | 4 | 4 | 0.0001 |
| BTC-PERP | 2 | 50x | 1 | 4 | 0.1 |
| ETH-PERP | 3 | 20x | 2 | 3 | 0.01 |
| SOL-PERP | 4 | 10x | 2 | 3 | 0.01 |
| XRP-PERP | 5 | 10x | 4 | 1 | 0.0001 |
| ADA-PERP | 6 | 5x | 4 | 1 | 0.0001 |
| BNB-PERP | 7 | 10x | 2 | 3 | 0.01 |
| TRX-PERP | 8 | 5x | 5 | 0 | 0.00001 |

All markets are quoted and settled in USDC. `GET /api/markets` returns the live list with every parameter.

## Parameters

| Parameter | Effect |
| --- | --- |
| `initial_margin_bps`, `maintenance_margin_bps` | Margin requirements |
| `max_open_interest` | Cap on total open size |
| `max_oracle_age_secs`, `max_oracle_confidence_bps` | Oracle guard |
| `max_execution_deviation_bps` | Price band around the oracle |
| Fee config | Maker and taker bps |
| Funding config | Coefficient and max hourly rate |
| OI policy | Cap relative to the insurance fund |

New markets are added with `client/scripts/add-market.ts`.
