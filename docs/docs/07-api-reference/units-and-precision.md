---
title: Units
sidebar_position: 3
---

# Units

| Quantity | Scale |
| --- | --- |
| Price | 10^18 |
| Size, token amounts | 10^7 |
| Margin and fees | bps |

A raw price is too large for a JavaScript number. Use `BigInt`:

```js
BigInt("77334100000000000000000")   // exact
Number("77334100000000000000000")   // loses precision
```

| Route | Format |
| --- | --- |
| Order submission, order list, markets | raw integers |
| Order book, trades, fills, WebSocket | human strings, 4 decimals |
| Candles | human numbers |
