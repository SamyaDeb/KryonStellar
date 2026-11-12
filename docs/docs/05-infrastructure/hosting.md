---
title: Hosting
sidebar_position: 7
---

# Hosting

```text
browser -> Cloudflare -> tunnel -> VM
                                   web app (Next.js)
                                   WebSocket server
                                   services (PM2)
                                   PostgreSQL (local only)
```

Nothing on the VM listens publicly; the Cloudflare Tunnel dials out. The docs are built into `client/public/docs` and served at `/docs`. Pushes to `main` deploy through `.github/workflows/deploy-production.yml`, which checks `/api/ready` afterwards. Host setup lives in `kryon-protocol/infra/a1flex/`.
