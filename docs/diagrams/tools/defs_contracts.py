"""B. Smart contract architecture diagrams."""
from engine import Diagram, sequence


def contract_suite():
    d = Diagram("smart-contract-architecture", "The eight contracts", "Who calls what")
    actors = [("op", 0, "Matcher"), ("lk", 300, "Liquidator"), ("pub", 600, "Oracle publisher"),
              ("tr", 900, "Trader"), ("adm", 1200, "Admin")]
    for nid, x, t in actors:
        d.node(nid, x + 20, 0, 220, 56, t, "", "actor", title_size=14)
    d.node("gw", 0, 120, 260, 80, "Order gateway", "verifies and settles fills", "chain")
    d.node("liq", 300, 120, 260, 80, "Liquidation", "liquidate · adl", "chain")
    d.node("ora", 600, 120, 260, 80, "Oracle adapter", "guarded prices", "chain")
    d.node("gov", 1200, 120, 260, 80, "Governance", "timelock · guardian", "chain")
    d.node("eng", 150, 300, 260, 80, "Engine", "positions · fees · funding", "chain")
    d.node("ins", 600, 300, 260, 80, "Insurance", "backstop · staking", "chain")
    d.node("risk", 1200, 300, 260, 80, "Risk", "read-only views", "chain")
    d.node("vault", 150, 480, 260, 80, "Vault", "custody · account health", "chain")
    d.node("tok", 150, 640, 260, 64, "Tokens", "USDC · USDT0", "ext")

    d.edge("op", "gw", "settle")
    d.edge("lk", "liq", "liquidate")
    d.edge("pub", "ora", "write_price")
    d.edge("adm", "gov", "queue · execute")
    d.edge("tr", "vault", "deposit · withdraw", ap="b", bp=("r", 20), via=[(1030, 540)], label_pos=0.3)
    d.edge("gw", "eng", "trades", ap="b", bp=("t", -60))
    d.edge("liq", "eng", "reduce", ap="b", bp=("t", 60))
    d.edge("liq", "ins", "reward", ap="b", bp="t", via=[(430, 250), (730, 250)], label_pos=0.6)
    d.edge("eng", "vault", "PnL · sync", ap="b", bp="t")
    d.edge("eng", "ins", "", ap="r", bp="l")
    d.edge("vault", "ins", "cover deficit", ap=("r", -20), bp="b", via=[(730, 500)], label_pos=0.3)
    d.edge("vault", "tok", "", ap="b", bp="t")
    d.legend(("chain", "Contract"), ("ext", "Token"), ("solid", "Call"))
    return d


def dependency_graph():
    d = Diagram("contract-dependency-graph", "Contract calls", "Every cross-contract call, by function")
    d.node("gw", 0, 0, 300, 70, "Order gateway", "", "chain")
    d.node("liq", 720, 0, 300, 70, "Liquidation", "", "chain")
    d.node("eng", 0, 300, 300, 70, "Engine", "", "chain")
    d.node("ins", 720, 300, 300, 70, "Insurance", "", "chain")
    d.node("ora", 0, 620, 300, 70, "Oracle adapter", "", "chain")
    d.node("vault", 720, 620, 300, 70, "Vault", "", "chain")
    d.node("tok", 1180, 780, 300, 60, "Tokens", "SEP-41", "ext")
    d.node("gov", 1180, 0, 300, 70, "Governance", "", "chain")
    d.node("any", 1180, 160, 300, 70, "Target contract", "action(args)", "ext")

    d.edge("gw", "eng", "positions\nopen_position\nincrease_position\nreduce_position\ncharge_trade_fee")
    d.edge("liq", "eng", "liquidate_reduce · positions", ap=("l", 10), bp=("t", 80),
           via=[(380, 45), (380, 230), (230, 230)], label_pos=0.15)
    d.edge("liq", "ins", "pay_liquidator\nbad_debt_of\nreduce_bad_debt")
    d.edge("liq", "vault", "account_health\nseize_for_deficit\nabsorb_bad_debt", ap="r", bp="r",
           via=[(1080, 35), (1080, 655)], label_pos=0.27)
    d.edge("eng", "ora", "get_price")
    d.edge("eng", "ins", "balance_of · bad_debt_of")
    d.edge("eng", "vault", "set_market_config · sync_positions\napply_pnl · account_health\nset_funding_indexes",
           ap=("b", 80), bp=("t", -60), via=[(230, 520), (810, 520)], label_pos=0.5)
    d.edge("vault", "ora", "get_price", ap="l", bp="r")
    d.edge("vault", "ins", "cover_deficit\nrecord_bad_debt", ap=("t", 60), bp=("b", 60), label_pos=0.45)
    d.edge("vault", "tok", "transfer", ap="b", bp="l", via=[(870, 810)], label_pos=0.6)
    d.edge("ins", "tok", "transfer", ap="r", bp="t", via=[(1330, 335)], label_pos=0.8)
    d.edge("gov", "any", "execute", "dashed")
    d.legend(("chain", "Contract"), ("ext", "External"), ("solid", "Call"), ("dashed", "Via proposal"))
    return d


def invocation_flow():
    d = Diagram("cross-contract-invocation-flow", "Settling one fill", "settle_fill_signed, call by call")
    parts = [("op", "Matcher", "operator", "actor"), ("gw", "Order gateway", "", "chain"),
             ("eng", "Engine", "", "chain"), ("ora", "Oracle", "", "chain"),
             ("vault", "Vault", "", "chain"), ("ins", "Insurance", "", "chain")]
    steps = [
        ("msg", "op", "gw", "1. settle_fill_signed"),
        ("self", "gw", "2. verify both signatures\nvalidate the fill"),
        ("msg", "gw", "eng", "3. positions(maker)"),
        ("msg", "gw", "eng", "4. open / increase / reduce"),
        ("msg", "eng", "ora", "5. get_price"),
        ("self", "eng", "6. price band · mark\nOI caps"),
        ("msg", "eng", "ins", "7. balance_of (OI policy)", "dashed"),
        ("msg", "eng", "vault", "8. apply_pnl"),
        ("msg", "eng", "vault", "9. sync_positions"),
        ("msg", "eng", "vault", "10. account_health"),
        ("msg", "vault", "ora", "11. get_price", "dashed"),
        ("self", "eng", "12. equity >= initial margin"),
        ("msg", "gw", "eng", "13. charge_trade_fee"),
        ("msg", "eng", "vault", "14. debit fee · credit recipient"),
        ("span", "gw", "vault", "15. repeat 3 to 14 for the taker"),
        ("self", "gw", "16. record both fills"),
        ("msg", "gw", "op", "17. FillReceipt", "dashed"),
    ]
    sequence(d, 0, 0, parts, steps, col_w=250, box_w=210)
    d.legend(("chain", "Contract"), ("solid", "Call"), ("dashed", "Conditional / return"))
    return d


def authorization():
    d = Diagram("contract-authorization", "Who can call what", "require_auth on every entry point")
    cells = [
        ("Admin", "upgrade · nominate_admin\nmarkets · fees · funding · OI policy\ncollateral · caps · oracle feeds\n"
         "reward rate · insurance sweep\nmigration import · unpause"),
        ("Contracts", "gateway -> engine trades\nengine -> vault PnL and sync\nliquidation -> engine, vault, insurance\n"
         "vault -> insurance deficit cover"),
        ("Guardian", "pause vault · pause gateway\nveto governance execute"),
        ("Matcher operator", "settle_fill_signed\nsettle_fill"),
        ("Oracle publisher", "write_price"),
        ("Vault operator", "settle_deficit"),
        ("Account owner", "deposit · withdraw · cancel_order\nsigned orders · insurance staking"),
        ("Anyone", "liquidate · adl · update_funding\nreclaim_order_state · reads"),
    ]
    for i, (t, s) in enumerate(cells):
        col, row = i % 2, i // 2
        h = 130 if row == 0 else 86
        y = [0, 150, 256, 362][row]
        d.node(f"c{i}", col * 480, y, 450, h, t, s, "chain" if i == 1 else "box", align="left",
               title_size=16, sub_size=13)
    d.legend(("box", "Key holder"), ("chain", "Contract"))
    return d


def storage():
    d = Diagram("contract-storage", "Contract storage", "[I] instance  ·  [P] persistent")
    boxes = [
        ("Engine", "[I] admin · peers · fee recipient\n[I] next position id\n[P] Market · FeeConfig · FundingConfig\n"
         "[P] FundingState · MarkState\n[P] Positions(user)\n[P] open interest · OI policy"),
        ("Vault", "[I] admin · guardian · operator · peers\n[I] paused · deposit caps\n[P] Collateral(asset)\n"
         "[P] Balance(user, asset)\n[P] Positions(user) synced copy\n[P] market config · funding indexes"),
        ("Order gateway", "[I] admin · guardian · operator\n[I] engine · domain · paused\n[P] Filled(owner, nonce)\n"
         "[P] Cancelled(owner, nonce)"),
        ("Oracle adapter", "[I] admin\n[P] Config(asset)\n[P] Price(asset)\n[P] SourcePublisher(asset, source)"),
        ("Insurance", "[I] admin · liquidation · vault\n[P] Balance · BadDebt\n[P] StakedBalance · TotalShares\n"
         "[P] Shares · Epoch · PendingUnstake"),
        ("Liquidation", "[I] admin · engine · vault\n[I] insurance · settlement asset\n[I] reward bps"),
        ("Governance", "[I] admin · guardian\n[I] min delay · paused\n[P] Proposal(id)"),
        ("Risk", "[I] admin\n[P] Market(id)"),
    ]
    y = 0
    for i, (t, s) in enumerate(boxes):
        if i % 2 == 0:
            rows = max(len(boxes[i][1].split("\n")), len(boxes[i + 1][1].split("\n")))
            h = rows * 17 + 56
        d.node(f"s{i}", (i % 2) * 480, y, 450, h, t, s, "chain", align="left", title_size=16, sub_size=13)
        if i % 2 == 1:
            y += h + 20
    return d


ALL = [contract_suite, dependency_graph, invocation_flow, authorization, storage]
