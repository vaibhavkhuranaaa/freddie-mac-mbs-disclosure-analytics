# Handoff

## Current result

M3 implementation is complete and awaiting exact-revision closure. The dashboard now derives findings from active data, removes issuance-date factor as a selectable insight, shows latest-month issuance by approved official UMBS term families, preserves an explicit unmapped group, exposes quality/freshness/methodology, and handles loading and fetch errors with recovery.

The current payload has 19 monthly rows and 95 mix rows. Official term-family mappings cover 99.29% of observed issuance UPB; 458 observations remain explicit under `Other / Unmapped prefix`.

## Exact next action

1. Commit the M3 pipeline, analytics, UI, tests, and contracts.
2. Rebuild the aggregate so metadata names that implementation revision.
3. Record M3 evidence, refresh Graphify/signature, run the full check, and commit closure evidence.
4. Do not begin M4 until authorized monthly factor/supplemental files and their data contract are available.

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
