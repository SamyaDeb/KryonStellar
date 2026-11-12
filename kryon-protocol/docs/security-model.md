# Security model (superseded)

This document has been superseded by the security section of the documentation site:

- [Threat model](../../docs/docs/08-security/threat-model.md)
- [Access control](../../docs/docs/08-security/access-control.md)
- [Security mechanisms](../../docs/docs/08-security/security-mechanisms.md) — verified controls, separated from recommendations

The previous version listed several controls that are not implemented in this repository (for example replayable keeper decisions, cursor-based RPC event ingestion, matcher queue-priority reset on replace, and liquidation rewards capped to available equity) and described funding as imbalance-based. The new pages describe only what the code does. The previous text remains in the Git history.
