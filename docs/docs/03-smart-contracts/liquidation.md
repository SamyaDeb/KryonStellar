---
title: Liquidation
sidebar_position: 6
---

# Liquidation

`perp-liquidation` reduces unhealthy accounts and pays the liquidator.

## Public functions

| Function | Caller | What it does |
| --- | --- | --- |
| `liquidate(liquidator, user, position_id, close_size, execution_price)` | anyone but the user | Liquidates part or all of a position |
| `adl(keeper, counterparty, position_id, close_size, execution_price)` | anyone | Reduces a profitable position to pay down bad debt |
| `max_reward_bps()`, `set_max_reward_bps(bps)` | anyone / admin | Liquidator reward, capped at 1000 bps |
| `set_engine`, `set_vault`, `set_insurance` | admin | Wiring |
| `initialize(admin, engine, vault, insurance, settlement_asset, max_reward_bps)` | admin | |
| `upgrade`, `nominate_admin`, `accept_admin`, `admin`, `pending_admin` | admin / nominee | |

## Liquidate

1. The account must be liquidatable.
2. The engine reduces the position inside the oracle band.
3. Health must improve: a higher margin ratio, or a lower maintenance requirement if equity is negative.
4. The liquidator is paid `close notional x max_reward_bps` from the insurance pool.
5. Other collateral covers any negative settlement balance. If equity is still negative, insurance covers it and any remainder is recorded as bad debt.

## Auto-deleveraging

`adl` only runs when bad debt is recorded and only against a position in profit. The close size is capped so the realised gain cannot exceed the bad debt, which is then reduced by that gain.
