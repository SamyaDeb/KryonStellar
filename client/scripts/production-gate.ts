#!/usr/bin/env tsx
import { StrKey } from "@stellar/stellar-sdk";
import { ACTIVE_MARKET_SYMBOLS, ACTIVE_MARKETS, ASSETS, CONTRACTS, DEFAULT_MARKET_SYMBOL, NETWORK, WS_URL } from "../config";

/** `--runtime`: also check the web tier's live env (URLs, DB, settlement key, Redis). */
const RUNTIME = process.argv.includes("--runtime");
/** `--keepers`: also check the keeper fleet's env. */
const KEEPERS = process.argv.includes("--keepers");

function fail(message: string): never {
  throw new Error(`production gate failed: ${message}`);
}

function assertContractId(label: string, value: string) {
  if (!StrKey.isValidContract(value)) fail(`${label} is not a valid Stellar contract id`);
}

function assertPublicKey(label: string, value: string) {
  if (!StrKey.isValidEd25519PublicKey(value)) fail(`${label} is not a valid Stellar public key`);
}

function assertHttpsUrl(label: string, value: string) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") fail(`${label} must use HTTPS`);
  } catch {
    fail(`${label} must be a valid HTTPS URL`);
  }
}

function assertWssUrl(label: string, value: string) {
  try {
    const url = new URL(value);
    if (url.protocol !== "wss:") fail(`${label} must use WSS`);
  } catch {
    fail(`${label} must be a valid WSS URL`);
  }
}

function main() {
  if (!ACTIVE_MARKET_SYMBOLS.length) fail("no active markets configured");
  if (!DEFAULT_MARKET_SYMBOL || !(DEFAULT_MARKET_SYMBOL in ACTIVE_MARKETS)) {
    fail("default market is not active");
  }

  const markets = Object.values(ACTIVE_MARKETS);
  const ids = new Set<number>();
  for (const market of markets) {
    if (ids.has(market.marketId)) fail(`duplicate marketId ${market.marketId}`);
    ids.add(market.marketId);
    if (market.marketId <= 0) fail(`${market.symbol} has invalid marketId`);
    if (!market.symbol.endsWith("-PERP")) fail(`${market.symbol} must use -PERP naming`);
    if (!market.oracleSymbol) fail(`${market.symbol} missing oracleSymbol`);
    if (!market.priceSourceSymbol) fail(`${market.symbol} missing priceSourceSymbol`);
    if (market.quoteAsset !== "USDC") fail(`${market.symbol} must be USDC settled for v1`);
    if (market.maxLeverageBps <= 0 || market.maxLeverageBps > 2_000_000) {
      fail(`${market.symbol} maxLeverageBps outside allowed range`);
    }
    if (market.initialMarginBps <= 0 || market.maintenanceMarginBps <= 0) {
      fail(`${market.symbol} margin bps must be positive`);
    }
    if (market.maintenanceMarginBps >= market.initialMarginBps) {
      fail(`${market.symbol} maintenance margin must be lower than initial margin`);
    }
  }

  assertContractId("CONTRACTS.governance", CONTRACTS.governance);
  assertContractId("CONTRACTS.oracleAdapter", CONTRACTS.oracleAdapter);
  assertContractId("CONTRACTS.vault", CONTRACTS.vault);
  assertContractId("CONTRACTS.engine", CONTRACTS.engine);
  assertContractId("CONTRACTS.orderGateway", CONTRACTS.orderGateway);
  assertContractId("CONTRACTS.insurance", CONTRACTS.insurance);
  assertContractId("CONTRACTS.liquidation", CONTRACTS.liquidation);
  assertContractId("CONTRACTS.risk", CONTRACTS.risk);
  assertContractId("ASSETS.nativeXlm", ASSETS.nativeXlm);
  assertContractId("ASSETS.usdc", ASSETS.usdc);
  assertPublicKey("ASSETS.usdcIssuer", ASSETS.usdcIssuer);

  if (!NETWORK.rpcUrl.startsWith("https://")) fail("NETWORK.rpcUrl must be HTTPS");
  if (NETWORK.passphrase !== "Test SDF Network ; September 2015") {
    fail("passphrase is not the Stellar testnet passphrase");
  }

  // Runtime checks need the deployment's real env (URLs and secrets), which CI
  // does not have. These used to run only when the network was mainnet, so
  // once testnet became the live venue they silently stopped running at all.
  // Now they are opt-in by flag and run on the box that serves traffic
  // (kryon-protocol/infra/a1flex/setup-web-tier.sh).
  if (RUNTIME) {
    assertHttpsUrl("NEXT_PUBLIC_APP_URL", process.env.NEXT_PUBLIC_APP_URL ?? "");
    assertWssUrl("NEXT_PUBLIC_WS_URL", WS_URL);

    if (!process.env.DATABASE_URL && !process.env.DATABASE_URL_TESTNET) {
      fail("DATABASE_URL is required for API routes");
    }
    if (!process.env.MATCHER_OPERATOR_SECRET && !process.env.MATCHER_OPERATOR_SECRET_TESTNET) {
      fail("MATCHER_OPERATOR_SECRET is required for settlement signing");
    }
    if (!process.env.UPSTASH_REDIS_REST_URL || !process.env.UPSTASH_REDIS_REST_TOKEN) {
      fail("distributed rate limit Redis is required");
    }
  }

  // A perpetual has no expiry, so funding is the only mechanism tethering the
  // mark to the index. Without this keeper the rate never accrues and the
  // market silently stops being a perp. Checked where the keepers run.
  if (KEEPERS && !process.env.FUNDING_KEEPER_SECRET) {
    fail("FUNDING_KEEPER_SECRET is required — funding does not accrue without the keeper");
  }

  console.log(`production gate passed: ${ACTIVE_MARKET_SYMBOLS.join(", ")} on ${NETWORK.name}`);
}

main();
