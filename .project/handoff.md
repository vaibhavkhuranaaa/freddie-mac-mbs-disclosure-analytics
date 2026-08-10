# Handoff

## Current result

M3 is complete at implementation revision `c72602c3febd`. The dashboard derives findings from active data, removes issuance-date factor as a selectable insight, shows latest-month issuance by approved official UMBS term families, preserves an explicit unmapped group, exposes quality/freshness/methodology, and handles loading and fetch errors with recovery.

Build `5c6977cfad48...` contains 19 monthly rows and 95 mix rows. Official term-family mappings cover 99.29% of observed issuance UPB; 458 observations remain explicit under `Other / Unmapped prefix`. Automated pipeline/analytics tests, payload reconciliation, Impeccable detection, project records, and local HTTP smoke pass.

## Blocking next milestone

M4 requires authorized monthly security-factor and any approved supplemental source files. They are not present in the workspace. Before implementation, the owner must place them under restricted raw storage and approve a data-contract amendment covering source names, rights/demo boundary, grain, effective period, correction behavior, keys, field allowlist, and intended measures.

Do not substitute synthetic data for the reviewer-facing workflow and do not implement runoff/prepayment claims from issuance-date factor/current-UPB fields.

## Guardrails

- The term-family taxonomy is composition monitoring, not an equivalence or investment claim.
- Raw sources and local SQLite remain restricted and ignored.
- Factor, runoff, prepayment, AI, cloud, deployment, and publication remain gated.

## Recovery commands

```sh
npm run load:raw
npm run check
npm run serve
```
