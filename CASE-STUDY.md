# Freddie Mac MBS Disclosure Intelligence

Status: verified issuance product with an implementation-ready BI expansion

## Problem

Disclosure analytics fails business users when polished charts hide missing records, schema changes, correction effects, incompatible cohorts, or ambiguous denominators. The product must prove whether a release can be trusted before asking what changed.

## Verified result

- 19 official issuance files covering 2024-12 through 2026-06.
- 60,604 physical rows reconciled to 59,904 accepted/published observations and 700 documented exclusions.
- Zero rejected rows and zero duplicate business keys.
- Exact legacy and FICO/VS4 schemas with period-validity enforcement.
- Aggregate-only release carrying build, source, schema, period, quality, and taxonomy metadata.
- Active-data issuance/count/composition findings, explicit unmapped prefixes, evidence, limitations, and resilient accessible states.
- Non-destructive automated verification and a fail-closed source-intake gate.

## Product expansion

The acquired restricted set now includes 71 monthly-security and 35 monthly loan-level archives. The roadmap converts these sources into a certified Power BI product for nine stakeholder workflows: executive overview, release health/revisions, issuance/balance, factor/prepayment, delinquency/assistance, collateral/credit, geography/counterparties, vintage/cohorts, and investigation/methods.

The metric contract spans disclosure quality, issuance, outstanding balance, factor, runoff, approved SMM/CPR, delinquency transitions, modifications, deferrals, credit/collateral distributions, geography, seller/servicer concentration, and mission indicators. It explicitly separates implemented, methodology-gated, and external-data metrics.

## Decision value

A nontechnical stakeholder should be able to decide whether a release is usable, identify a material change, isolate the segment/cohort driving it, recognize corrections or comparability issues, and assign an evidence-backed investigation without SQL. Authorized analysts retain full governed detail; a reviewer release is generated separately from an approved aggregate allowlist.

## Boundaries

The current release remains issuance-only until M4–M8 evidence is complete. The product does not infer voluntary prepayment from total balance decline and does not claim price, yield, OAS, duration, convexity, valuation, trading, hedging, loss severity, borrower decisioning, or causation without separately governed data/methods. It is local and unpublished; cloud, AI, deployment, and publication are not approved.
