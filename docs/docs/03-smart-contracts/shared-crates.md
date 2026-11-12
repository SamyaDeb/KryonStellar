---
title: Shared crates
sidebar_position: 10
---

# Shared crates

## protocol-core

Fixed-point math, shared types, oracle validation and errors.

| Function | Meaning |
| --- | --- |
| `mul_div(a, b, d)` | a x b / d in 256 bits, then back to i128 |
| `mul_precision`, `div_precision` | multiply or divide by 10^18 |
| `apply_bps(amount, bps)` | amount x bps / 10,000 |
| `notional(size, price)` | size x price / 10^18 |
| `signed_position_pnl(position, mark)` | price PnL for a position |
| `funding_pnl(position, index)` | -size x (index - last index) / 10^18 |
| `collateral_value_after_haircut(value, bps)` | value less haircut |

Division rounds toward zero.

## risk-engine

| Function | Meaning |
| --- | --- |
| `account_health(env, account, markets)` | equity, IM, MM, margin ratio, liquidatable |
| `validate_withdrawal(env, account, markets, value)` | equity minus value must stay above IM |
| `update_from_premium(cfg, state, premium, now)` | advances funding indexes |
| `premium_from_mark(mark, index)` | (mark - index) / index |
| `plan_liquidation(env, account, markets, position_id, bps)` | smallest close that restores health |
