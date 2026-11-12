# Kryon · Frontend

Stellar/Soroban perpetual-futures DEX terminal (Next.js 16 + React 19). Launch market: **XLM-PERP**, USDC-settled, on Stellar **testnet**.

## Prerequisites

- [Bun](https://bun.sh)
- [Freighter](https://freighter.app) wallet, set to **Stellar Testnet**
- A desktop / large screen (≥ 1024px), the terminal is desktop-first

## Setup

```bash
bun install
```

Create `.env` (Next.js) **and** `.env.local` (the off-chain scripts read this):

```ini
DATABASE_URL="postgresql://…"                               # any PostgreSQL (Neon URLs supported)
ORACLE_PUBLISHER_SECRET="S…"                                 # authorized oracle publisher key
```

Order & market data uses the app's own `/api` routes (same-origin), no matcher/indexer URL needed.

## Run

```bash
bun run dev        # http://localhost:3000  →  /trade/XLM-PERP
```

### Off-chain services (run for live prices & fills)

```bash
bun run dev:oracle     # publish XLM price on-chain (~8s)
bun run dev:matcher    # match orders + settle fills on-chain
bun run dev:indexer    # sync on-chain state → DB
```

## Other

```bash
bun run build && bun run start   # production
bun run lint
```

## Routes

- `/trade/[market]`: trading terminal (e.g. `/trade/XLM-PERP`)
- `/portfolio`: account overview
- `/markets`: market list
- `/docs`: documentation (built from `../docs`)

Full service, API and configuration reference: [`docs/docs/05-infrastructure`](../docs/docs/05-infrastructure/backend-services.md), [`docs/docs/07-api-reference`](../docs/docs/07-api-reference/rest-api.md) and [`docs/docs/06-developer-guides`](../docs/docs/06-developer-guides/local-development.md).
