# Freddie Mac MBS Disclosure Intelligence

Status: draft — issuance trust foundation implemented; later analytical and release milestones pending

## Problem

Month-end disclosure files can support issuance monitoring only when the analyst can distinguish accepted observations, documented exclusions, quality failures, duplicates, and provider schema changes. A polished chart without that lineage can hide incomplete totals.

## Current workflow

The authorized local workflow validates official Freddie Mac issuance ZIP names, embedded members, exact ordered-header fingerprints, source-period compatibility, row-level business rules, and duplicate keys. It writes accepted security observations, a source manifest, and value-free quality events to local SQLite. Publication occurs only after every source passes and all counts reconcile.

## Verified result

- 19 official files covering 2024-12 through 2026-06.
- 60,604 physical source rows.
- 59,904 accepted and published issuance observations.
- 700 documented status-`C` blank-balance exclusions.
- Zero rejected rows and zero duplicate business keys.
- Two explicit schemas, including the observed December 2025 FICO/VS4 transition.
- Aggregate-only dashboard payload with build, schema, period, and quality metadata.

## Analyst use

The current product supports release validation and descriptive issuance monitoring. An analyst can verify that dashboard totals trace to accepted records and that no row disappeared silently. The next milestone turns that trusted foundation into a data-derived issuance and composition investigation workflow.

## Limitations

The implemented data is issuance-only. It does not yet support longitudinal balance runoff, paydown, prepayment, disclosure timeliness, valuation, trading, hedging, or borrower decisions. Monthly factor and supplemental sources require separate acquisition and approval. The application is local and has not been deployed or published.
