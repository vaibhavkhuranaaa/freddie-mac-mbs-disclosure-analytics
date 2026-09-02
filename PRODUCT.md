# Product

<!-- impeccable:product-schema 1 -->

## Platform

Responsive web application backed by the existing verified SQLite release. Power BI remains a later, resumable presentation target.

## Stack

Static HTML, CSS, and JavaScript for the client; Python standard library and read-only SQLite for the provider-neutral semantic service; existing repository validation and test tooling.

## Users

Disclosure operations specialists and MBS analytics leaders who need to validate a release, understand material changes, and assign a bounded investigation without writing SQL.

## Purpose

Turn verified Freddie Mac disclosure data into a trustworthy decision workflow that moves from release health to change, drivers, comparability, and evidence-backed follow-up.

## Positioning

Evidence-first disclosure intelligence. The product favors explicit provenance, correction lineage, visible limitations, and reproducible investigation over unexplained scores or speculative interpretation.

## Operating Context

Users first confirm the release is usable, then identify what changed, inspect the strongest disclosed drivers, test whether periods are comparable, and preserve the filters and evidence needed for follow-up.

## Capabilities and Constraints

- Use only source-backed, released metric contracts. Never infer unavailable measures or silently substitute a proxy.
- Keep source values and generated analytical data outside Git until the explicit publication gate. The publication target is complete row-level source and derived data with provenance.
- Preserve both `As reported` and `Latest known` correction views wherever the released engine supports them.
- Treat Power BI as parked, not cancelled. Continue provider-neutral dashboard, investigation, and API work without pretending Power BI acceptance has passed.
- Do not use AI, paid services, cloud resources, deployment, or publication without their separate approvals.
- Avoid valuation, trading, hedging, lending, causality, and borrower-judgment claims.

## Evidence on Hand

- Verified issuance release.
- Conformed M4 security and loan facts with exact lineage and correction handling.
- Immutable M5 release with 38 supported contracts and full-population parity evidence.
- Explicit unreleased catalog entries for methodology-, field-, and external-data-gated measures.

## Product Principles

- Trust before interpretation.
- One primary business question per view.
- Make filters, period, correction view, quality, comparability, and metric version visible.
- Every exception must lead to reproducible evidence and a clear next action.
- Missing, partial, stale, non-comparable, and refused states must name the cause and recovery path.

## Accessibility

Meet WCAG 2.2 AA. Support keyboard navigation, visible focus, 200% zoom, meaningful status text, non-color status cues, and accessible summaries or tables for every chart conclusion.
