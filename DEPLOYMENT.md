# Deployment decision record

## Current state

M11 deployed the governed application and derived product payload as an authenticated Azure Container Apps release candidate, verified it, and tore it down in the same session. No remote endpoint or cloud resource remains active.

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
4. Approve the exact reviewer model/payload, host, visibility, checksum, source revision, screenshots, domain, budget, and teardown for M12.

`netlify.toml` supports the current static application's no-build local/reviewer shape only. Its presence does not authorize deployment or public release.

GitHub Actions runs the complete local verification path. A deployed release is complete only when exact source/infrastructure/application revisions, model/payload checksum, approvals, and a verified live URL are recorded.

## Verified M11 shape

- Azure Container Apps consumption plan in Central US, maximum one replica and scale-to-zero.
- Microsoft Entra authentication on HTTPS-only ingress; spoofed identity headers and unauthenticated requests fail closed.
- The application Bicep requires tenant ID, client ID, and a secure client-secret parameter, then deploys the `authConfigs/current` child resource with `Return401`; secrets must be supplied through an ephemeral parameter file and never committed.
- Managed identity for immutable private-registry image pull; AI disabled.
- SQLite runtime state mirrored atomically to Azure Files after committed writes and restored on startup.
- Log Analytics for system and console telemetry plus application request audit.
- Resource-group budget, same-session rollback test, and complete resource-group and Entra teardown.
