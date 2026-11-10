---
id: contracts
title: Soroban Contract Architecture
sidebar_position: 2
---

# Soroban Contract Architecture

Contracts live in `kryon-protocol/contracts/` and share types via
`crates/protocol-core` and `crates/risk-engine`. All are `#![no_std]` Soroban
contracts.

## Deployed addresses (Stellar testnet, v4)

Kryon runs on Stellar testnet. The live set was deployed 2026-09-07 and is
recorded in `kryon-protocol/infra/deploy/testnet-deployment-v4.json`. Every
contract exposes `upgrade()`, so new builds are installed in place with
`client/scripts/upgrade-contracts.ts` and the addresses do not change.

| Contract | Address |
| --- | --- |
| Governance | `CD5QPRFE6ND6UIJDDIR3Z2I4DNLN4TXT4CTFOIFCN7IY33YO424ZDNL5` |
| Oracle Adapter | `CDOAKTFECPGLX54H6ST3O3LT6476O27S67W26NYEOC7WDRY4GWCEZQZE` |
| Vault | `CCWDYVNAYWU3IWKC2KJJ5MFTPHUBXOZU5CKGEH5S4DAKGX3HUFHQDJGF` |
| Engine | `CDUGOFF3GWFXPYWYH7B3WCS6W7WQX4YTO7HF3ZVI6JBWRJWBOQJPLVSZ` |
| Order Gateway | `CCGDR2SWS7OMHT6T37YDWLHST5C4ZZI6K2N2WU6D47TXKCKCKLYF7SNB` |
| Insurance | `CDUQUDR3S7R6OIPNQ7SRHZEPTYZJPWPMXYKRMTXK3CLJYPEGWVPQXHV7` |
| Liquidation | `CDJ2ASKLIXRMDM3SWKTLWW7GOXJYMHGZMO5GYCGOXLA6R3FFN5MGJZ7G` |
| Risk | `CAR5JGY4DMZOWZYK27EBB5IWNOMIG5AD5CGYTZI2URFGB4ABUGRLC5MY` |

Collateral and settlement assets:

| Asset | Contract |
| --- | --- |
| USDC (testnet SAC, settlement) | `CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA` |
| USDC issuer | `GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5` |
| USDT0 (mock, margin only, 500bps haircut) | `CCXWM7LWNT4VDRUJ4KZILV6KB7SXWDWDBF5TT65E5IRDEX7QZTDMNLRO` |
| XLM (native SAC) | `CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC` |

These are baked into `client/config/networks.ts` and can be overridden with
`NEXT_PUBLIC_CONTRACT_*` environment variables.

A trial **mainnet** deployment (2026-07-07, recorded in
`kryon-protocol/infra/deploy/mainnet-deployment.json`) was retired on
2026-11-11: its contracts predate `upgrade()` and can never be patched. See
`kryon-protocol/infra/deploy/runbooks/mainnet-migration.md`.

## Authorisation graph

Each contract enforces *who may call it*:

```
admin ───────────────▶ (initialize, set_* config on every contract)
operator ────────────▶ Order Gateway.settle_fill
Order Gateway ───────▶ Engine.open/increase/reduce_position, charge_trade_fee
Engine ──────────────▶ Vault.apply_pnl, lock/release margin
Liquidation ─────────▶ Engine.liquidate
trader (Freighter) ──▶ Vault.deposit / withdraw,  Gateway.cancel_order
oracle publisher ────▶ Oracle Adapter.write_price
```

Key property: **the engine and vault trust only their authorised callers**, not
end users. `Engine.open_position` requires `require_order_gateway()`;
`Vault.apply_pnl` requires `require_engine()`. End-user authority is required
only where the user spends their own funds (deposit/withdraw) or revokes their
own order (cancel).

## Order Gateway — `settle_fill`

The gateway is the settlement entry point. Its core function:

```rust
pub fn settle_fill(env: Env, fill: MatchedFill) -> Result<FillReceipt, CoreError> {
    require_operator(&env)?;        // trusted-operator auth
    validate_fill(&env, &fill)?;    // price band, expiry, cancellation, overfill,
                                    // self-trade, direction, market match
    settle_user_side(&env, /* maker */ ...)?;  // reduce/close then open residual
    engine_charge_trade_fee(...)?;             // maker fee
    settle_user_side(&env, /* taker */ ...)?;
    engine_charge_trade_fee(...)?;             // taker fee
    // record cumulative filled size per (owner, nonce) for overfill protection
}
```

### `settle_user_side`

For each side the gateway derives the position effect from existing positions:

- **Opposite-side position exists** → `reduce_position` up to `min(posSize,
  fillSize)`; any residual `open_position` in the new direction (unless
  `reduce_only`).
- **Same-side position exists** → `increase_position` (VWAP entry).
- **No position** → `open_position` (rejected if `reduce_only`).

This is what makes a market collapse to a **single position row per
(trader, market)** with a volume-weighted entry price.

### Trusted-operator model

`settle_fill` historically required both maker and taker to sign their auth
entries. This blocked automatic settlement (each side had to approve in their
wallet). It was replaced with `require_operator(&env)`: a single trusted
operator (the matcher fee-payer, set via `set_operator`) authorises settlement.

On-chain validation still fully protects users — the operator can only settle
fills consistent with the limit price, expiry, and cancellation state of orders
the traders actually submitted. See [Security](/security) for the trade-offs.

## Engine

- `positions(user) -> Vec<Position>` — read model used by the gateway and FE.
- `open_position / increase_position / reduce_position` — gateway-only mutators
  that maintain open interest, funding index snapshots, and call
  `sync_and_require_initial_margin`.
- `charge_trade_fee` — applies maker/taker fees via the vault.
- Margin is held at the **vault** account level (cross-margin); `position.margin`
  is always `0` — never read it. Leverage/liq-price derive from account equity.

## Vault

- `deposit / withdraw` — user-authorised collateral movement.
- `apply_pnl` — engine-only; credits/debits realized PnL and fees.
- `account_health(user, asset)` → `{ collateral_value, unrealized_pnl, equity,
  initial_margin_required, maintenance_margin_required, free_collateral,
  margin_ratio, liquidatable }`. This struct drives the entire margin/PnL UI.

## Oracle Adapter

`write_price(asset, publisher, price, confidence, timestamp)` — guarded by
`OracleGuard { max_age_secs, max_confidence_bps }`. The engine rejects trades
against stale prices (default `max_age = 60s`), which is why the keeper
publishes every 8s.

## Building & redeploying

```bash
cd kryon-protocol
cargo test -p perp-order-gateway          # run contract tests
cargo build --target wasm32-unknown-unknown --release -p perp-order-gateway
stellar contract optimize --wasm target/wasm32-unknown-unknown/release/perp_order_gateway.wasm
stellar contract deploy --wasm <optimized.wasm> --source <key> --network testnet
```

See [Deployment](/operations/deployment) for the full sequence (upload → deploy
→ initialize → set_operator → rewire engine).
