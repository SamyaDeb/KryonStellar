"""C. Trading architecture diagrams."""
from engine import Diagram, sequence


def checklist(d, x, y, items, w=360, h=50, gap=22, rx=None, rw=250, kind="box"):
    """Vertical chain of checks; items: (id, title, sub, reject or None[, kind]).\n    Each reject renders as a terminal box to the right."""
    rx = rx if rx is not None else x + w + 70
    prev = None
    for it in items:
        nid, title, sub, rej = it[:4]
        k = it[4] if len(it) > 4 else kind
        d.node(nid, x, y, w, h, title, sub, k, title_size=14, sub_size=12)
        if prev:
            d.edge(prev, nid, "", ap="b", bp="t")
        if rej:
            d.node(nid + "_r", rx, y + 6, rw, h - 12, rej, "", "terminal", title_size=12)
            d.edge(nid, nid + "_r", "", "dashed", ap="r", bp="l")
        prev = nid
        y += h + gap
    return y


def order_lifecycle():
    d = Diagram("order-lifecycle", "Order lifecycle", "From signature to fill")
    W = 240
    d.node("signed", 0, 0, W, 60, "Signed order", "SEP-53 signature")
    d.node("rej", 0, 200, W, 60, "Rejected", "4xx response", "terminal")
    d.node("rest", 380, 0, W, 60, "Resting", "in the order book")
    d.node("cancel", 380, 200, W, 60, "Cancelled", "by the owner", "terminal")
    d.node("expired", 380, 320, W, 60, "Expired", "past expiry_ts", "terminal")
    d.node("tomb", 380, 440, W, 60, "Cancelled on-chain", "cancel_order", "chain")
    d.node("match", 760, 0, W, 60, "Matched", "crossing order found")
    d.node("settle", 1140, 0, W, 60, "Settling", "settle_fill_signed")
    d.node("part", 1140, 200, W, 60, "Partially filled", "remainder rests")
    d.node("filled", 1140, 360, W, 60, "Filled", "", "terminal")
    d.edge("signed", "rest", "POST /api/orders")
    d.edge("signed", "rej", "invalid")
    d.edge("rest", "match", "crosses")
    d.edge("match", "settle", "submit")
    d.edge("settle", "part", "confirmed")
    d.edge("part", "filled", "done")
    d.edge("part", "match", "next match", ap="l", bp="b", via=[(1080, 230), (1080, 130), (880, 130)],
           label_pos=0.35)
    d.edge("settle", "rest", "failed: back to book", "dashed", ap="t", bp="t",
           via=[(1260, -60), (500, -60)])
    d.edge("rest", "cancel", "cancel")
    d.edge("rest", "expired", "", "dashed", ap=("l", 20), bp="l", via=[(350, 50), (350, 350)])
    d.legend(("box", "Live"), ("terminal", "Final"), ("chain", "On-chain"), ("solid", "Transition"),
             ("dashed", "Fallback"))
    return d


def order_validation():
    d = Diagram("order-submission-validation", "Order intake", "Checks run by POST /api/orders")
    items = [
        ("v0", "Body under 4 KB", "", "413"),
        ("v1", "Valid JSON", "", "400"),
        ("v2", "Rate limit", "30 / min per owner and IP", "429"),
        ("v3", "Valid owner address", "", "400"),
        ("v4", "Active market", "", "400"),
        ("v5", "Size and price in range", "price > 0", "400"),
        ("v6", "Nonce is u64", "", "400"),
        ("v7", "Expiry in 5 s to 7 days", "server clock", "400"),
        ("v8", "Signature verifies", "SEP-53 ed25519", "400"),
        ("v9", "Store order", "idempotent on owner:nonce", "500"),
        ("v10", "{ ok: true }", "order is resting", None, "terminal"),
    ]
    checklist(d, 0, 0, items, w=340, h=52, gap=18, rw=120)
    d.text(0, 790, "Margin is checked on-chain at settlement, not at intake.", 13, "#495057")
    d.legend(("box", "Check"), ("terminal", "Response"), ("dashed", "Rejected"))
    return d


def matching_execution():
    d = Diagram("matching-engine-execution", "Matching loop", "One matcher tick, every second")
    items = [
        ("m0", "Find markets with open orders", "", None),
        ("m1", "Load resting orders", "best price first, then oldest", None),
        ("m2", "Read oracle price", "from the indexer", "skip market"),
        ("m3", "Drop orders outside the band", "oracle +/- 10 %", None),
        ("m4", "Match by price-time priority", "maker price · no self-trades", None),
        ("m5", "Re-check both signatures", "", "cancel order"),
        ("m6", "Record the fill", "", None),
        ("m7", "Submit settlement", "wait for confirmation", "roll back fill"),
        ("m8", "Confirmed", "", None, "terminal"),
    ]
    checklist(d, 0, 0, items, w=380, h=58, gap=20, rw=180)
    d.legend(("box", "Step"), ("terminal", "Outcome"), ("dashed", "Failure path"))
    return d


def partial_fill():
    d = Diagram("partial-fill-lifecycle", "Partial fills", "One ask of 100 filled by three takers")
    d.node("ask", 0, 0, 300, 64, "Maker ask", "100 @ 0.2050")
    rows = [
        ("t1", "Taker A buys 30", "fill 30", "30 / 100"),
        ("t2", "Taker B buys 50", "fill 50", "80 / 100"),
        ("t3", "Taker C buys 40", "fill 20", "100 / 100"),
    ]
    y = 130
    d.text(0, 100, "TAKER", 12, "#495057")
    d.text(380, 100, "MATCH", 12, "#495057")
    d.text(700, 100, "FILLED ON-CHAIN", 12, "#495057")
    for nid, a, b, e in rows:
        d.node(nid, 0, y, 300, 56, a, "", "box", title_size=15)
        d.node(nid + "m", 380, y, 220, 56, b, "@ 0.2050", "box", title_size=15, sub_size=12)
        d.node(nid + "c", 700, y, 260, 56, e, "", "chain", title_size=15)
        d.edge(nid, nid + "m", "")
        d.edge(nid + "m", nid + "c", "")
        y += 96
    d.node("rest", 0, y, 300, 56, "Taker C rests 20", "", "box", title_size=15)
    d.edge("t3", "rest", "", ap="b", bp="t")
    d.text(380, y + 12, "filled + fill_size <= size, or the fill reverts", 13, "#495057")
    d.legend(("box", "Order"), ("chain", "Contract state"))
    return d


def trade_settlement():
    d = Diagram("trade-settlement", "Trade settlement", "One fill, end to end")
    parts = [("m", "Matcher", "", "box"), ("db", "PostgreSQL", "", "store"),
             ("rpc", "Soroban RPC", "", "ext"), ("gw", "Order gateway", "", "chain"),
             ("eng", "Engine + Vault", "", "chain")]
    steps = [
        ("msg", "m", "db", "1. record fill"),
        ("msg", "m", "rpc", "2. simulate"),
        ("msg", "m", "rpc", "3. submit"),
        ("msg", "rpc", "gw", "4. settle_fill_signed"),
        ("msg", "gw", "eng", "5. both sides + fees"),
        ("msg", "m", "rpc", "6. poll status", "dashed"),
        ("msg", "m", "db", "7. mark confirmed"),
        ("span", "m", "eng", "On failure the fill is removed and both orders go back to the book."),
    ]
    sequence(d, 0, 0, parts, steps, col_w=250, box_w=210)
    d.legend(("box", "Service"), ("store", "Database"), ("ext", "RPC"), ("chain", "Contract"))
    return d


def position_opening():
    d = Diagram("position-opening", "Opening a position", "How a fill becomes a position")
    d.node("s0", 0, 0, 340, 56, "Load positions", "", title_size=15)
    d.node("q1", 50, 100, 240, 80, "Opposite\nposition?", "", "decision", title_size=14)
    d.node("red", 420, 110, 300, 60, "Reduce it", "", title_size=15)
    d.node("q2", 470, 220, 200, 76, "Size left?", "", "decision", title_size=14)
    d.node("ro1", 800, 228, 220, 60, "Reduce-only: revert", "", "terminal", title_size=13)
    d.node("q3", 50, 240, 240, 80, "Reduce-only?", "", "decision", title_size=14)
    d.node("ro2", 50, 370, 240, 50, "Revert", "", "terminal", title_size=13)
    d.node("q4", 380, 360, 240, 80, "Same-side\nposition?", "", "decision", title_size=14)
    d.node("inc", 380, 490, 260, 64, "Increase", "average entry price", title_size=15, sub_size=12)
    d.node("open", 700, 380, 300, 64, "Open", "entry = fill price", title_size=15, sub_size=12)
    d.edge("s0", "q1", "")
    d.edge("q1", "red", "yes", ap="r", bp="l")
    d.edge("red", "q2", "")
    d.edge("q2", "ro1", "yes", ap="r", bp="l")
    d.edge("q2", "open", "yes", ap="b", bp="t", via=[(570, 330), (850, 330)], label_pos=0.4)
    d.edge("q1", "q3", "no", ap="b", bp="t")
    d.edge("q3", "ro2", "yes", ap="b", bp="t")
    d.edge("q3", "q4", "no", ap="r", bp="t", via=[(340, 280), (340, 335), (500, 335)], label_pos=0.15)
    d.edge("q4", "inc", "yes", ap="b", bp="t")
    d.edge("q4", "open", "no", ap="r", bp="l")
    checks = [
        ("c0", "Called by the gateway", "", None),
        ("c1", "Price inside the oracle band", "", "PriceOutsideBand"),
        ("c2", "Open interest under cap", "", "OpenInterestExceeded"),
        ("c3", "Insurance headroom", "", "InsuranceFundInsufficient"),
        ("c4", "Under 16 positions", "", "TooManyPositions"),
        ("c5", "Equity >= initial margin", "", "InsufficientCollateral"),
    ]
    d.text(1100, -26, "CHECKS ON OPEN", 12, "#495057")
    checklist(d, 1100, 0, checks, w=300, h=48, gap=16, rw=230)
    d.edge("open", "c0", "", "dashed", ap="r", bp="l", via=[(1060, 412), (1060, 24)])
    d.legend(("box", "Step"), ("decision", "Decision"), ("terminal", "Revert"))
    return d


def position_closing():
    d = Diagram("position-closing", "Reducing a position", "Shared by trades and liquidations")
    items = [
        ("r0", "Authorised caller", "gateway or liquidation", None),
        ("r1", "Size within position", "", "InvalidAmount"),
        ("r2", "Price inside the oracle band", "", "PriceOutsideBand"),
        ("r3", "Settle accrued funding", "", None),
        ("r4", "Realise PnL", "size x (exit - entry)", None),
        ("r5", "Update position and OI", "", None),
        ("r6", "Trades: equity >= initial margin", "liquidations skip this", "InsufficientCollateral"),
        ("r7", "Done", "", None, "terminal"),
    ]
    checklist(d, 0, 0, items, w=400, h=56, gap=18, rw=230)
    d.legend(("box", "Step"), ("terminal", "Result"), ("dashed", "Revert"))
    return d


def margin_calculation():
    d = Diagram("margin-calculation", "Margin calculation", "How the vault computes account health")
    d.node("bal", 0, 0, 300, 64, "Balances", "per collateral asset", "store")
    d.node("cpx", 0, 110, 300, 56, "Collateral prices", "", "chain", title_size=15)
    d.node("cv", 0, 210, 300, 64, "Collateral value", "after haircut")
    d.node("pos", 400, 0, 300, 64, "Positions", "synced from the engine", "store")
    d.node("mpx", 400, 110, 300, 56, "Oracle prices", "", "chain", title_size=15)
    d.node("n", 400, 210, 300, 64, "Notional", "size x price")
    d.node("upnl", 800, 210, 300, 64, "Unrealised PnL", "price PnL + funding")
    d.node("im", 400, 340, 300, 64, "Requirements", "IM and MM in bps of notional")
    d.node("eq", 0, 340, 300, 64, "Equity", "collateral + uPnL")
    d.node("out", 0, 470, 1100, 90, "Account health",
           "trade or withdraw only if equity >= IM      liquidatable when equity < MM", "chain",
           title_size=16, sub_size=14)
    for a, b in [("bal", "cpx"), ("cpx", "cv"), ("pos", "mpx"), ("mpx", "n"), ("n", "im"), ("cv", "eq")]:
        d.edge(a, b, "")
    d.edge("mpx", "upnl", "", ap="r", bp="t", via=[(950, 138)])
    d.edge("upnl", "eq", "", ap="b", bp="r", via=[(950, 430), (340, 430), (340, 372)])
    d.edge("eq", "out", "", ap="b", bp=("t", -400))
    d.edge("im", "out", "", ap="b", bp=("t", 0))
    d.legend(("store", "Stored"), ("chain", "Oracle / result"), ("box", "Computed"))
    return d


def liquidation_lifecycle():
    d = Diagram("liquidation-lifecycle", "Liquidation", "Keeper to contracts")
    parts = [("k", "Keeper", "", "box"), ("liq", "Liquidation", "", "chain"),
             ("eng", "Engine", "", "chain"), ("vault", "Vault", "", "chain"), ("ins", "Insurance", "", "chain")]
    steps = [
        ("self", "k", "scan accounts every 5 s\npick the largest position"),
        ("msg", "k", "liq", "1. liquidate"),
        ("msg", "liq", "vault", "2. health: must be unhealthy"),
        ("msg", "liq", "eng", "3. reduce the position"),
        ("msg", "liq", "vault", "4. health: must improve"),
        ("msg", "liq", "ins", "5. pay the liquidator"),
        ("msg", "liq", "vault", "6. seize other collateral"),
        ("msg", "liq", "vault", "7. absorb bad debt if negative", "dashed"),
        ("msg", "vault", "ins", "8. cover deficit", "dashed"),
        ("msg", "liq", "k", "receipt", "dashed"),
    ]
    sequence(d, 0, 0, parts, steps, col_w=270, box_w=220)
    d.legend(("box", "Keeper"), ("chain", "Contract"), ("solid", "Call"), ("dashed", "Conditional / return"))
    return d


def insurance_fund():
    d = Diagram("insurance-fund", "Insurance fund", "Pools and the calls that move value")
    d.node("op", 380, 180, 300, 90, "Operating pool", "pays rewards · covers deficits", "chain")
    d.node("vault", 820, 197, 240, 56, "Vault", "", "chain", title_size=15)
    d.node("bd", 1220, 180, 260, 90, "Bad debt", "recorded shortfall", "store")
    d.node("liqc", 380, 0, 300, 56, "Liquidation", "", "chain", title_size=15)
    d.node("donor", 0, 195, 200, 60, "Funder", "", "actor")
    d.node("eng", 820, 330, 240, 56, "Engine", "reads only", "chain", title_size=15, sub_size=12)
    d.node("stk", 380, 450, 300, 90, "Staked pool", "shares · 7 day unstake", "chain")
    d.node("staker", 0, 460, 200, 70, "Staker", "", "actor")
    d.node("admin", 820, 460, 240, 70, "Admin", "", "box", title_size=15)
    d.edge("donor", "op", "deposit")
    d.edge("op", "liqc", "reward")
    d.edge("op", "vault", "cover")
    d.edge("vault", "bd", "record")
    d.edge("liqc", "bd", "reduce (adl)", ap="r", bp="t", via=[(1350, 28)], label_pos=0.5)
    d.edge("staker", "stk", "stake", ap=("r", -12), bp=("l", -12))
    d.edge("stk", "staker", "unstake", ap=("l", 14), bp=("r", 14), label_dy=16)
    d.edge("stk", "op", "sweep", ap=("t", -60), bp=("b", -60))
    d.edge("admin", "stk", "sweep", "dashed")
    d.edge("eng", "op", "", "dashed", ap="l", bp=("b", 90), via=[(620, 358)])
    d.legend(("chain", "Contract / pool"), ("store", "Ledger entry"), ("solid", "Value"), ("dashed", "Authority / read"))
    return d


ALL = [order_lifecycle, order_validation, matching_execution, partial_fill, trade_settlement, position_opening,
       position_closing, margin_calculation, liquidation_lifecycle, insurance_fund]
