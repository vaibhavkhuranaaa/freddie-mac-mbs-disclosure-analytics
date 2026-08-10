# Freddie Mac MBS Disclosure Intelligence

## Charter

- **Industry:** mortgage-backed securities disclosure analytics
- **Current implemented release:** month-end Freddie Mac security-level issuance monitoring with fail-closed quality and provenance
- **Target product:** governed issuance, composition, factor, balance/runoff, prepayment, revision, and disclosure-quality investigation workflow
- **Primary stakeholder:** MBS disclosure operations or market-data analyst
- **Authorized data use:** the project owner is an authorized Freddie Mac user and may acquire and process the relevant source files for this project
- **Current delivery:** local static dashboard, local SQLite processing, $0 operating baseline
- **Current data coverage:** 19 official issuance files from December 2024 through June 2026

## Purpose

Build a reproducible analyst workflow that answers what changed, whether the change is data-related or activity-related, what evidence supports it, and what should be investigated next. Preserve an aggregate-only reviewer mode while developing a separately governed authorized analyst mode.

## Current business question

Where did issuance accelerate, cool, and change composition over the observed period, and what should an operations or market-data team investigate next?

## Implemented capabilities

- Validates exact official `FRE_IS_YYYYMM.zip` archive names, members, ordered-header fingerprints, and source periods.
- Recognizes the legacy issuance schema through November 2025 and the FICO/VS4 schema beginning December 2025.
- Reconciles physical input, accepted, documented-exclusion, rejected, duplicate, quarantined, and published counts per source file.
- Blocks publication when a schema, row, duplicate, or reconciliation rule fails.
- Stores accepted security observations, SHA-256 source manifests, and value-free quality events in local SQLite.
- Publishes aggregate-only monthly dashboard data with period, generation, pipeline, build, schema, and quality metadata.
- Runs automated official-file, failure-path, idempotence, payload, non-destructive, and static-preview checks.

## Verified baseline

- 60,604 physical rows across 19 official files.
- 59,904 accepted and published issuance observations.
- 700 documented status-`C` blank-balance exclusions.
- Zero rejected rows and zero duplicate business keys in the verified build.
- 19 monthly aggregate rows covering 2024-12 through 2026-06.

## Current limitations

- The implemented source set is issuance-only. Issuance-date factor and current UPB are not measures of subsequent runoff.
- Issuance mix is planned for M3 after the Prefix taxonomy is approved and tested.
- Balance movement, paydown, CPR/prepayment, timeliness, and supplemental monitoring require separately approved monthly factor and supplemental files.
- Authenticated analyst mode, AI, cloud infrastructure, deployment, and public publication are not implemented or authorized.
- The product is descriptive operational analytics; it does not make borrower decisions or provide investment, valuation, hedging, or trading recommendations.

## Success criteria

The end-to-end product is complete when the analyst workflow, data contracts, governed measures, authorized/public access boundary, evaluation, security, operations, deployment evidence, case study, and publication records satisfy M0–M10 in `.project/milestones.yml`.

## Delivery roadmap

The approved executable plan is `.project/milestones.yml`; the detailed architecture, AI safety, risks, and approval gates are in `.project/refinement-plan.md`.
