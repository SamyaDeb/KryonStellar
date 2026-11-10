import { neon, type SqlClient } from "@/lib/sql";
import { PRIMARY_NETWORK, type NetworkId } from "@/config/networks";

// Server-side only — never import this in client components.
// The DATABASE_URL_* vars are private (no NEXT_PUBLIC_ prefix).

/**
 * The testnet database (`kryon_testnet`).
 *
 * `DATABASE_URL_TESTNET` wins when set; `DATABASE_URL` is the plain spelling.
 * The suffixed name is left over from when the app also served mainnet and is
 * still honoured so existing env files keep working.
 */
function urlForNetwork(network: NetworkId): string {
  const url = process.env.DATABASE_URL_TESTNET || process.env.DATABASE_URL;
  if (url) return url;
  throw new Error(
    `No database configured for network "${network}". Set DATABASE_URL (or DATABASE_URL_TESTNET).`
  );
}

// Created lazily so a build or script that never touches the database does not
// need a connection string.
const clients = new Map<NetworkId, SqlClient>();

/** Get the SQL client for a network (always testnet today). */
function getDb(network: NetworkId = PRIMARY_NETWORK): SqlClient {
  const cached = clients.get(network);
  if (cached) return cached;
  const client = neon(urlForNetwork(network));
  clients.set(network, client);
  return client;
}

export const db = getDb;

/**
 * Retry a DB operation on transient Neon errors ("fetch failed",
 * connection resets) which occur sporadically under burst on the serverless
 * driver. Deterministic errors (constraint violations, bad SQL) are NOT
 * retried — they surface immediately.
 */
export async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      const msg = e instanceof Error ? e.message : String(e);
      const transient = /fetch failed|ECONNRESET|ETIMEDOUT|connect|terminat|timeout/i.test(msg);
      if (!transient || i === attempts - 1) throw e;
      await new Promise((r) => setTimeout(r, 100 * (i + 1)));
    }
  }
  throw lastErr;
}
