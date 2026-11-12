---
title: Engine
sidebar_position: 3
---

# Engine

`perp-engine` owns positions and market state.

## Public functions

| Function | Caller | What it does |
| --- | --- | --- |
| `open_position(user, market_id, size, is_long, execution_price, mode)` | gateway | New cross-margin position |
| `increase_position(user, position_id, size_delta, execution_price)` | gateway | Settles funding, averages the entry price |
| `reduce_position(user, position_id, size_delta, execution_price)` | gateway | Settles funding, realises PnL |
| `close_position(user, position_id, execution_price)` | gateway | Full reduce |
| `liquidate_reduce(user, position_id, size_delta, execution_price)` | liquidation | Reduce without the margin check |
| `charge_trade_fee(user, market_id, size, execution_price, is_maker)` | fee collector | Maker or taker fee |
| `update_funding(market_id)` | anyone | Advances funding from the premium |
| `positions(user)` | anyone | Account positions |
| `open_interest`, `long_open_interest`, `short_open_interest` | anyone | Per market |
| `funding_state`, `mark_price`, `mark_state` | anyone | Funding and mark |
| `insurance_coverage_bps(market_id)` | anyone | Insurance vs open interest |
| `oi_policy`, `total_oi_policy_bps`, `max_total_oi_policy_bps` | anyone | Insurance-relative OI caps |
| `set_market(config)` | admin | Registers a market and mirrors it to the vault |
| `set_fee_config`, `set_funding_config` | admin | Per market |
| `set_oi_policy`, `set_max_total_oi_policy_bps` | admin | OI caps relative to insurance |
| `set_order_gateway`, `set_fee_collector`, `set_fee_recipient`, `set_vault`, `set_liquidation`, `set_insurance` | admin | Wiring |
| `migrate_import_positions(entries)`, `seal_migration()`, `migration_sealed()` | admin | One-time state import |
| `extend_instance_ttl()` | anyone | |
| `initialize(admin, oracle, vault, settlement_asset)` | admin | |
| `upgrade`, `nominate_admin`, `accept_admin`, `admin`, `pending_admin` | admin / nominee | |

## Checks on every trade

| Check | Error |
| --- | --- |
| Price within oracle +/- `max_execution_deviation_bps` | `PriceOutsideBand` |
| Open interest under `max_open_interest` (open and increase) | `OpenInterestExceeded` |
| Insurance headroom, when an OI policy is set | `InsuranceFundInsufficient` |
| Fewer than 16 positions | `TooManyPositions` |
| Equity at or above initial margin afterwards | `InsufficientCollateral` |

Reductions are never blocked by open interest or insurance limits.

## Mark price

Each trade fill updates a time-weighted mark. `update_funding` reads the average since the last update and starts a new window. Liquidation fills never move the mark.

## Related

- [Positions and PnL](../04-trading-mechanics/positions-and-pnl.md)
- [Funding](../04-trading-mechanics/funding.md)
