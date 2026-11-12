---
title: Order gateway
sidebar_position: 4
---

# Order gateway

`perp-order-gateway` is the only way into a trade. It checks that both traders signed what is being filled, then drives the engine for each side.

## Public functions

| Function | Caller | What it does |
| --- | --- | --- |
| `settle_fill_signed(fill, maker_sig, taker_sig)` | operator | Settles a fill using the traders' order signatures |
| `settle_fill(fill)` | operator + both owners | Same, using Soroban auth entries |
| `cancel_order(owner, nonce, expiry_ts)` | owner | Writes a tombstone kept for at least 7 days |
| `reclaim_order_state(owner, nonces)` | anyone | Prunes records of long-expired orders |
| `filled(owner, nonce)`, `is_cancelled(owner, nonce)` | anyone | Order state |
| `emergency_pause(caller)` | admin or guardian | Stops settlement |
| `unpause()`, `is_paused()` | admin / anyone | |
| `set_operator`, `set_engine`, `set_domain`, `set_guardian` | admin | Config |
| `operator()`, `domain()`, `guardian()` | anyone | |
| `extend_instance_ttl()` | anyone | |
| `initialize(admin, engine)` | admin | |
| `upgrade`, `nominate_admin`, `accept_admin`, `admin`, `pending_admin` | admin / nominee | |

## What it checks

| Check | Error |
| --- | --- |
| Both signatures verify | host error |
| Maker and taker differ | `SelfTrade` |
| Same market, opposite sides | `InvalidConfig`, `DirectionMismatch` |
| Not expired, and expiry within 7 days | `OrderExpired` |
| Not cancelled on-chain | `OrderCancelled` |
| Filled so far + fill size within order size | `OrderOverfilled` |
| Fill price no worse than either limit | `PriceOutsideBand` |

## Signed message

```text
<network passphrase>|place_order|<pubkey hex>|<market_id>|<is_long 0/1>|<size>|<limit_price>|<reduce_only 0/1>|<nonce>|<expiry_ts>
```

Signed with SEP-53. The passphrase makes a signature useless on any other network. See [Order signing](../06-developer-guides/order-signing.md).

## Per side

For each side the gateway reduces any opposite position first, opens the rest on the new side unless the order is reduce-only, otherwise increases or opens. Then it charges the fee and records the fill.
