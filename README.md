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

## Run locally

```sh
npm run check
npm run inventory:sources
npm run load:raw
npm run check
npm run serve
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173).

`npm run check` is non-destructive: it runs Python and dashboard tests, validates the released payload, smoke-tests the static application, and checks project/Graphify freshness. `npm run inventory:sources` records only safe archive/member/schema metadata. `npm run load:raw` intentionally rebuilds the verified issuance release from authorized ignored files.

## Current and target scope

Implemented through M3: issuance UPB/count, corrections, official term-family composition, exact schemas, provenance, reconciliation, data-derived findings, resilient UI states, and aggregate-only local publication.

M4 is the next implementation milestone: approve and implement the security/loan source contract, corrections, conformed grains, joins, and backfill/incremental parity. M5–M9 add the metric engine, certified Power BI semantic model, nontechnical dashboard, investigation workflow, and governed API. M10–M12 remain separately gated AI, private-cloud, and reviewer-publication work.

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
