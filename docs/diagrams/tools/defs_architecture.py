"""A. Protocol architecture diagrams."""
from engine import Diagram


def system_architecture():
    d = Diagram("system-architecture", "System architecture", "Components and the paths between them")
    d.node("trader", 0, 150, 180, 64, "Trader / bot", "", "actor")
    d.node("wallet", 0, 300, 180, 64, "Stellar wallet", "Freighter or keypair", "ext")
    d.node("web", 230, 150, 240, 64, "Web app", "Next.js")
    d.node("api", 230, 290, 240, 64, "REST API", "Next.js route handlers")
    d.node("db", 230, 520, 240, 70, "PostgreSQL", "order book · fills · jobs", "store")

    d.frame(540, 0, 710, 92, "PRICE SOURCES")
    d.node("cex", 560, 30, 260, 48, "Binance · Coinbase · Kraken", "", "ext", title_size=14)
    d.node("refl", 980, 30, 250, 48, "Reflector", "", "ext", title_size=14)

    d.frame(540, 110, 300, 690, "SERVICES")
    svc = [
        ("oracle_k", "Oracle keeper", "3-source median"),
        ("matcher", "Matcher", "price-time CLOB"),
        ("fund_k", "Funding keeper", "every 15 min"),
        ("liq_k", "Liquidation keeper", "every 5 s"),
        ("indexer", "State indexer", "chain -> Market rows"),
        ("recon", "Reconciler", "settlement recovery"),
        ("ws", "WebSocket server", "book and trades"),
        ("ttl_k", "TTL keeper", "daily"),
        ("monitor", "Monitor", "alerts"),
    ]
    for i, (nid, t, sub) in enumerate(svc):
        d.node(nid, 560, 150 + 70 * i, 260, 56, t, sub, title_size=15, sub_size=12)

    d.frame(960, 110, 290, 690, "SOROBAN CONTRACTS")
    chain = ["Oracle adapter", "Order gateway", "Engine", "Liquidation", "Vault", "Insurance", "Risk", "Governance"]
    ids = ["oracle", "gw", "engine", "liq", "vault", "ins", "risk", "gov"]
    for i, (nid, t) in enumerate(zip(ids, chain)):
        d.node(nid, 980, 154 + 70 * i, 250, 48, t, "", "chain", title_size=15)

    d.node("db_port", 539.5, 555, 1, 1, "", kind="anchor")
    d.node("chain_port", 959.5, 667.5, 1, 1, "", kind="anchor")

    d.edge("trader", "web", "", ap="r", bp="l")
    d.edge("web", "wallet", "sign", label_pos=0.5)
    d.edge("web", "api", "REST", ap="b", bp="t")
    d.edge("api", "db", "orders", ap="b", bp="t")
    d.edge("db", "db_port", "", ap="r", both=True)
    d.edge("cex", "oracle_k", "", ap="b", bp="t")
    d.edge("refl", "oracle_k", "cross-check", "dashed", ap="l", bp=("r", -14), via=[(900, 54), (900, 164)],
           label_pos=0.18)
    d.edge("oracle_k", "oracle", "write_price", ap=("r", 8), bp=("l", 8))
    d.edge("matcher", "gw", "settle", ap="r", bp="l")
    d.edge("fund_k", "engine", "funding", ap="r", bp="l")
    d.edge("liq_k", "liq", "liquidate", ap="r", bp="l")
    d.edge("ttl_k", "chain_port", "extend TTL", ap="r")
    d.edge("wallet", "vault", "deposit · withdraw · cancel", ap="b", bp="r",
           via=[(90, 840), (1290, 840), (1290, 458)], label_pos=0.3)
    d.legend(("box", "Service"), ("chain", "Contract"), ("store", "Database"), ("ext", "External"),
             ("solid", "Write"), ("dashed", "Read"))
    return d


def onchain_offchain():
    d = Diagram("onchain-offchain-boundary", "Trust boundary", "What runs off-chain and what the chain enforces")
    rows = [
        ("Matching", "settle_fill_signed", "operator", "signatures · nonces · limits · margin"),
        ("Price aggregation", "write_price", "publisher", "publisher · age · confidence"),
        ("Funding schedule", "update_funding", "anyone", "premium · 1 h accrual cap"),
        ("Liquidation scan", "liquidate", "anyone", "unhealthy before · healthier after"),
        ("Wallet", "deposit / withdraw", "owner", "custody · equity >= initial margin"),
        ("Wallet", "cancel_order", "owner", "tombstone blocks settlement"),
    ]
    d.frame(0, 0, 300, 470, "OFF-CHAIN")
    d.frame(380, 0, 300, 470, "INTERFACE")
    d.frame(760, 0, 360, 470, "ON-CHAIN")
    for i, (a, f, who, chk) in enumerate(rows):
        y = 44 + i * 70
        d.node(f"o{i}", 20, y, 260, 52, a, "", "box", title_size=15)
        d.node(f"i{i}", 400, y, 260, 52, f, who, "box", title_size=14, sub_size=12)
        d.node(f"c{i}", 780, y, 320, 52, chk, "", "chain", title_size=14)
        d.edge(f"o{i}", f"i{i}", "")
        d.edge(f"i{i}", f"c{i}", "")
    d.legend(("box", "Off-chain / call"), ("chain", "Enforced by contracts"))
    return d


def component_dependencies():
    d = Diagram("component-dependencies", "Repository structure", "How the modules depend on each other")
    d.frame(0, 0, 1180, 130, "APPLICATIONS")
    d.node("ui", 20, 40, 260, 70, "Trading UI", "client/app")
    d.node("api", 310, 40, 260, 70, "API routes", "client/app/api")
    d.node("svc", 600, 40, 260, 70, "Services", "client/scripts")
    d.node("docs", 890, 40, 270, 70, "Docs site", "docs/", "ext")

    d.frame(0, 170, 1180, 210, "SHARED TYPESCRIPT")
    libs = [
        ("cfg", "config", "markets · networks"),
        ("mkt", "lib/market", "signing · intents"),
        ("val", "lib/validation", "order intake"),
        ("rl", "lib/rate-limit", "Upstash"),
        ("stl", "lib/stellar", "contracts · settlement"),
        ("sec", "lib/secrets-check", "key guards"),
        ("dbl", "lib/sql · lib/db", "PostgreSQL client"),
    ]
    for i, (nid, t, s) in enumerate(libs):
        d.node(nid, 20 + (i % 4) * 290, 206 + (i // 4) * 86, 260, 64, t, s, "box", title_size=15, sub_size=12)
    for nid, x in (("ui", 150), ("api", 440), ("svc", 730)):
        d.node(nid + "_p", x - 0.5, 169.5, 1, 1, "", kind="anchor")
        d.edge(nid, nid + "_p", "", ap="b")

    d.frame(0, 420, 760, 160, "RUST WORKSPACE")
    d.node("contracts", 20, 460, 230, 80, "contracts", "8 Soroban contracts", "chain")
    d.node("re", 270, 460, 220, 80, "risk-engine", "margin · funding", "chain")
    d.node("pc", 510, 460, 230, 80, "protocol-core", "math · types", "chain")
    d.node("prisma", 870, 460, 290, 80, "Prisma schema", "kryon-protocol/prisma", "store")

    d.edge("val", "mkt", "")
    d.edge("contracts", "re", "")
    d.edge("re", "pc", "")
    d.edge("contracts", "pc", "", ap="b", bp="b", via=[(135, 565), (625, 565)])
    d.edge("dbl", "prisma", "", "dashed", ap="b", bp=("t", 15))
    d.legend(("box", "Module"), ("chain", "Rust crate"), ("store", "Schema"), ("solid", "Imports"))
    return d


def external_integrations():
    d = Diagram("external-integrations", "External integrations", "Third-party systems Kryon relies on")
    d.node("core", 400, 80, 260, 100, "Kryon", "app · API · services")
    d.frame(0, 0, 320, 250, "USER")
    d.node("fr", 20, 40, 280, 80, "Freighter", "signs orders and txs", "ext", sub_size=12)
    d.node("tv", 20, 145, 280, 80, "TradingView", "price chart", "ext", sub_size=12)
    d.frame(740, 0, 340, 470, "STELLAR")
    st = [("rpc", "Soroban RPC", "simulate · submit"),
          ("hz", "Horizon", "accounts · trustlines"),
          ("usdc", "USDC", "settlement asset"),
          ("usdt", "USDT0", "margin collateral"),
          ("refl", "Reflector", "price cross-check")]
    for i, (nid, t, s) in enumerate(st):
        d.node(nid, 760, 40 + i * 84, 300, 66, t, s, "ext", title_size=15, sub_size=12)
    d.frame(0, 300, 660, 220, "DATA AND INFRASTRUCTURE")
    oth = [("cex", "Binance · Coinbase · Kraken", "price feeds"),
           ("up", "Upstash Redis", "rate limiting"),
           ("cf", "Cloudflare Tunnel", "public edge"),
           ("hook", "Alert webhook", "monitoring")]
    for i, (nid, t, s) in enumerate(oth):
        d.node(nid, 20 + (i % 2) * 320, 340 + (i // 2) * 88, 300, 66, t, s, "ext", title_size=15, sub_size=12)
    d.node("pl", 319.5, 130, 1, 1, "", kind="anchor")
    d.node("pr", 739.5, 130, 1, 1, "", kind="anchor")
    d.node("pb", 529.5, 299.5, 1, 1, "", kind="anchor")
    d.edge("core", "pl", "", ap="l")
    d.edge("core", "pr", "", ap="r")
    d.edge("core", "pb", "", "dashed", ap="b")
    d.legend(("ext", "External system"), ("solid", "Trading path"), ("dashed", "Data and operations"))
    return d


ALL = [system_architecture, onchain_offchain, component_dependencies, external_integrations]
