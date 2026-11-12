"""D. Oracle architecture diagrams."""
from engine import Diagram
from defs_trading import checklist


def oracle_ingestion():
    d = Diagram("oracle-data-ingestion", "Price ingestion", "How the oracle keeper builds each price")
    d.node("bn", 0, 0, 200, 56, "Binance", "", "ext", title_size=15)
    d.node("cb", 230, 0, 200, 56, "Coinbase", "", "ext", title_size=15)
    d.node("kr", 460, 0, 200, 56, "Kraken", "", "ext", title_size=15)
    items = [
        ("a0", "Fetch every 8 s", "", None),
        ("a1", "At least 2 sources", "", "skip"),
        ("a2", "Spread under 2 %", "", "skip"),
        ("a3", "Take the median", "confidence from the spread", None),
        ("a4", "Reflector cross-check", "within 3 %", "halt market"),
        ("a5", "Moved 0.3 % or 60 s passed", "", "wait"),
        ("a6", "write_price", "signed by the publisher", None),
    ]
    checklist(d, 130, 120, items, w=400, h=58, gap=20, rw=160)
    for s in ("bn", "cb", "kr"):
        d.edge(s, "a0", "", ap="b", bp="t")
    d.node("ora", 130, 680, 400, 56, "Oracle adapter", "", "chain", title_size=15)
    d.edge("a6", "ora", "", ap="b", bp="t")
    d.legend(("ext", "Source"), ("box", "Keeper step"), ("terminal", "No publish"), ("chain", "Contract"))
    return d


def price_validation():
    d = Diagram("oracle-price-validation", "Price validation", "Checks on every oracle write")
    d.text(0, -28, "SINGLE SOURCE  ·  write_price", 12, "#495057")
    single = [
        ("w0", "Publisher signed", "", None),
        ("w1", "Feed is active", "", "InvalidConfig"),
        ("w2", "Publisher matches feed", "", "Unauthorized"),
        ("w3", "Price > 0", "", "InvalidPrice"),
        ("w4", "Not in the future", "", "StaleOracle"),
        ("w5", "Fresher than max age", "", "StaleOracle"),
        ("w6", "Confidence within limit", "", "OracleConfidenceTooWide"),
        ("w7", "Newer than last write", "", "StaleOracle"),
        ("w8", "Store snapshot", "", None, "chain"),
    ]
    checklist(d, 0, 0, single, w=320, h=48, gap=16, rw=200)
    d.text(680, -28, "QUORUM  ·  write_quorum_price", 12, "#495057")
    quorum = [
        ("q0", "Quorum feed is active", "", "InvalidConfig"),
        ("q1", "Enough observations", "odd, at least 3", "OracleQuorumNotMet"),
        ("q2", "Each source required, once", "", "DuplicateOracleSource"),
        ("q3", "Each publisher signed", "", "Unauthorized"),
        ("q4", "Each observation valid", "same checks as left", "StaleOracle"),
        ("q5", "Take the median", "", None),
        ("q6", "All prices near median", "", "OracleDeviationTooWide"),
        ("q7", "Newer than last write", "", "StaleOracle"),
        ("q8", "Store snapshot", "", None, "chain"),
    ]
    checklist(d, 680, 0, quorum, w=320, h=48, gap=16, rx=1070, rw=200)
    d.legend(("box", "Check"), ("terminal", "Error"), ("chain", "Stored"))
    return d


def stale_price():
    d = Diagram("oracle-stale-price-handling", "Stale prices", "Every read re-checks freshness")
    d.node("gp", 0, 0, 340, 60, "get_price", "oracle adapter", "chain", title_size=15)
    items = [
        ("g1", "Feed active", "", "InvalidConfig"),
        ("g2", "Snapshot exists", "", "StaleOracle"),
        ("g3", "Age and confidence OK", "re-checked at read time", "StaleOracle"),
    ]
    checklist(d, 0, 100, items, w=340, h=56, gap=18, rw=170)
    d.edge("gp", "g1", "", ap="b", bp="t")
    cons = [
        ("c1", "Trades", "settlement reverts"),
        ("c2", "Funding", "does not accrue"),
        ("c3", "Withdrawals", "blocked"),
        ("c4", "Liquidations", "wait for a fresh price"),
    ]
    for i, (nid, t, s) in enumerate(cons):
        d.node(nid, 780, i * 86, 300, 66, t, s, "box", title_size=15, sub_size=12)
        d.edge(nid, "gp", "", "dashed", ap="l", bp=("r", -18 + i * 12), via=[(740, i * 86 + 33), (740, 12 + i * 12)])
    d.legend(("chain", "Oracle"), ("box", "Consumer"), ("terminal", "Error"), ("dashed", "Reads"))
    return d


def oracle_contract_flow():
    d = Diagram("oracle-to-contract-flow", "Where prices are used", "Consumers and the guard each applies")
    d.node("kp", 0, 160, 220, 64, "Oracle keeper", "")
    d.node("ora", 300, 150, 260, 84, "Oracle adapter", "markets and collateral", "chain")
    rows = [
        ("e1", "Engine · price band", "market guard"),
        ("e2", "Engine · funding", "index vs mark"),
        ("e3", "Engine · insurance coverage", "OI notional"),
        ("v1", "Vault · positions", "market guard"),
        ("v2", "Vault · collateral", "feed guard"),
        ("ix", "State indexer", "every 5 s"),
    ]
    for i, (nid, t, s) in enumerate(rows):
        kind = "box" if nid == "ix" else "chain"
        d.node(nid, 680, i * 76 - 40, 340, 60, t, s, kind, title_size=15, sub_size=12)
        d.edge("ora", nid, "", "solid" if kind == "chain" else "dashed", ap="r", bp="l",
               via=[(620, 192), (620, i * 76 - 10)])
    d.node("mt", 1100, 335, 240, 60, "Matcher · UI", "", "box", title_size=15)
    d.edge("ix", "mt", "", "dashed")
    d.edge("kp", "ora", "")
    d.legend(("chain", "On-chain"), ("box", "Off-chain"), ("solid", "Contract read"), ("dashed", "Simulated read"))
    return d


ALL = [oracle_ingestion, price_validation, stale_price, oracle_contract_flow]
