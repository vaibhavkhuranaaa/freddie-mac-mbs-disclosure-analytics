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

## Verified M4 conformance

- Approved machine contracts govern 71 monthly-security and 35 loan-level archives across exact legacy, FICO/VS4, retirement, and April 2026 consolidation windows.
- 693,640,933 physical records reconcile to 274,162,591 accepted/published conformed rows and 419,478,342 explicit supplemental native-grain exclusions, with zero rejected, duplicate, or quarantined rows.
- Restricted outputs contain 9,240,038 security-period and 264,922,553 loan-period facts. All loan joins are matched in the acquired population; unmatched, ambiguous, late, ineligible, and terminated behaviors remain golden-tested.
- Backfill and unchanged incremental runs produce snapshot SHA-256 `ec3862e9f6c1f4531424a26e4d3934b12b4e690ebb14fe58e8fd343c81074528`.

## Verified M5 supported metric engine

- Machine-readable catalog contains 54 contracts: 23 supported/implemented, 17 methodology-gated, 11 field-contract extensions, and 3 external families.
- Restricted local SQLite output contains 256,355 released additive/weighted components and 180 explicitly unreleased candidates.
- All 35 loan partitions and 264,922,553 rows reconcile; both original/latest security views cover 9,240,038 rows.
- 564 segment and weighted-component parity checks pass with measured peak RSS of 29,196,288 bytes.
- Full and unchanged incremental outputs share checksum `7f83b73d126631fe16bfa13e205dec1d4bd2ec3c22c4efa21d21252543d5d6d3`.

## Run locally

```sh
npm run check
npm run inventory:sources
npm run load:raw
npm run load:m4
npm run verify:m4
npm run load:m5
npm run verify:m5
npm run check
npm run serve
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173).

`npm run check` is non-destructive: it runs Python and dashboard tests, validates the released payload, smoke-tests the static application, and checks project/Graphify freshness. `npm run inventory:sources` records only safe archive/member/schema metadata. `npm run load:raw` intentionally rebuilds the verified issuance release from authorized ignored files.

## Current and target scope

Implemented through M3: issuance UPB/count, corrections, official term-family composition, exact schemas, provenance, reconciliation, data-derived findings, resilient UI states, and aggregate-only local publication.

Implemented M5 boundary: every currently supported local metric contract, additive numerator/denominator components, correction views, score-model separation, real-inventory reconciliation, and bounded-memory streaming. M5 acceptance remains blocked by recorded field-contract and domain-methodology approvals; M6 has not started. M6–M9 add the certified Power BI model, nontechnical dashboard, investigation workflow, and governed API. M10–M12 remain separately gated AI, private-cloud, and reviewer-publication work.

The [BI product specification](docs/BI_PRODUCT_SPEC.md) defines the pages, industry metric catalog, semantic model, visuals, user experience, governance, and history recommendation. The [milestone plan](.project/milestones.yml) is the execution contract.

The project does not make borrower, investment, valuation, trading, hedging, or unsupported causal decisions.

## Project records

- `PROJECT.md` — business and scope contract
- `DESIGN.md` — BI visual, interaction, language, and accessibility rules
- `docs/BI_PRODUCT_SPEC.md` — complete decision product and metric specification
- `.project/refinement-plan.md` — architectural and delivery rationale
- `.project/milestones.yml` — executable M0–M12 roadmap
- `.project/data.md` — rights, grain, fields, quality, retention, and release boundary
- `.project/evaluation.md` — verification and stakeholder success gates
- `.project/state.md` and `.project/handoff.md` — exact continuation state
- `CASE-STUDY.md` — current verified result and target value
