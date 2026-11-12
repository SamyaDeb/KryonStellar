---
title: Local development
sidebar_position: 1
---

# Local development

You need Node 22, a PostgreSQL database and Freighter. Rust is only needed for contract work.

```bash
cd client
npm install
cp .env.local.example .env.local      # set DATABASE_URL and any keys
npm run db:seed-markets
npm run dev                           # http://localhost:3000
```

Start the services you need in separate terminals:

```bash
npm run dev:oracle
npm run dev:indexer
npm run dev:matcher
npm run dev:ws
```

To try a trade, fund two accounts, deposit USDC into the vault from each, and cross a buy and a sell within 10 % of the oracle price.

## Checks

```bash
cd client && npm run lint && npx tsc --noEmit && npm test && npm run build
cd kryon-protocol && cargo fmt --all -- --check && cargo clippy --workspace --all-targets -- -D warnings && cargo test --workspace
cd docs && npm run build
```

## Tips

- Give every signing service its own key.
- Treat amounts as integers: `BigInt` in TypeScript, `numeric` in SQL.
- Read `NEXT_PUBLIC_` variables as literal `process.env.NEXT_PUBLIC_X` so Next.js can inline them.
