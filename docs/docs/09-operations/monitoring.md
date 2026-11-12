---
title: Monitoring
sidebar_position: 3
---

# Monitoring

`monitor.ts` runs every 30 seconds and posts alerts to `ALERT_WEBHOOK_URL`. It alerts once, reminds hourly, and posts when things recover.

| Check | Alerts when |
| --- | --- |
| Oracle freshness | newest price older than 110 s |
| Matcher lag | oldest pending order older than 60 s |
| Indexer lag | market data older than 60 s |
| Database | round trip over 2 s |
| App and WebSocket | unreachable |
| Operator balances | under 25 XLM |
| Funding | not updated for an hour |
| Insurance coverage | under 2,000 bps of open interest |
