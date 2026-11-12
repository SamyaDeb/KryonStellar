---
title: Contract development
sidebar_position: 3
---

# Contract development

The toolchain is pinned in `kryon-protocol/rust-toolchain.toml` (Rust 1.89, target `wasm32v1-none`).

```bash
cd kryon-protocol
cargo test --workspace
cargo build --workspace --release
python3 infra/deploy/optimize-wasm.py --all target/wasm32v1-none/release target/wasm32v1-none/release/deploy
```

## Adding an entry point

1. Add an explicit auth check: admin, a peer contract, or the caller's `require_auth`.
2. Return `CoreError`. Add new variants at the end so existing codes stay stable.
3. Test the happy path and every rejection.
4. Update any `invoke_contract` callers and the client encoding in `client/lib/stellar`.

## Upgrading

Every contract has `upgrade(new_wasm_hash)`. Upload the new WASM, then call `upgrade`, either directly or through a governance proposal. `npm run contracts:upgrade` in `client/` does both. Keep storage keys backward compatible.
