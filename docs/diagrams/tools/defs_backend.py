"""E. Backend architecture diagrams."""
from engine import Diagram


def backend_services():
    d = Diagram("backend-service-architecture", "Services", "Long-running processes and what each one does")
    svc = [
        ("Matcher", "every 1 s", "matches orders\nsettles fills on-chain"),
        ("Oracle keeper", "every 8 s", "publishes prices"),
        ("State indexer", "every 5 s", "mirrors chain state\ninto the database"),
        ("Reconciler", "every 15 s", "recovers settlement jobs"),
        ("Liquidation keeper", "every 5 s", "liquidates unhealthy\naccounts"),
        ("Funding keeper", "every 15 min", "advances funding"),
        ("WebSocket server", "every 1 s", "streams book and trades"),
        ("TTL keeper", "daily", "keeps contracts live"),
        ("Monitor", "every 30 s", "health checks and alerts"),
    ]
    for i, (t, c, s) in enumerate(svc):
        col, row = i % 3, i // 3
        d.node(f"s{i}", col * 360, row * 140, 330, 116, t, f"{c}\n{s}", "box", align="left",
               title_size=17, sub_size=14)
    d.node("db", 0, 440, 1050, 56, "PostgreSQL", "", "store", title_size=16)
    d.node("rpc", 0, 520, 1050, 56, "Soroban RPC", "", "ext", title_size=16)
    d.legend(("box", "Service"), ("store", "Database"), ("ext", "Network"))
    return d


def matching_architecture():
    d = Diagram("matching-engine-architecture", "Matcher internals", "One process, one tick at a time")
    d.frame(0, 0, 820, 420, "MATCHER")
    d.node("loop", 20, 40, 240, 60, "Poll loop", "1 s", sub_size=13)
    d.node("probe", 290, 40, 240, 60, "Market probe", "", sub_size=13)
    d.node("load", 560, 40, 240, 60, "Order loader", "", sub_size=13)
    d.node("band", 560, 150, 240, 60, "Band filter", "oracle +/- 10 %", sub_size=13)
    d.node("core", 290, 150, 240, 60, "Match", "price-time priority", sub_size=13)
    d.node("q", 20, 150, 240, 60, "Signature check", "", sub_size=13)
    d.node("pf", 20, 280, 240, 60, "Record fill", "", sub_size=13)
    d.node("ex", 290, 280, 240, 60, "Settle", "submit and confirm", sub_size=13)
    d.node("rb", 560, 280, 240, 60, "Roll back", "on failure", sub_size=13)
    for a, b in [("loop", "probe"), ("probe", "load"), ("load", "band"), ("band", "core"), ("core", "q"), ("q", "pf"),
                 ("pf", "ex")]:
        d.edge(a, b, "")
    d.edge("ex", "rb", "", "dashed")
    d.node("db", 900, 120, 240, 70, "PostgreSQL", "orders · fills · jobs", "store")
    d.node("rpc", 900, 290, 240, 60, "Soroban RPC", "", "ext")
    d.node("gw", 900, 410, 240, 60, "Order gateway", "", "chain")
    d.node("p_db", 819.5, 155, 1, 1, "", kind="anchor")
    d.edge("p_db", "db", "", both=True)
    d.edge("ex", "rpc", "", ap="b", bp="l", via=[(410, 385), (860, 385), (860, 320)])
    d.edge("rpc", "gw", "")
    d.legend(("box", "Component"), ("store", "Database"), ("ext", "RPC"), ("chain", "Contract"))
    return d


def indexer_architecture():
    d = Diagram("indexer-architecture", "Indexing", "Chain state to the database")
    d.node("rpc", 0, 0, 280, 64, "Soroban RPC", "simulated reads", "ext")
    d.node("ix", 380, 0, 320, 64, "State indexer", "every 5 s")
    d.node("r", 380, 110, 320, 84, "Reads per market", "funding · open interest\noracle price",
           "box", title_size=15, sub_size=13)
    d.node("mk", 800, 120, 280, 64, "Market rows", "", "store")
    d.node("agg", 380, 250, 320, 64, "Stats aggregation", "every 30 s")
    d.node("src", 0, 250, 280, 64, "Fills", "", "store")
    d.node("out", 800, 250, 280, 64, "Trader stats", "", "store")
    d.edge("ix", "r", "")
    d.edge("r", "rpc", "", "dashed", ap="l", bp="b", via=[(140, 152)])
    d.edge("r", "mk", "")
    d.edge("ix", "agg", "", ap=("l", 10), bp="l", via=[(350, 42), (350, 282)])
    d.edge("src", "agg", "", "dashed")
    d.edge("agg", "out", "")
    d.legend(("box", "Step"), ("store", "Table"), ("ext", "RPC"), ("dashed", "Read"))
    return d


def database_architecture():
    d = Diagram("database-architecture", "Database", "Core tables and their relations")
    d.node("mkt", 0, 0, 220, 76, "Market", "chain summary", "store")
    d.node("ord", 300, 0, 220, 76, "Order", "owner:nonce", "store")
    d.node("acc", 600, 0, 220, 76, "Account", "trader address", "store")
    d.node("tx", 0, 160, 220, 76, "TxJob", "settlement jobs", "store")
    d.node("fill", 300, 160, 220, 76, "Fill", "maker · taker", "store")
    d.node("stat", 600, 160, 220, 76, "TraderStat", "volume by period", "store")
    d.edge("ord", "mkt", "market")
    d.edge("ord", "acc", "owner")
    d.edge("fill", "acc", "", ap=("t", 60), bp="b", via=[(470, 130), (710, 130)])
    d.edge("fill", "mkt", "", ap="l", bp="b", via=[(260, 198), (260, 120), (110, 120)])
    d.legend(("store", "Table"), ("solid", "Foreign key"))
    return d


def websocket_distribution():
    d = Diagram("websocket-event-distribution", "Real-time stream", "WebSocket server")
    d.node("cl", 0, 100, 240, 76, "Browser", "", "box")
    d.node("ws", 440, 0, 360, 280, "WebSocket server", "subscribe to channels\n  orderbook:<id>\n  trades:<id>\n\n"
           "broadcast every second\nping every 25 s", "box", align="left", sub_size=14)
    d.node("db", 960, 102, 240, 76, "PostgreSQL", "", "store")
    d.edge("cl", "ws", "subscribe", ap=("r", -14), bp=("l", -14))
    d.edge("ws", "cl", "book · trades", ap=("l", 22), bp=("r", 22), label_dy=20)
    d.edge("ws", "db", "poll", "dashed", ap="r", bp="l")
    d.node("fb", 0, 250, 240, 64, "REST fallback", "", "box")
    d.edge("cl", "fb", "no WS", "dashed", ap="b", bp="t")
    d.legend(("box", "Process"), ("store", "Database"), ("dashed", "Poll / fallback"))
    return d


def frontend_backend():
    d = Diagram("frontend-backend-communication", "Frontend", "What the trading terminal talks to")
    d.node("ui", 380, 200, 300, 90, "Trading terminal", "Next.js · React")
    d.node("api", 0, 0, 300, 70, "REST API", "orders · market data", "box", sub_size=13)
    d.node("rpc", 760, 0, 300, 70, "Soroban RPC", "positions · health", "ext", sub_size=13)
    d.node("fr", 760, 210, 300, 70, "Freighter", "signs orders and txs", "ext", sub_size=13)
    d.node("ws", 0, 210, 300, 70, "WebSocket", "live book", "box", sub_size=13)
    d.node("bn", 0, 400, 300, 64, "Binance", "24 h change", "ext", sub_size=13)
    d.node("tv", 380, 400, 300, 64, "TradingView", "chart", "ext", sub_size=13)
    d.node("ch", 760, 400, 300, 64, "Contracts", "", "chain")
    d.edge("ui", "api", "", ap=("t", -80), bp="b", via=[(450, 140), (150, 140)])
    d.edge("ui", "rpc", "", ap=("t", 80), bp="b", via=[(610, 140), (910, 140)])
    d.edge("ui", "fr", "", ap="r", bp="l")
    d.edge("ui", "ws", "", "dashed", ap="l", bp="r")
    d.edge("ui", "bn", "", "dashed", ap=("b", -80), bp="t", via=[(450, 340), (150, 340)])
    d.edge("ui", "tv", "", "dashed", ap="b", bp="t")
    d.edge("fr", "ch", "", ap="b", bp="t")
    d.legend(("box", "Kryon"), ("ext", "External"), ("chain", "Contract"), ("solid", "Request"),
             ("dashed", "Market data"))
    return d


ALL = [backend_services, matching_architecture, indexer_architecture, database_architecture, websocket_distribution,
       frontend_backend]
