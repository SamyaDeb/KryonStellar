---
title: Error codes
sidebar_position: 11
---

# Error codes

Every contract returns `CoreError`. A failed simulation shows it as `Error(Contract, #code)`.

| Code | Name | Usually means |
| --- | --- | --- |
| 1 | `MathOverflow` | Arithmetic overflow |
| 2 | `DivisionByZero` | Division by zero |
| 3 | `InvalidAmount` | Zero or negative size, price or amount |
| 4 | `InvalidPrice` | Bad oracle price |
| 5 | `InvalidConfig` | Missing or invalid configuration |
| 6 | `StaleOracle` | Price too old or out of order |
| 7 | `OracleConfidenceTooWide` | Price too uncertain |
| 8 | `AccountInsolvent` | Reserved |
| 9 | `InsufficientCollateral` | Below initial margin |
| 10 | `NotLiquidatable` | Account is healthy |
| 11 | `Unauthorized` | Wrong caller, or contract paused |
| 12 | `AlreadyInitialized` | Already set up, or migration sealed |
| 13 | `AssetDisabled` | Collateral not active |
| 14 | `PositionNotFound` | Unknown position |
| 15 | `DirectionMismatch` | Both orders on one side |
| 16 | `PriceOutsideBand` | Outside the limit or oracle band |
| 17 | `OpenInterestExceeded` | Market open interest cap |
| 18 | `LiquidationWouldNotImproveHealth` | Liquidation did not help |
| 19 | `InsuranceFundInsufficient` | Insurance cap or balance |
| 20 | `OrderExpired` | Past expiry, or expiry too far out |
| 21 | `OrderCancelled` | Cancelled on-chain |
| 22 | `OrderOverfilled` | Fill exceeds order size |
| 23 | `SelfTrade` | Same account on both sides |
| 24 | `OracleQuorumNotMet` | Not enough sources |
| 25 | `OracleDeviationTooWide` | Sources disagree |
| 26 | `DuplicateOracleSource` | Source repeated |
| 27 | `TooManyPositions` | 16 positions already open |
| 28 | `DepositCapExceeded` | Over the deposit cap |
| 29 | `IsolatedMarginDisabled` | Isolated mode requested |
| 30 | `AggregateOiPolicyExceeded` | OI policies over the shared ceiling |
| 31 | `NoBadDebtToOffset` | Nothing for ADL to pay down |
| 32 | `PositionNotInProfit` | ADL target is not in profit |
