/**
 * Network configuration registry.
 *
 * Kryon runs on Stellar TESTNET only. Mainnet was a trial deployment: its
 * contracts predate `upgrade()` and can never be patched (see
 * kryon-protocol/infra/deploy/runbooks/mainnet-migration.md), so it was dropped
 * from the product on 2026-11-11. The mainnet record lives on in
 * kryon-protocol/infra/deploy/mainnet-deployment.json for anyone who needs to
 * reach those contracts with the standalone scripts/mainnet-*.ts tools.
 *
 * The multi-network shape (NetworkId, NETWORKS, getNetworkConfig) is kept so
 * that adding a network back later is a data change, not a refactor. All of
 * these values are public (contract ids, RPC endpoints, network passphrases).
 *
 * ── The env-inlining trap (do not "clean this up") ───────────────────────────
 * Every `process.env.NEXT_PUBLIC_X` read MUST be written as a literal member
 * expression. Next.js inlines these into the client bundle by *static textual
 * substitution*; a computed key (`process.env[key]`) is not substituted and
 * silently becomes `undefined` in the browser. This cost a day on 2026-07-08,
 * when an `envOrDefault(key, fallback)` helper did exactly that.
 *
 * ── Env overrides ────────────────────────────────────────────────────────────
 * The `NEXT_PUBLIC_*` overrides below let an operator repoint a deployment at
 * freshly redeployed contracts without a code change. Unset, the baked
 * defaults apply.
 */

export const NETWORK_IDS = ["testnet"] as const;
export type NetworkId = (typeof NETWORK_IDS)[number];

export function isNetworkId(value: unknown): value is NetworkId {
  return typeof value === "string" && (NETWORK_IDS as readonly string[]).includes(value);
}

// A process (keeper, script, build) still configured for mainnet must not
// silently run against testnet addresses — it would be pointed at the wrong
// chain without knowing it. Fail loudly instead.
const REQUESTED_NETWORK = process.env.NEXT_PUBLIC_STELLAR_NETWORK;
if (REQUESTED_NETWORK && !isNetworkId(REQUESTED_NETWORK)) {
  throw new Error(
    `NEXT_PUBLIC_STELLAR_NETWORK="${REQUESTED_NETWORK}" is not supported. ` +
      `Kryon runs on testnet only; set NEXT_PUBLIC_STELLAR_NETWORK=testnet.`
  );
}

/** The deployment's network. Always testnet. */
export const PRIMARY_NETWORK: NetworkId = "testnet";

export interface ContractSet {
  governance: string;
  oracleAdapter: string;
  vault: string;
  engine: string;
  orderGateway: string;
  insurance: string;
  liquidation: string;
  risk: string;
}

export interface AssetSet {
  nativeXlm: string;
  usdc: string;
  usdcIssuer: string;
}

/**
 * A collateral asset the vault accepts.
 *
 * Listing here does NOT make an asset depositable — the vault's own
 * `set_collateral` does. This registry only tells the client which assets are
 * worth asking the chain about; `lib/stellar/collateral.ts` reads the vault and
 * drops anything not actually listed and active, so a config entry can never
 * present a deposit that would revert.
 */
export interface CollateralAsset {
  /** Ticker shown in the UI. */
  code: string;
  /** SAC contract id — what vault deposit/withdraw take as `asset`. */
  contract: string;
  /** Classic issuer account. Null for the native XLM wrapper. */
  issuer: string | null;
  /** Oracle symbol the vault prices this asset under. */
  oracleSymbol: string;
  /** The asset PnL, funding and liquidation settle in. Exactly one is true. */
  settlement: boolean;
  /**
   * Decimals to round withdrawals down to, when the asset bridges out at fewer
   * decimals than Stellar's 7. USDT0's LayerZero OFT normalises to 6 shared
   * decimals, so a 7th-decimal remainder cannot be bridged and would strand as
   * dust. Undefined means no rounding.
   */
  bridgeDecimals?: number;
  /** Short note surfaced in the deposit dialog. */
  note?: string;
}

export interface NetworkConfig {
  id: NetworkId;
  /** Human label for chrome: "Stellar Testnet". */
  label: string;
  /** Short label: "Testnet". */
  shortLabel: string;
  rpcUrl: string;
  passphrase: string;
  horizonUrl: string;
  explorerUrl: string;
  contracts: ContractSet;
  assets: AssetSet;
  /** Assets the vault may accept as margin, settlement asset first. */
  collateral: readonly CollateralAsset[];
  /**
   * Whether keepers (oracle/matcher/indexer) are expected to be running. When
   * false the UI shows a degraded-venue banner rather than presenting an empty
   * order book as if it were real market state.
   */
  keepersExpected: boolean;
}

// ─── Baked defaults ──────────────────────────────────────────────────────────
// v4, deployed 2026-09-07: kryon-protocol/infra/deploy/testnet-deployment-v4.json
//
// EVERY layer must name the same contract set: this file (browser + API), the
// keeper env (NEXT_PUBLIC_CONTRACT_*, .env.testnet), and any script. When the
// web tier briefly pointed at one set while the keepers ran another, deposits
// landed in a vault no matcher was watching, every fill failed its margin check
// and rolled back, and one settle job retried 356 times.
//
// v4 has `upgrade()` on every contract, so code changes are applied in place
// with scripts/upgrade-contracts.ts — addresses here should not need to change
// again. Verified on chain 2026-11-11: USDC (0bps) and USDT0 (500bps haircut)
// listed and active on the vault.
const TESTNET_DEFAULTS = {
  rpcUrl: "https://soroban-testnet.stellar.org",
  passphrase: "Test SDF Network ; September 2015",
  horizonUrl: "https://horizon-testnet.stellar.org",
  contracts: {
    governance: "CD5QPRFE6ND6UIJDDIR3Z2I4DNLN4TXT4CTFOIFCN7IY33YO424ZDNL5",
    oracleAdapter: "CDOAKTFECPGLX54H6ST3O3LT6476O27S67W26NYEOC7WDRY4GWCEZQZE",
    vault: "CCWDYVNAYWU3IWKC2KJJ5MFTPHUBXOZU5CKGEH5S4DAKGX3HUFHQDJGF",
    engine: "CDUGOFF3GWFXPYWYH7B3WCS6W7WQX4YTO7HF3ZVI6JBWRJWBOQJPLVSZ",
    orderGateway: "CCGDR2SWS7OMHT6T37YDWLHST5C4ZZI6K2N2WU6D47TXKCKCKLYF7SNB",
    insurance: "CDUQUDR3S7R6OIPNQ7SRHZEPTYZJPWPMXYKRMTXK3CLJYPEGWVPQXHV7",
    liquidation: "CDJ2ASKLIXRMDM3SWKTLWW7GOXJYMHGZMO5GYCGOXLA6R3FFN5MGJZ7G",
    risk: "CAR5JGY4DMZOWZYK27EBB5IWNOMIG5AD5CGYTZI2URFGB4ABUGRLC5MY",
  },
  assets: {
    nativeXlm: "CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC",
    usdc: "CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA",
    usdcIssuer: "GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5",
  },
  // Real USDT0 is a mainnet-only issuance (its issuer 404s on testnet), so
  // testnet uses the mock from scripts/deploy-testnet-usdt0.ts.
  collateral: [
    {
      code: "USDC",
      contract: "CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA",
      issuer: "GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5",
      oracleSymbol: "USDC",
      settlement: true,
    },
    {
      code: "USDT0",
      contract: "CCXWM7LWNT4VDRUJ4KZILV6KB7SXWDWDBF5TT65E5IRDEX7QZTDMNLRO",
      issuer: "GDEJSYQQOZIUKFZVS4OKWZCH7D3YCGN2NMUGBCNPVQXFX6XN4JRK32ND",
      oracleSymbol: "USDT0",
      settlement: false,
      bridgeDecimals: 6,
      note: "Margin only. PnL settles in USDC.",
    },
  ],
} as const;

// ─── Env overrides ───────────────────────────────────────────────────────────
// Read once, as literal expressions, so Next.js inlines them.

const OVERRIDES = {
  rpcUrl: process.env.NEXT_PUBLIC_STELLAR_RPC_URL,
  passphrase: process.env.NEXT_PUBLIC_STELLAR_PASSPHRASE,
  horizonUrl: process.env.NEXT_PUBLIC_STELLAR_HORIZON_URL,
  governance: process.env.NEXT_PUBLIC_CONTRACT_GOVERNANCE,
  oracleAdapter: process.env.NEXT_PUBLIC_CONTRACT_ORACLE_ADAPTER,
  vault: process.env.NEXT_PUBLIC_CONTRACT_VAULT,
  engine: process.env.NEXT_PUBLIC_CONTRACT_ENGINE,
  orderGateway: process.env.NEXT_PUBLIC_CONTRACT_ORDER_GATEWAY,
  insurance: process.env.NEXT_PUBLIC_CONTRACT_INSURANCE,
  liquidation: process.env.NEXT_PUBLIC_CONTRACT_LIQUIDATION,
  risk: process.env.NEXT_PUBLIC_CONTRACT_RISK,
  nativeXlm: process.env.NEXT_PUBLIC_ASSET_NATIVE_XLM,
  usdc: process.env.NEXT_PUBLIC_ASSET_USDC,
  usdcIssuer: process.env.NEXT_PUBLIC_USDC_ISSUER,
} as const;

// A testnet passphrase override that is actually the mainnet one would sign
// every order for the wrong chain. Refuse it.
if (OVERRIDES.passphrase && OVERRIDES.passphrase.includes("Public Global Stellar Network")) {
  throw new Error("NEXT_PUBLIC_STELLAR_PASSPHRASE is the mainnet passphrase; Kryon runs on testnet only.");
}

// USDT0 can be repointed at a re-issued mock. `_TESTNET` is the older spelling,
// still accepted so existing env files keep working.
const USDT0_OVERRIDE = {
  contract: process.env.NEXT_PUBLIC_ASSET_USDT0 || process.env.NEXT_PUBLIC_ASSET_USDT0_TESTNET,
  issuer: process.env.NEXT_PUBLIC_USDT0_ISSUER || process.env.NEXT_PUBLIC_USDT0_ISSUER_TESTNET,
} as const;

const pick = (override: string | undefined, fallback: string): string => override || fallback;

/** Resolves the collateral list, applying the USDC and USDT0 overrides. */
function buildCollateral(defaults: readonly CollateralAsset[]): readonly CollateralAsset[] {
  return defaults.map((c) => {
    if (c.settlement) {
      return {
        ...c,
        contract: pick(OVERRIDES.usdc, c.contract),
        issuer: pick(OVERRIDES.usdcIssuer, c.issuer ?? ""),
      };
    }
    if (c.code === "USDT0" && USDT0_OVERRIDE.contract) {
      return { ...c, contract: USDT0_OVERRIDE.contract, issuer: USDT0_OVERRIDE.issuer ?? c.issuer };
    }
    return c;
  });
}

function parseKeepersFlag(raw: string | undefined, fallback: boolean): boolean {
  if (raw === undefined || raw === "") return fallback;
  return raw === "true" || raw === "1";
}

function buildTestnet(): NetworkConfig {
  const d = TESTNET_DEFAULTS;
  return {
    id: "testnet",
    label: "Stellar Testnet",
    shortLabel: "Testnet",
    rpcUrl: pick(OVERRIDES.rpcUrl, d.rpcUrl),
    passphrase: pick(OVERRIDES.passphrase, d.passphrase),
    horizonUrl: pick(OVERRIDES.horizonUrl, d.horizonUrl),
    explorerUrl: "https://stellar.expert/explorer/testnet",
    contracts: {
      governance: pick(OVERRIDES.governance, d.contracts.governance),
      oracleAdapter: pick(OVERRIDES.oracleAdapter, d.contracts.oracleAdapter),
      vault: pick(OVERRIDES.vault, d.contracts.vault),
      engine: pick(OVERRIDES.engine, d.contracts.engine),
      orderGateway: pick(OVERRIDES.orderGateway, d.contracts.orderGateway),
      insurance: pick(OVERRIDES.insurance, d.contracts.insurance),
      liquidation: pick(OVERRIDES.liquidation, d.contracts.liquidation),
      risk: pick(OVERRIDES.risk, d.contracts.risk),
    },
    assets: {
      nativeXlm: pick(OVERRIDES.nativeXlm, d.assets.nativeXlm),
      usdc: pick(OVERRIDES.usdc, d.assets.usdc),
      usdcIssuer: pick(OVERRIDES.usdcIssuer, d.assets.usdcIssuer),
    },
    collateral: buildCollateral(d.collateral),
    // Set to false while the keeper fleet is down so traders see the banner
    // instead of an order book that silently never fills.
    keepersExpected: parseKeepersFlag(process.env.NEXT_PUBLIC_TESTNET_KEEPERS_LIVE, true),
  };
}

export const NETWORKS: Record<NetworkId, NetworkConfig> = {
  testnet: buildTestnet(),
};

export function getNetworkConfig(id: NetworkId): NetworkConfig {
  return NETWORKS[id];
}
