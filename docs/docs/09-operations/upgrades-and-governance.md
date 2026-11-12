---
title: Upgrades and governance
sidebar_position: 2
---

# Upgrades and governance

Every contract can be upgraded in place with `upgrade(new_wasm_hash)`. Storage and addresses survive.

## Through governance

Once governance is a contract's admin, changes follow a 48-hour minimum timeline:

1. `queue(id, target, action, args, wasm_hash, eta)`.
2. Wait until `eta`. The guardian can veto with `emergency_pause(true)` and the admin can `cancel`.
3. `execute(id)`.

## Handing over admin

1. The current admin calls `nominate_admin(governance)` on each contract.
2. Governance queues and executes `accept_admin` on each one.
3. Check `admin()` on every contract returns governance.

`client/scripts/governance-handover.ts` automates this and `verify-decentralization.ts` checks the result.
