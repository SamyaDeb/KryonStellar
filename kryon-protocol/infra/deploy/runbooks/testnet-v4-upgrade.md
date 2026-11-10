# Testnet v4: upgrade in place and go live

**Status: NOT EXECUTED.** Prepared 2026-11-11, when Kryon moved to testnet only.
The frontend, scripts and configs already point at v4
(`testnet-deployment-v4.json`). This runbook covers the steps that need
operator keys.

## Where v4 stands (verified on chain 2026-11-11)

| Check | Result |
| --- | --- |
| All 8 contracts live, `upgrade()` exported | yes |
| Admin of all 8 contracts | `GAPMSIT3SPNR7D2B3LXS6QWM5MC7BKUMTZHO2PAV7UFZF4F2QZ3MQUMN` (bare keypair) |
| Governance `min_delay` / guardian | 172800s / `GBQFGV2C…FGHHHM` |
| Vault collateral | USDC active (0bps), USDT0 mock active (500bps haircut) |
| Markets registered on engine | **XLM-PERP only** (market 1) |
| Last oracle price on XLM-PERP | 2026-09-07 — no keepers have run against v4 since |
| Audit fixes from `c4abb66` / `652f967` (ADL, aggregate OI cap, insurance staking, `reduce_bad_debt`, migration) | **missing** — v4 predates them |

The v4 admin's secret is **not** in this machine's Stellar keystore, and the
deploy secrets file (`infra/deploy/testnet-secrets.env`, gitignored) is absent.
v4 was deployed from another machine, so find that key first. Without it, the
only path is a fresh deploy (`client/scripts/testnet-deploy.ts`) and updating
every address again.

## 1. Build the WASM from `main`

```bash
cd kryon-protocol
cargo test --workspace --locked
cargo build --workspace --release --locked --target wasm32v1-none
python3 infra/deploy/optimize-wasm.py --all target/wasm32v1-none/release target/wasm32v1-none/release/deploy
shasum -a 256 target/wasm32v1-none/release/deploy/*.wasm
```

## 2. Dry-run the upgrade

```bash
cd client
DEPLOY_STATE_PATH=../kryon-protocol/infra/deploy/testnet-deployment-v4.json \
PROTOCOL_ADMIN_SECRET=S... npx tsx --env-file=.env.testnet scripts/upgrade-contracts.ts
```

It must report `✓ upgradeable` for all eight and print a WASM hash per
contract. Any `✗ frozen` means you are pointed at the wrong state file.

## 3. Execute

```bash
DEPLOY_STATE_PATH=../kryon-protocol/infra/deploy/testnet-deployment-v4.json \
PROTOCOL_ADMIN_SECRET=S... npx tsx --env-file=.env.testnet scripts/upgrade-contracts.ts --execute
```

Each confirmed upgrade writes its new hash into the state file's `wasm` block
(ttl-keeper.ts reads it). Commit the updated `testnet-deployment-v4.json`.

Then re-check the interface. The new entrypoints must appear:

```bash
stellar contract info interface --id CDUQUDR3S7R6OIPNQ7SRHZEPTYZJPWPMXYKRMTXK3CLJYPEGWVPQXHV7 --network testnet | grep -E "fn (stake|share_price|request_unstake)"
stellar contract info interface --id CDUGOFF3GWFXPYWYH7B3WCS6W7WQX4YTO7HF3ZVI6JBWRJWBOQJPLVSZ --network testnet | grep -E "fn (adl|set_max_total_oi_policy_bps)"
```

## 4. Configure the new code paths

The upgrade does not set the new parameters:

- `set_max_total_oi_policy_bps` on the engine (aggregate OI cap)
- insurance staking parameters, if any are not defaulted
- funding config: `imbalance_coeff` now means premium sensitivity
  (`set-risk-params.ts`)

```bash
PROTOCOL_ADMIN_SECRET=S... npx tsx --env-file=.env.testnet scripts/set-risk-params.ts
```

## 5. Register the other seven markets

Admin is still a keypair, so these submit directly with no timelock:

```bash
npx tsx --env-file=.env.testnet scripts/add-market.ts --all --check
npx tsx --env-file=.env.testnet scripts/add-market.ts --all --dry-run
MARKET_ADMIN_SECRET=S... npx tsx --env-file=.env.testnet scripts/add-market.ts --all
DATABASE_URL=... npx tsx scripts/seed-markets.ts
```

Then widen `NEXT_PUBLIC_ACTIVE_MARKETS` in the web tier's env.

## 6. Start the testnet keeper fleet

`client/.env.testnet` from `.env.testnet.example`. The operator keys must be
the accounts v4 was wired to (`testnet-deployment-v4.json` → `ops`):

| Role | Public key |
| --- | --- |
| oracle publisher | `GA3SSO6D4YL5W6NDCO5V72BN5PHXC3SOBRAFMDSMUOM7OTXY2S6UAUHF` |
| matcher operator | `GC3JI2IC7ROSBFL5GVAIWKMBHV4E6ZUZKHC6N4R37NO4VK3UJTYRK63O` |
| liquidator | `GD7Y6ZHZOVQBLEN64WQUOUDDN2FXXWPHSVRCE4U2L4PKNNTQGRHSWGXY` |
| funding keeper | any funded account distinct from the above |

Keep `PUBLISH_TIME_BACKDATE_SECS=15`. Then:

```bash
(cd ../kryon-protocol && DATABASE_URL=…/kryon_testnet npm run db:migrate:deploy)
pm2 start ecosystem.testnet.config.cjs
npm run production:gate -- --keepers
```

Stop the mainnet fleet (`pm2 delete` the `kryon-*` mainnet processes from
`ecosystem.config.cjs`) so it stops burning fees and firing alerts.

## 7. Web tier env on the VM

`client/.env.local` / `.env.production.local` on the box. **A leftover
`NEXT_PUBLIC_STELLAR_NETWORK=mainnet` now fails the build on purpose**, so do
this before merging, or the deploy keeps the previous bundle:

- `NEXT_PUBLIC_STELLAR_NETWORK=testnet`
- delete every `NEXT_PUBLIC_CONTRACT_*`, `NEXT_PUBLIC_ASSET_*`,
  `NEXT_PUBLIC_USDC_ISSUER`, `NEXT_PUBLIC_STELLAR_{RPC_URL,PASSPHRASE,HORIZON_URL}`
  (the baked v4 defaults apply)
- `DATABASE_URL=…/kryon_testnet`, `MATCHER_OPERATOR_SECRET=` the testnet matcher key
- `NEXT_PUBLIC_WS_URL=wss://ws-testnet.kryonprotocol.live`
- `NEXT_PUBLIC_TESTNET_KEEPERS_LIVE=true` once step 6 is healthy (false until then)

GitHub `production` environment: replace `DATABASE_URL` /
`MATCHER_OPERATOR_SECRET` secrets with the testnet ones, and delete the
mainnet `NEXT_PUBLIC_CONTRACT_*` vars (`preflight.yml` no longer reads them).

## 8. Verify

```bash
npx tsx --env-file=.env.testnet scripts/liquidation-drill.ts
curl -fsS https://kryonprotocol.live/api/ready?network=testnet
bash kryon-protocol/infra/a1flex/check-go-live.sh
```

## Later: governance handover

Admin is still the bare key `GAPMSIT3…`. Once stable, hand it to governance
`CD5QPRFE…ZDNL5` with `governance-handover.ts` (see
`governance-admin-transfer.md`). After that, every parameter change goes
through the 48h timelock.

## Mainnet funds

The frontend no longer offers mainnet. Any balances left in the mainnet vault
`CDXGTJQS…LR4J` can only be withdrawn by calling the vault directly (for
example with the Stellar CLI or Stellar Lab).
