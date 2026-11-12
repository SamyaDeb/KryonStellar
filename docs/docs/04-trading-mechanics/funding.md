---
title: Funding
sidebar_position: 6
---

# Funding

Funding keeps the perp close to spot. When the perp trades above the oracle, longs pay shorts; below it, shorts pay longs.

```text
premium = (mark - index) / index
rate    = clamp(premium x coefficient, -max rate, +max rate)    per hour
delta   = rate x min(seconds since last update, 3600) / 3600
long index  += delta
short index -= delta
your funding = -size x (index now - index when you last settled)
```

- **Mark** is the time-weighted average fill price since the last update, so a burst of trades cannot move it much.
- **Index** is the oracle price.
- **Coefficient and max rate** are set per market with `set_funding_config`.

Anyone can call `update_funding`. Our funding keeper calls it every 15 minutes. One call never charges more than an hour, so a missed update under-charges rather than over-charges.

Funding is included in your equity right away and settles into your balance the next time the position changes.
