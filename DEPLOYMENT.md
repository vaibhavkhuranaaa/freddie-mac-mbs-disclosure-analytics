# Deployment decision record

## Current state

M11 deployed the governed application and derived product payload as an authenticated Azure Container Apps release candidate, verified it, and tore it down in the same session. No Azure endpoint or cloud resource remains active.

M12 publishes the verified static product through [GitHub Pages](https://vaibhavkhuranaaa.github.io/freddie-mac-mbs-disclosure-analytics/) and all approved row-level source and derived artifacts through the immutable [`data-v1` GitHub Release](https://github.com/vaibhavkhuranaaa/freddie-mac-mbs-disclosure-analytics/releases/tag/data-v1). The public manifest records every asset size and SHA-256 digest.

## Local workflow

```sh
npm run load:raw
npm run check
npm run serve
```

Power BI M6 begins as a local Import model. Power BI Service, gateway, tenant roles, RLS/OLS, refresh capacity, licensing, and sharing are deployment decisions, not local-development assumptions.

## Deployment gates

1. Complete M4-M9 data, metric, semantic-model, dashboard, investigation, and API evidence.
2. Approve provider/tenant, region, residency, identity, licensing, cost ceiling, retention, backup, recovery, and teardown for M11.
3. Pass infrastructure, security, access, observability, load, failure-recovery, rollback, restore, and cost tests in a private pilot. M11 completed this gate on 2026-09-01.
4. Verify public product health, exact source revision, complete release-asset membership, byte sizes, SHA-256 digests, accessibility, and rollback. M12 completed this gate on 2026-09-02.

`netlify.toml` preserves a provider-neutral static-hosting option. The current public release is the GitHub Pages workflow recorded above.

GitHub Actions runs the complete local verification path. A deployed release is complete only when exact source/infrastructure/application revisions, model/payload checksum, approvals, and a verified live URL are recorded.

## Verified M11 shape

- Azure Container Apps consumption plan in Central US, maximum one replica and scale-to-zero.
- Microsoft Entra authentication on HTTPS-only ingress; spoofed identity headers and unauthenticated requests fail closed.
- The application Bicep requires tenant ID, client ID, and a secure client-secret parameter, then deploys the `authConfigs/current` child resource with `Return401`; secrets must be supplied through an ephemeral parameter file and never committed.
- Managed identity for immutable private-registry image pull; AI disabled.
- SQLite runtime state mirrored atomically to Azure Files after committed writes and restored on startup.
- Log Analytics for system and console telemetry plus application request audit.
- Resource-group budget, same-session rollback test, and complete resource-group and Entra teardown.
