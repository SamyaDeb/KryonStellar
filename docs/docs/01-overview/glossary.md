---
title: Glossary
sidebar_position: 2
---

# Glossary

## Units

| Quantity | Scale | Example |
| --- | --- | --- |
| Price | 10^18 | 0.2038 USDC per XLM is `203800000000000000` |
| Size | 10^7 | 100 XLM is `1000000000` |
| Token amount | 10^7 | 50 USDC is `500000000` |
| Notional | size x price / 10^18 | in USDC units |
| Basis point (bps) | 1 / 10,000 | 1000 bps is 10 % |

All contract math uses checked 128-bit integers. Products are computed in 256 bits before dividing, and division rounds toward zero.

## Terms

| Term | Meaning |
| --- | --- |
| Equity | Collateral value plus unrealised PnL and accrued funding |
| Initial margin (IM) | Notional x initial margin bps. Equity must stay above it after a trade or withdrawal. |
| Maintenance margin (MM) | Notional x maintenance margin bps. Below it, an account can be liquidated. |
| Execution band | The allowed fill range: oracle price plus or minus the market's deviation bps |
| Mark price | Time-weighted average of fill prices since the last funding update |
| Index price | The oracle price |
| Funding index | Running funding per unit of size, one per side |
| Maker / taker | The older order in a match is the maker; the newer one is the taker |
| Nonce | A u64 you choose per order, unique across all your orders |
| Tombstone | An on-chain cancel record that blocks any further fills |
| Haircut | Discount applied to a collateral asset's value |
| Bad debt | A loss larger than the account's collateral and the insurance pool |
| SEP-53 | Stellar's signed-message format: ed25519 over sha256("Stellar Signed Message:\n" + message) |
| TTL | How long Soroban keeps a storage entry live before archiving it |
