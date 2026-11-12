# Documentation audit report

Date: 2026-11-12. Scope: every documentation file in the repository, audited against the contract source, crates, services, API routes, schema, deployment records and CI configuration at commit `f99447d`.

This report records the state **before** the documentation overhaul. The results of the overhaul are in [`documentation-validation.md`](documentation-validation.md).

## 1. Method

1. Inventoried all Markdown, MDX, diagram and image documentation files.
2. Read every contract (`kryon-protocol/contracts/*/src/lib.rs`, 8 455 lines including tests) and both crates in full; extracted public functions, storage keys, events, authorisation checks and cross-contract calls.
3. Read the matcher, settlement library, oracle keeper, state indexer, stats aggregator, liquidation keeper, funding keeper, TTL keeper, reconciler, WebSocket server and monitor; every API route; `client/config`; the Prisma schema and migrations; deployment scripts, manifests and deployment JSON; CI workflows.
4. Ran `cargo test --workspace --locked`: 101 unit tests passed.
5. Compared every factual claim in the existing documentation with the source.

## 2. Existing documentation inventory

| File | Lines | Disposition |
| --- | --- | --- |
| `README.md` | ~320 | Retained; inaccurate sections corrected (see §5) |
| `ARCHITECTURE.md` | 558 | Content moved to `docs/docs/02-architecture`, `03-smart-contracts`; replaced by an index page |
| `docs/README.md` | 42 | Rewritten (structure and documentation standard) |
| `docs/SETTLEMENT_AUTH.md` | 66 | Merged into `04-trading-mechanics/settlement.md`, `03-smart-contracts/order-gateway.md`, `06-developer-guides/order-signing.md`; removed |
| `docs/docs/intro.md` | 72 | Replaced by `index.md`, `01-overview/introduction.md` |
| `docs/docs/architecture/overview.md` | 571 | Replaced by `02-architecture/*` and `03-smart-contracts/overview.md` |
| `docs/docs/architecture/protocol.md` | 86 | Merged into `02-architecture/system-architecture.md`, `onchain-offchain-boundary.md` |
| `docs/docs/architecture/contracts.md` | 145 | Replaced by `03-smart-contracts/*` |
| `docs/docs/architecture/backend.md` | 100 | Replaced by `05-infrastructure/backend-services.md` |
| `docs/docs/architecture/frontend.md` | 97 | Replaced by `05-infrastructure/frontend.md` |
| `docs/docs/architecture/infra.md` | 75 | Replaced by `05-infrastructure/hosting.md` |
| `docs/docs/trading/lifecycle.md`, `order-lifecycle.md` | 184 | Replaced by `04-trading-mechanics/order-lifecycle.md`, `settlement.md` |
| `docs/docs/trading/execution-engine.md` | 81 | Replaced by `04-trading-mechanics/matching.md`, `05-infrastructure/matching-engine.md` |
| `docs/docs/trading/pnl-funding.md` | 108 | Replaced by `positions-and-pnl.md`, `margin-and-leverage.md`, `funding.md` |
| `docs/docs/data/database.md` | 84 | Replaced by `05-infrastructure/database.md` |
| `docs/docs/data/leaderboard.md`, `portfolio.md` | 158 | Merged into `05-infrastructure/indexer.md`, `07-api-reference/rest-api.md` |
| `docs/docs/agents/*.md` (6 files) | 701 | Replaced by `06-developer-guides/trading-bot-guide.md`, `order-signing.md`, `07-api-reference/units-and-precision.md` |
| `docs/docs/api/rest.md`, `websocket.md` | 231 | Replaced by `07-api-reference/*` |
| `docs/docs/operations/*.md` (4 files) | 316 | Replaced by `06-developer-guides/*`, `09-operations/deployment.md` |
| `docs/docs/security.md` | 83 | Replaced by `08-security/*` |
| `docs/docs/scaling.md` | 69 | Replaced by `09-operations/scaling.md` |
| `docs/docs/mainnet-readiness.md` | 97 | Replaced by `09-operations/mainnet-readiness.md` |
| `docs/static/img/architecture-overview.png` | — | Replaced by 33 Excalidraw diagrams; removed |
| `kryon-protocol/README.md` | 81 | Retained; status corrected |
| `kryon-protocol/docs/architecture.md` | 104 | Superseded; replaced by a pointer page |
| `kryon-protocol/docs/security-model.md` | 92 | Superseded; replaced by a pointer page |
| `kryon-protocol/docs/legacy-issues-fixed.md` | 161 | Retained as a historical record with a status note |
| `kryon-protocol/docs/multi-collateral-runbook.md` | 244 | Retained in place; linked from the runbook index |
| `kryon-protocol/infra/deploy/runbooks/*.md` (9 files) | 1 050 | Retained in place; indexed in `09-operations/runbooks.md` |
| `kryon-protocol/infra/a1flex/*.md` (4 files) | 1 087 | Retained in place; summarised in `05-infrastructure/hosting.md` |
| `kryon-protocol/infra/{deploy,monitoring,rpc,signers}/README.md`, `prisma/README.md` | 174 | Retained in place; linked |
| `client/README.md` | 51 | Retained; removed route and database wording corrected |
| `client/AGENTS.md`, `client/CLAUDE.md` | 6 | Agent instructions; not documentation; untouched |
| Mermaid diagrams in `architecture/overview.md` (6) | — | Replaced by Excalidraw diagrams |
| ASCII diagrams in `README.md`, `infra.md`, `agents/lifecycle.md` | — | Replaced by Excalidraw diagrams |

Every removed file remains in the Git history.

## 3. Inaccurate or outdated statements

| # | Location | Statement | Actual behaviour (source) |
| --- | --- | --- | --- |
| A1 | `kryon-protocol/README.md` | "Live on Stellar mainnet since 2026-07-07" | Mainnet retired from the product 2026-11-11; testnet only (`config/networks.ts`) |
| A2 | `agents/funding.md` | Vault `CCFVY4…`, engine `CAF5OD…`, gateway `CDGWX…` as current testnet | These are the v2 set (`testnet-deployment-v2.json`); current is v4 |
| A3 | `agents/units.md` | Trade `side` derived from maker-nonce parity | Joined from the taker's order row (`markets/[id]/trades/route.ts`) |
| A4 | `agents/signing.md` | `limit_price = 0` means a market order | Intake rejects price ≤ 0 (`lib/validation.ts`); the gateway also rejects it |
| A5 | `agents/risk.md` and others | Liquidator takes a 25–50 bps liquidation fee | Reward is `max_reward_bps` of closed notional paid by insurance; `liquidation_fee_bps` is unused by `perp-liquidation` |
| A6 | `agents/lifecycle.md` | "A fill in the trades feed is the only proof anything settled" | Fill rows are written before confirmation and deleted on failure; proof is `gateway.filled` or `TxJob CONFIRMED` |
| A7 | `security-model.md` | Liquidation rewards capped to available equity | Capped by bps and insurance balance only |
| A8 | `security-model.md` | Replaced orders lose queue priority; keeper decisions pure and replayable; RPC events ingested by cursor; load/chaos tests | No replace endpoint; no event ingestion (`LedgerCursor`, `ProtocolEvent` have no writer); no such tests in the repository |
| A9 | `security-model.md`, `architecture.md` | Funding from market imbalance | Mark-TWAP versus index premium (`risk-engine/src/funding.rs`) |
| A10 | `architecture/backend.md`, indexer header | Indexer syncs `Position` rows | No component writes `Position` |
| A11 | `operations/local-dev.md` | Matcher "books PnL" | `lib/stats.ts` writer is not called |
| A12 | `operations/env-setup.md` | Matcher and indexer process market 1 only | Both iterate `ACTIVE_MARKETS` (all eight by default) |
| A13 | `architecture/frontend.md`, `README.md`, `client/README.md` | `/leaderboard` page | Removed in `7d921e1` |
| A14 | `architecture/infra.md`, `README.md` | Neon serverless Postgres on Vercel | Self-hosted PostgreSQL and Next.js on an OCI VM behind Cloudflare Tunnel (`lib/sql.ts`, `infra/a1flex/WEB-TIER.md`, `deploy-production.yml`) |
| A15 | `README.md` | Oracle keeper publishes every ~8 s | Fetches every 8 s; publishes on 30 bps deviation or 60 s heartbeat; idles without activity |
| A16 | `README.md` | Internal audit reports in `Audit Reports/`; all findings fixed | Directory does not exist in the repository; no audit evidence present |
| A17 | `README.md` | Guarded oracle with quorum medianisation | Quorum path implemented but unused; every feed is single-source |
| A18 | `README.md` | CI secrets for Cloudflare Workers and Vercel deploys | `deploy-production.yml` deploys over SSH (`VM_SSH_KEY`, `VM_HOST`, `VM_USER`) |
| A19 | `README.md` | Rust tests cover "matcher determinism" | The matcher is TypeScript; no Rust test covers it |
| A20 | `docs/SETTLEMENT_AUTH.md` | Frontend live-path switch is a remaining step | Implemented (`lib/market/matcher.ts` signs the settlement message) |
| A21 | `docusaurus.config.ts` | GitHub link `SamyaDeb/KryonV2` | Repository remote is `SamyaDeb/KryonStellar` |

## 4. Implementation findings surfaced during the audit

These are code or configuration observations, not documentation errors. They are now documented in [Known limitations](../docs/08-security/known-limitations.md). No code was changed.

| # | Finding | Source |
| --- | --- | --- |
| F1 | `max_open_interest` is registered at 10¹⁸ scale (`PRECISION × units`) while OI is accumulated in 10⁷ size units, making OI caps ≈ 10¹¹ times looser than intended | `client/scripts/add-market.ts:126`, `testnet-deploy.ts:565`, `perp-engine` |
| F2 | The admin of all eight testnet v4 contracts is a plain keypair; governance controls nothing | `infra/deploy/environments/testnet.toml` |
| F3 | Governance's own admin can upgrade governance and change its guardian without delay | `perp-governance` |
| F4 | No script calls `set_fee_config`, `set_fee_collector` or `set_funding_config`; fees are zero and funding cannot accrue unless configured out of band | `client/scripts` |
| F5 | `FundingConfig.imbalance_coeff` produces an absolute index change in price units per hour | `risk-engine/src/funding.rs` |
| F6 | On the signed settlement path `Fill.txHash` keeps the provisional `dbfill…` value | `matcher-service.ts` |
| F7 | A settlement that times out after 60 s but later confirms is rolled back in the database | `lib/stellar/settlement.ts`, `matcher-service.ts` |
| F8 | `Position`, `PnlEvent`, `BalanceChange`, `FundingPayment`, `PortfolioSnapshot` and all operational tables have no writer | repository-wide search |
| F9 | Only `CollateralSeized` is emitted as a contract event | contracts |
| F10 | `testnet.toml` `[risk_limits]` (60 s, 100 bps, 100 bps) differ from values applied by `testnet-deploy.ts` (120 s, 1000 bps, 1000 bps) | manifest vs script |
| F11 | Code comments disagree with code: liquidation keeper header says it tries 100 % → 50 % → 25 %, the ladder is minimum → 50 % → 100 %; `order-intent.ts` and the matcher start-up log describe the auth-entry path as primary; `signing-message.ts` names a golden test (`canonical_digest_matches_offchain_golden`) that does not exist | scripts, lib |
| F12 | Order-book, trades and WebSocket responses round all prices to 4 decimals | API routes, `ws-server.ts` |

## 5. Missing documentation (before)

- Per-contract references with complete function, storage and error tables.
- Cross-contract call graph and authorisation matrix.
- Funding formula after the move to the premium model, including units.
- Precise on-chain versus off-chain guarantee statement.
- Settlement failure and rollback semantics, and what each record proves.
- Implementation status per feature.
- Privileged role holders on the live deployment.
- Emergency control effects (for example, that pausing the vault halts liquidation).
- Index of the operational runbooks.
- Diagram sources (the single architecture PNG had no editable source).

## 6. Duplicate documentation

`ARCHITECTURE.md` and `docs/docs/architecture/overview.md` were near-identical. `trading/lifecycle.md` and `trading/order-lifecycle.md` overlapped. `agents/*` repeated the REST API and signing content. `kryon-protocol/docs/architecture.md` duplicated the contract list in both READMEs.

## 7. Missing diagrams

The repository contained one raster architecture diagram, six Mermaid diagrams and several ASCII sketches. None covered storage, authorisation, oracle validation, liquidation, insurance flows, settlement rollback, indexing, database writers, trust boundaries, privileged roles or emergency procedures. All 33 requested diagrams were created.
