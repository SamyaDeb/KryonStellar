---
title: Security mechanisms
sidebar_position: 2
---

# Security mechanisms

| Area | Mechanism | Where |
| --- | --- | --- |
| Orders | ed25519 verification of the exact order bytes | Order gateway |
| Replay | `Filled(owner, nonce)` running total | Order gateway |
| Cancels | Tombstones that outlive any fillable order | Order gateway |
| Prices | Publisher auth, age, confidence, monotonic time | Oracle adapter |
| Trades | Gateway-only position changes, price band, margin after every step | Engine |
| Custody | Credit after transfer in, debit before transfer out | Vault |
| Withdrawals | Equity check from stored state | Vault |
| Liquidation | Health before and after, no self-liquidation | Liquidation |
| Exposure | 16 positions per account, OI caps | Engine |
| Pause | Guardian can pause, only admin can unpause | Vault, gateway, governance |
| Upgrades | Admin only, optionally behind a 48 h timelock | All |
| Services | Separate key per role, secret leak checks | `client/scripts` |
| API | Rate limits, body limits, signed cancels | `client/app/api` |
| CI | Lint, type checks, tests, CodeQL, dependency review | `.github/workflows` |
