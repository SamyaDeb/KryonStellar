"use client";

import { useNetwork } from "@/features/network/NetworkContext";

/**
 * Warns when the venue has no keepers behind it.
 *
 * Without this, a venue with no running oracle/matcher/indexer renders as a
 * perfectly normal one that simply has no orders — indistinguishable from a
 * quiet market. A trader could place an order and wait indefinitely for a match
 * that nothing is running to produce. Say so explicitly instead.
 *
 * Driven by `NEXT_PUBLIC_TESTNET_KEEPERS_LIVE`; see config/networks.ts.
 */
export function NetworkBanner() {
  // From context (server-seeded), never the module-scope `KEEPERS_EXPECTED`,
  // so server and client render the same markup.
  const { config } = useNetwork();
  if (config.keepersExpected) return null;

  return (
    <div
      role="status"
      className="flex shrink-0 items-center justify-center gap-2 border-b border-[#48331c] bg-[#2a1f11] px-3 py-[6px] text-center text-[12px] text-[#ff9440]"
    >
      <span aria-hidden="true" className="h-[6px] w-[6px] shrink-0 rounded-full bg-[#ff9440]" />
      <span>
        <strong className="font-semibold">Trading is paused.</strong>{" "}
        Kryon&apos;s price, matching and indexing services aren&apos;t running right now, so the
        order book will be empty and orders won&apos;t fill.
      </span>
    </div>
  );
}
