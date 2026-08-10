# Deployment decision record

## Current state

The verified static issuance dashboard runs locally at `http://127.0.0.1:4173`. Git revision lineage exists, but no remote, hosted environment, cloud account connection, public visibility, or paid resource is configured.

## Local workflow

```sh
npm run load:raw
npm run check
npm run serve
```

Power BI M6 begins as a local Import model. Power BI Service, gateway, tenant roles, RLS/OLS, refresh capacity, licensing, and sharing are deployment decisions, not local-development assumptions.

## Deployment gates

1. Complete M4–M9 data, metric, semantic-model, dashboard, investigation, and API evidence.
2. Approve provider/tenant, region, residency, identity, licensing, cost ceiling, retention, backup, recovery, and teardown for M11.
3. Pass infrastructure, security, access, observability, load, failure-recovery, rollback, restore, and cost tests in a private pilot.
4. Approve the exact reviewer model/payload, host, visibility, checksum, source revision, screenshots, domain, budget, and teardown for M12.

`netlify.toml` supports the current static application's no-build local/reviewer shape only. Its presence does not authorize deployment or public release.

GitHub Actions runs the complete local verification path. A deployed release is complete only when exact source/infrastructure/application revisions, model/payload checksum, approvals, and a verified live URL are recorded.
