---
title: Order signing
sidebar_position: 5
---

# Order signing

Every message is signed with SEP-53:

```text
signature = ed25519(sha256("Stellar Signed Message:\n" + message))
```

Send it as base64.

## Orders

```text
<network passphrase>|place_order|<pubkey hex>|<market_id>|<is_long 0/1>|<size>|<limit_price>|<reduce_only 0/1>|<nonce>|<expiry_ts>
```

Example:

```text
Test SDF Network ; September 2015|place_order|403074f465f427f58ce06adf008069c5e9bb34d8e43e735350ee9d70b26bcd09|1|1|10000000|205000000000000000|0|1780061000000|1780064600
```

`pubkey hex` is the lowercase hex of your ed25519 key. Numbers are plain decimals. The gateway rebuilds these exact bytes on-chain, so one wrong character means the order never settles. The reference code is `orderSettlementMessage` in `client/lib/market/signing-message.ts`.

## Cancel

```text
domain=kryon.perps
action=cancel_order
network=<network passphrase>
owner=<address>
nonce=<nonce>
```

## Cancel all

```text
domain=kryon.perps
action=cancel_all
network=<network passphrase>
owner=<address>
market_id=<id or all>
issued_at=<unix seconds>
```

`issued_at` must be within 60 seconds of `GET /api/time`.
