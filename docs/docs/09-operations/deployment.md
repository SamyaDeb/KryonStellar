---
title: Deployment
sidebar_position: 1
---

# Deployment

## Contracts

```bash
cd kryon-protocol
cargo build --release --target wasm32v1-none
python3 infra/deploy/optimize-wasm.py --all target/wasm32v1-none/release target/wasm32v1-none/release/deploy
```

`client/scripts/testnet-deploy.ts` deploys and wires all eight contracts, sets up USDC, the oracle feeds and the first market. Add markets with `add-market.ts` and set risk parameters with `npm run risk:params`. Record addresses in `kryon-protocol/infra/deploy/` and `client/config/networks.ts` together.

Upgrades keep the same addresses: `npm run contracts:upgrade`.

## Database

```bash
cd kryon-protocol && npm run db:migrate:deploy
cd client && npm run db:seed-markets
```

## App and services

Pushes to `main` deploy the web tier automatically. Services run under PM2:

```bash
cd client && pm2 start ecosystem.testnet.config.cjs
```

Run `ttl-keeper.ts` once a day from cron.

## Before going live

1. All tests and builds pass.
2. App, keepers and deployment records name the same contracts.
3. Every market and collateral asset has a live price.
4. Operator accounts hold enough XLM.
5. `ALERT_WEBHOOK_URL` is set.
6. `GET /api/ready` returns `ok: true`.
