---
title: Governance
sidebar_position: 9
---

# Governance

`perp-governance` puts a delay of at least 48 hours in front of admin actions. Once it is a contract's admin, every change to that contract goes through queue, wait, execute, and the guardian can veto.

## Public functions

| Function | Caller | What it does |
| --- | --- | --- |
| `queue(id, target, action, args, wasm_hash, eta)` | admin | Queues a call, `eta` at least `min_delay` away |
| `execute(id)` | admin | Runs the call after `eta` |
| `cancel(id)` | admin | Drops a queued call |
| `emergency_pause(paused)` | guardian | Blocks or unblocks `execute` |
| `set_guardian(guardian)` | admin | |
| `min_delay()`, `guardian()`, `paused()`, `proposal(id)` | anyone | Views |
| `initialize(admin, guardian, min_delay_secs)` | admin | `min_delay_secs` at least 172,800 |
| `upgrade`, `nominate_admin`, `accept_admin`, `admin`, `pending_admin` | admin / nominee | |

See [Upgrades and governance](../09-operations/upgrades-and-governance.md) for the handover process.
