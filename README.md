# Freddie Mac MBS Disclosure Intelligence

A governed MBS disclosure analytics product in progress. The verified baseline processes official Freddie Mac issuance files locally, reconciles every source row, and presents aggregate issuance monitoring. The implementation roadmap expands it into a full authorized Power BI decision workflow using the acquired monthly security and loan-level history.

## Verified baseline

- 19 issuance files from 2024-12 through 2026-06.
- 60,604 physical rows = 59,904 accepted/published + 700 documented status-`C` exclusions + 0 rejected + 0 duplicates.
- Two exact issuance schemas, including the December 2025 FICO/VS4 transition.
- 19 monthly aggregate rows and 95 term-family mix rows; 99.29% of issuance UPB is mapped and the remainder stays explicit.
- Active-data findings, resilient accessible states, source/build/schema/quality metadata, and a fail-closed release gate.

## Acquired implementation inputs

- 71 monthly-security archives: one December 2024 sample, all 48 applicable 2025 packages, and all 22 applicable 2026 packages through the August/March family endpoints.
- 35 monthly loan-level archives: 20 `fu` files through August 2026 and 15 `au` files through its March 2026 retirement, approximately 9.1 GiB compressed.
- Restricted row-level use is authorized. Retention is seven years from acquisition, with earlier deletion if authorization ends.

These files are ignored by Git and are not public assets. Public/demo redistribution is separately gated.

Restricted files live outside this repository. By default, commands use sibling `../freddie-mac-mbs-disclosure-analytics-data`; set absolute `MBS_DATA_ROOT` to use another external location. Layout is `raw/`, one `current/` release, isolated `build/`, and value-free `manifests/`.

## Verified M4 conformance

- Approved machine contracts govern 71 monthly-security and 35 loan-level archives across exact legacy, FICO/VS4, retirement, and April 2026 consolidation windows.
- 693,640,933 physical records reconcile to 274,162,591 accepted/published conformed rows and 419,478,342 explicit supplemental native-grain exclusions, with zero rejected, duplicate, or quarantined rows.
- Restricted outputs contain 9,240,038 security-period and 264,922,553 loan-period facts. All loan joins are matched in the acquired population; unmatched, ambiguous, late, ineligible, and terminated behaviors remain golden-tested.
- Backfill and unchanged incremental runs produce snapshot SHA-256 `ec3862e9f6c1f4531424a26e4d3934b12b4e690ebb14fe58e8fd343c81074528`.

## Verified M5 metric engine

- Machine-readable catalog contains 54 contracts: 27 supported/implemented, 13 methodology-gated, 11 field-contract extensions, and 3 external families.
- Restricted local SQLite output contains 256,821 released additive, weighted, and approved derived components; HHI, delinquency-threshold rates, modification rate, and involuntary-removal share are released for restricted local use.
- All 35 loan partitions and 264,922,553 rows reconcile; both original/latest security views cover 9,240,038 rows.
- 684 segment/weighted checks and 360 independent derived-formula checks pass with measured peak RSS of 37,355,520 bytes.
- Full external-path rebuild and independent verification share checksum `08ce8c2a43990f52d1544415a49ec81584d0c856748f8b4ede423b91952bf229`.

## Verified storage boundary

- One external canonical set contains 125 checksummed archives; one active release contains issuance, M4, 35 loan partitions, and M5 outputs.
- Recovery ledger records every retained and removed file with size, checksum, producer, consumers, retention, recovery source, cleanup action, and final state. All destination checksums match; all classified recoverable or valueless files were removed.
- Product repository contains no physical analytical data, generated release, cache, bytecode, dated graph output, copied tool, stale prompt, or migrated legacy record.
- Stable v1 analytical storage is 40,173,821,505 bytes. This exceeds the 34 GiB target, so M5.3 must meet the approved compact-partition benchmark or record a revised budget before M4 v2.

## Run locally

```sh
npm run check
npm run inventory:sources
npm run load:raw
npm run load:m4
npm run verify:m4
npm run load:m5
npm run verify:m5
npm run storage:check
npm run check
npm run serve
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173).

`npm run check` is non-destructive: it runs Python and dashboard tests, validates the released payload, smoke-tests the static application, and checks project/Graphify freshness. `npm run inventory:sources` records only safe archive/member/schema metadata. `npm run storage:check` fails on repository analytical data, canonical duplicates, multiple releases, build residue, or inadequate free space. `npm run load:raw` intentionally rebuilds the verified issuance release from authorized external files.

Full `load:m4` and `load:m5` commands write only to `MBS_DATA_ROOT/build/manual/`; they never replace `current/`. Incremental verification reads the active release. A later cutover requires full parity and an explicit verified switch.

## Current and target scope

Implemented through M3: issuance UPB/count, corrections, official term-family composition, exact schemas, provenance, reconciliation, data-derived findings, resilient UI states, and aggregate-only local publication.

Implemented M5 boundary: every currently supported local metric contract, additive numerator/denominator components, approved derived formulas, correction views, score-model separation, real-inventory reconciliation, and bounded-memory streaming. M5 remains in progress while exact provider rules, field extensions, transition methods, and deferred inputs are resolved; M6 has not started. M6–M9 add the certified Power BI model, nontechnical dashboard, investigation workflow, and governed API. M10–M12 remain separately gated AI, private-cloud, and reviewer-publication work.

The [BI product specification](docs/BI_PRODUCT_SPEC.md) defines the pages, industry metric catalog, semantic model, visuals, user experience, governance, and history recommendation. [Scope](docs/scope.md) records implemented and planned boundaries.

The project does not make borrower, investment, valuation, trading, hedging, or unsupported causal decisions.

## Project records

- `PROJECT.md` — business and scope contract
- `DESIGN.md` — BI visual, interaction, language, and accessibility rules
- `docs/BI_PRODUCT_SPEC.md` — complete decision product and metric specification
- `docs/architecture.md` — current and target system design
- `docs/scope.md` — implemented, gated, and excluded capabilities
- `docs/data-dictionary.md` — grains, fields, classifications, and release boundaries
- `docs/metric-glossary.md` — governed measure definitions and limitations
- `contracts/` — versioned machine source and metric contracts
- Private sibling delivery workspace — approvals, milestones, evaluation evidence, state, and handoff
- `CASE-STUDY.md` — current verified result and target value
