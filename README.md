# Freddie Mac MBS Disclosure Intelligence

A governed data-engineering and analytics case study. The implemented release processes authorized official Freddie Mac month-end issuance files locally, proves how every physical source row was handled, and presents aggregate issuance monitoring without exposing security-level data.

## Verified release data

- 19 observed files from December 2024 through June 2026.
- 60,604 physical source rows reconciled to 59,904 published observations and 700 documented status-`C` exclusions.
- Zero rejected rows and zero duplicate business keys in the verified build.
- Two exact source schemas, with the FICO/VS4 transition enforced from December 2025.
- A 19-row aggregate payload carrying period, build, pipeline, schema, and quality metadata.

## Run the reviewer workflow

```sh
npm run check
npm run load:raw
npm run check
npm run serve
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173).

`npm run check` is non-destructive. It runs 12 pipeline and release tests, validates the actual released aggregate payload, smoke-tests the static preview, and checks the project records. Sample output stays under ignored `local/` paths. `npm run load:raw` is the intentional rebuild from authorized ignored source files.

## How the quality gate works

1. Validate the official ZIP name and its single matching text member.
2. Match the ordered header to a reviewed SHA-256 schema fingerprint and allowed period.
3. Validate balances, factor, correction flag, security key, and duplicate business keys.
4. Count accepted, documented exclusions, rejected, duplicate, quarantined, and published rows per source.
5. Block publication unless every source passes and all counts reconcile.
6. Publish monthly aggregates and safe build/quality metadata only.

The 700 excluded rows are all status-`C` securities whose issuance UPB, current UPB, and factor are blank. They are recorded explicitly rather than silently discarded. Any other incomplete balance combination fails the build.

## Current scope

Implemented: issuance UPB, issued-security count, source correction count, exact schema control, provenance, quality reconciliation, and aggregate-only local dashboard publication.

Planned under approval-gated milestones: issuance composition, monthly factor and supplemental sources, balance/runoff/prepayment measures, authenticated analyst workflow, governed semantic API, evaluated cited assistant, cloud pilot, and public portfolio release.

The project does not make borrower, investment, valuation, trading, or hedging decisions.

## Project records

- `PROJECT.md` — approved business and product contract
- `.project/data.md` — source rights, grain, fields, quality, privacy, and release boundary
- `.project/evaluation.md` — verified and proposed evaluation gates
- `.project/milestones.yml` — approved M0–M10 executable roadmap
- `.project/refinement-plan.md` — end-to-end architecture, AI safety, and risk plan
- `.project/handoff.md` — exact continuation state
- `CASE-STUDY.md` — stakeholder-readable current result and limitations
