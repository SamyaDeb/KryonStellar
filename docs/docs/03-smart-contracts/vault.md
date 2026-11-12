---
title: Vault
sidebar_position: 2
---

# Vault

`perp-vault` holds every collateral token, keeps each account's balances, and decides whether an account is healthy.

## Public functions

| Function | Caller | What it does |
| --- | --- | --- |
| `deposit(user, asset, amount)` | user | Transfers tokens in, then credits the balance. Checks the asset is listed and under its deposit cap. |
| `withdraw(user, asset, amount)` | user | Checks equity after the withdrawal stays above initial margin, debits, then transfers out. |
| `balance_of(user, asset)` | anyone | Internal balance. Can be negative after losses. |
| `account_health(user, asset)` | anyone | Equity, margin requirements and liquidation status |
| `collateral(asset)` | anyone | Listed collateral config |
| `apply_pnl(user, asset, pnl)` | engine | Credits or debits a balance |
| `sync_positions(user, positions)` | engine | Stores the account's positions |
| `set_funding_indexes(market_id, long, short)` | engine | Stores funding indexes |
| `seize_for_deficit(user, deficit_asset)` | liquidation | Covers a negative balance from other collateral |
| `absorb_bad_debt(user, asset)` | liquidation | Draws insurance for what is left, records the rest as bad debt |
| `settle_deficit(caller, user, asset)` | owner or operator | Seizure outside a liquidation |
| `emergency_pause(caller)` | admin or guardian | Pauses deposits, withdrawals and PnL |
| `unpause()`, `is_paused()` | admin / anyone | |
| `set_collateral(asset, oracle_asset, haircut_bps, active)` | admin | List collateral |
| `set_deposit_cap(asset, cap)`, `deposit_cap`, `total_deposited` | admin / anyone | Per-asset cap |
| `set_market_config(config)` | admin | Market risk parameters, set through the engine |
| `set_engine`, `set_oracle`, `set_insurance`, `set_liquidation`, `set_guardian`, `set_operator` | admin | Wiring |
| `guardian()`, `operator()` | anyone | |
| `migrate_import_balances(entries)`, `seal_migration()`, `migration_sealed()` | admin | One-time state import |
| `extend_instance_ttl()` | anyone | Keeps the instance live |
| `initialize(admin, oracle, engine)` | admin | |
| `upgrade`, `nominate_admin`, `accept_admin`, `admin`, `pending_admin` | admin / nominee | |

## Collateral seizure

When the settlement balance goes negative, the vault reassigns the account's other collateral to cover it, most liquid (lowest haircut) first, valued after haircut and rounded down. Tokens stay put; only the internal claims move. It emits `CollateralSeized { user, deficit_asset, credited, uncovered_value }`.

## Pause

A paused vault blocks `deposit`, `withdraw`, `settle_deficit` and `apply_pnl`. Since every trade and liquidation books PnL, pausing the vault stops trading too.

## Related

- [Collateral](../04-trading-mechanics/collateral.md)
- [Margin](../04-trading-mechanics/margin-and-leverage.md)
