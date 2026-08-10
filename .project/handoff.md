# Handoff

## Current result

M3 is complete at implementation revision `c72602c3febd`. The dashboard derives findings from active data, removes issuance-date factor as a selectable insight, shows latest-month issuance by approved official UMBS term families, preserves an explicit unmapped group, exposes quality/freshness/methodology, and handles loading and fetch errors with recovery.

Build `5c6977cfad48...` contains 19 monthly rows and 95 mix rows. Official term-family mappings cover 99.29% of observed issuance UPB; 458 observations remain explicit under `Other / Unmapped prefix`. Automated pipeline/analytics tests, payload reconciliation, Impeccable detection, project records, and local HTTP smoke pass.

M4 intake preparation is committed at `29db1f055d32`. The command validates a machine-readable governance contract, exact archive/member/schema/period rules, required families, and value-free metadata. Eighteen Python tests now pass without resource warnings.

## Blocking next milestone

M4 requires authorized monthly security-factor and any approved supplemental source files. They are not present in the workspace. A fail-closed intake gate is now implemented: it recognizes all 19 existing issuance archives, emits no disclosure row values, reports zero approved M4 archives, and exits 2 when readiness is required.

Before integration, the owner must place the authorized files under restricted raw storage and approve `.project/m4-source-contract.json`. Use `.project/m4-data-intake.md` to record exact archive/member conventions, rights/demo boundary, retention, grain, effective period, correction behavior, keys, schema fingerprints/validity, field allowlist, intended measures, and required families. Discovery alone must not change the contract to approved.

Do not substitute synthetic data for the reviewer-facing workflow and do not implement runoff/prepayment claims from issuance-date factor/current-UPB fields.

## Guardrails

- The term-family taxonomy is composition monitoring, not an equivalence or investment claim.
- Raw sources and local SQLite remain restricted and ignored.
- Factor, runoff, prepayment, AI, cloud, deployment, and publication remain gated.

## Recovery commands

```sh
npm run load:raw
npm run inventory:sources
npm run check
npm run serve
```

After the owner supplies and approves M4 sources, run the fail-closed gate before writing a parser:

```sh
python3 scripts/source_inventory.py --input data/raw --contract .project/m4-source-contract.json --require-ready
```
