---
title: Contract calls
sidebar_position: 4
---

# Contract calls

Reads are free: simulate a transaction from any account.

| Read | Contract | Function |
| --- | --- | --- |
| Account health | Vault | `account_health(user, usdc)` |
| Balance | Vault | `balance_of(user, asset)` |
| Positions | Engine | `positions(user)` |
| Funding | Engine | `funding_state(market_id)` |
| Oracle price | Oracle adapter | `get_price(asset, null)` |
| Order fill | Gateway | `filled(owner, nonce)` |

```ts
import { Account, Address, Contract, Keypair, TransactionBuilder, scValToNative, rpc } from "@stellar/stellar-sdk";

const server = new rpc.Server("https://soroban-testnet.stellar.org");
const vault = new Contract("CCWDYVNAYWU3IWKC2KJJ5MFTPHUBXOZU5CKGEH5S4DAKGX3HUFHQDJGF");
const USDC = "CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA";

const tx = new TransactionBuilder(new Account(Keypair.random().publicKey(), "0"), {
  fee: "100", networkPassphrase: "Test SDF Network ; September 2015",
})
  .addOperation(vault.call("account_health", new Address(user).toScVal(), new Address(USDC).toScVal()))
  .setTimeout(30)
  .build();

const sim = await server.simulateTransaction(tx);
if (rpc.Api.isSimulationSuccess(sim)) console.log(scValToNative(sim.result!.retval));
```

## Writes

| Action | Call | Signed by |
| --- | --- | --- |
| Deposit | `vault.deposit(user, asset, amount)` | you |
| Withdraw | `vault.withdraw(user, asset, amount)` | you |
| Cancel on-chain | `gateway.cancel_order(owner, nonce, expiry_ts)` | you |

Build with your account as source, simulate, assemble, sign and send. Struct arguments are encoded as maps with keys in alphabetical order, and `i128`, `u64` and `u32` need explicit types.
