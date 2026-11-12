"""F. Security architecture diagrams."""
from engine import Diagram


def trust_boundaries():
    d = Diagram("trust-boundaries", "Trust boundaries", "What each zone is trusted for")
    d.frame(0, 0, 300, 400, "USER")
    d.node("wk", 20, 40, 260, 64, "Wallet key", "never leaves the wallet")
    d.node("int", 20, 140, 260, 64, "Signed order", "market · side · size · price")
    d.node("utx", 20, 240, 260, 64, "User transactions", "deposit · withdraw · cancel")
    d.frame(380, 0, 460, 400, "OPERATOR  (liveness only)")
    d.node("api", 400, 40, 200, 64, "Web / API", "")
    d.node("dbz", 400, 130, 200, 64, "Database", "", "store")
    d.node("lk", 400, 220, 200, 64, "Keepers", "")
    d.node("ad", 620, 40, 200, 64, "Admin key", "")
    d.node("mt", 620, 130, 200, 64, "Matcher", "")
    d.node("ok", 620, 220, 200, 64, "Oracle keeper", "")
    d.node("n1", 400, 310, 420, 70, "", "can delay or reorder\ncannot forge orders", "note", align="left", sub_size=14)
    d.frame(920, 0, 320, 400, "STELLAR  (enforcement)")
    d.node("gwz", 940, 40, 280, 70, "Order gateway", "signatures · nonces", "chain")
    d.node("ez", 940, 150, 280, 70, "Engine + vault", "margin · custody", "chain")
    d.node("oz", 940, 260, 280, 70, "Oracle adapter", "price guards", "chain")
    d.frame(380, 440, 860, 100, "EXTERNAL DATA")
    d.node("cx", 400, 470, 400, 50, "Exchange prices", "", "ext", title_size=15)
    d.node("rp", 820, 470, 400, 50, "RPC responses", "", "ext", title_size=15)
    d.edge("wk", "int", "")
    d.edge("int", "api", "", ap="r", bp=("l", 10), via=[(340, 172), (340, 82)])
    d.edge("mt", "gwz", "", ap="r", bp="l", via=[(870, 162), (870, 75)])
    d.edge("ok", "oz", "", ap="r", bp="l", via=[(890, 252), (890, 295)])
    d.edge("utx", "ez", "", ap="b", bp="r", via=[(150, 420), (1270, 420), (1270, 185)])
    d.legend(("box", "Component"), ("chain", "Contract"), ("ext", "Untrusted input"))
    return d


def privileged_roles():
    d = Diagram("privileged-roles", "Privileged roles", "Each role and its powers")
    roles = [
        ("Admin", "upgrades and configuration"),
        ("Guardian", "pause vault and gateway"),
        ("Governance", "timelocked admin actions"),
        ("Matcher operator", "submits settlements"),
        ("Oracle publisher", "writes prices"),
        ("Vault operator", "settles deficits"),
    ]
    for i, (t, s) in enumerate(roles):
        col, row = i % 2, i // 2
        d.node(f"r{i}", col * 460, row * 100, 430, 76, t, s, "chain" if t == "Governance" else "box",
               title_size=17, sub_size=14)
    d.legend(("box", "Key holder"), ("chain", "Contract"))
    return d


def emergency_procedures():
    d = Diagram("emergency-recovery-procedures", "Incident response", "Detect, contain, recover")
    steps = [
        ("d", "Detect", "monitor alert"),
        ("c", "Contain", "guardian pause"),
        ("x", "Diagnose", "runbook"),
        ("r", "Fix", "config or upgrade"),
        ("u", "Resume", "admin unpause"),
        ("k", "Reconcile", "jobs and fills"),
    ]
    for i, (nid, t, s) in enumerate(steps):
        d.node(nid, i * 200, 0, 170, 90, t, s, "box", title_size=17, sub_size=13)
        if i:
            d.edge(steps[i - 1][0], nid, "")
    d.node("vp", 0, 160, 370, 90, "Pause vault", "stops deposits, withdrawals,\ntrades and liquidations", "chain",
           sub_size=13)
    d.node("gp", 400, 160, 370, 90, "Pause gateway", "stops settlement only", "chain", sub_size=13)
    d.node("gv", 800, 160, 370, 90, "Pause governance", "blocks proposal execution", "chain", sub_size=13)
    d.edge("c", "vp", "", "dashed", ap="b", bp=("t", 100))
    d.edge("c", "gp", "", "dashed", ap="b", bp=("t", -60))
    d.legend(("box", "Step"), ("chain", "On-chain control"), ("dashed", "Triggers"))
    return d


def critical_paths():
    d = Diagram("critical-transaction-paths", "Value paths", "Checks on every call that moves funds")
    paths = [
        ("Deposit", "listed asset · deposit cap\ntransfer in, then credit"),
        ("Withdraw", "equity after >= initial margin\ndebit, then transfer out"),
        ("Settle a fill", "two signatures · limits · band\nmargin after each side"),
        ("Liquidate", "unhealthy before · healthier after\nreward from insurance"),
        ("Cover a deficit", "seize collateral first\nthen insurance, then bad debt"),
        ("Upgrade", "admin only\nstorage preserved"),
    ]
    for i, (t, s) in enumerate(paths):
        col, row = i % 2, i // 2
        d.node(f"k{i}", col * 480, row * 120, 450, 100, t, s, "chain" if i in (2, 3) else "box",
               align="left", title_size=17, sub_size=14)
    d.legend(("chain", "Trading path"), ("box", "Funds path"))
    return d


ALL = [trust_boundaries, privileged_roles, emergency_procedures, critical_paths]
