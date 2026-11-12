---
title: Collateral
sidebar_position: 7
---

# Collateral

| Asset | Haircut | Role |
| --- | --- | --- |
| USDC | 0 bps | Settlement. PnL, fees and funding are paid in USDC. |
| USDT0 | 500 bps | Margin |

## Deposit

1. Hold the asset. USDC needs a trustline to its issuer.
2. Call `vault.deposit(user, asset, amount)`.

## Withdraw

Call `vault.withdraw(user, asset, amount)`. It goes through if your equity after the withdrawal is still above initial margin, using live prices.

## Other collateral and losses

Losses are always booked in USDC. If you margin with USDT0, your USDC balance can go negative while your USDT0 still covers it. The vault converts USDT0 into USDC credit to settle that deficit, most liquid asset first and valued after its haircut. This happens during liquidations and can be triggered at any time by you or our keeper with `settle_deficit`.
