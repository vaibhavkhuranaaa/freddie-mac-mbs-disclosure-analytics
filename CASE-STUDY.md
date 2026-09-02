# Freddie Mac MBS Disclosure Intelligence

Status: verified and publicly released provider-neutral decision product through M12

## Problem

Disclosure analytics fails business users when polished charts hide missing records, schema changes, correction effects, incompatible cohorts, or ambiguous denominators. The product must prove whether a release can be trusted before asking what changed.

## Verified result

- 19 official issuance files covering 2024-12 through 2026-06.
- 60,604 physical rows reconciled to 59,904 accepted/published observations and 700 documented exclusions.
- Zero rejected rows and zero duplicate business keys.
- Exact legacy and FICO/VS4 schemas with period-validity enforcement.
- Release payload carrying build, source, schema, period, quality, and taxonomy metadata.
- Active-data issuance/count/composition findings, explicit unmapped prefixes, evidence, limitations, and resilient accessible states.
- Non-destructive automated verification and a fail-closed source-intake gate.
- Approved contracts and exact inventory for 106 monthly-security/loan archives.
- 693,640,933 M4 rows reconciled with zero rejected, duplicate, or quarantined records.
- 9,240,038 security-period and 264,922,553 loan-period facts; every real loan join matched.
- Full, incremental, idempotence, stale-output, and active read-only M4 checks share snapshot `dbe035f51b4e7e163c5c53c5b6449ca62145877e408f7b3612cb3a1a2c1c881a`; sampled restricted-value matches in tracked artifacts are zero.
- 54 versioned metric contracts classified as 38 supported, 11 methodology-gated, 2 field-contract extensions, and 3 external families.
- All 38 supported contracts run over 264,922,553 loan rows and both 9,240,038-row security correction views, including nine M4 v2 field families plus roll, cure, new-delinquency, and redefault measures.
- 1,816 segment, weighted, and transition parity checks plus 1,068 independent formula checks pass; full/incremental metric checksum is `786b09b022bc4ab24a3e78c13947fac05410a5d3e946b2b616debc188b47bcea`.
- Exact comparability and transition rules are owner-approved, versioned as `m5-exact-methodology-v1`, and covered by safe golden cases.
- Atomic M5.7 cutover is verified at 45,675,380,656 stable bytes under a 43 GiB measured ceiling. The owner-approved superseded M5.6 rollback was permanently removed after active-release verification.
- A validated 20-period dashboard payload connects all 38 supported contracts to release, issuance, portfolio, credit, concentration, cohort, and evidence views.
- The investigation workflow persists owner, priority, status, immutable release/filter/evidence context, resolution, and mutation audit separately from source facts.
- The authenticated semantic API matches the product payload, rejects unauthenticated access, records request audit evidence without credentials, and passed 50 concurrent acceptance requests with 12.371 ms p95 latency.
- The bounded M10 cited assistant passed all six fixed decision, citation, privacy, safety, latency, cost, and workflow cases; its runtime route remains disabled by default.
- The M11 Entra-authenticated Azure release candidate passed eight security, recovery, observability, load, rollback, lineage, cost, and teardown categories before complete teardown.
- M12 publishes the live product and all 167 approved row-level source and derived artifacts; unauthenticated remote verification matched every asset size and SHA-256 digest.

## Product expansion

The acquired set includes 71 monthly-security and 35 monthly loan-level archives. M4 converts them into governed native-grain facts. M5 implements every currently supported measure, including nine M4 v2 field families and loan-history transitions, and closes on the approved reduced DPR boundary. M7-M9 deliver the provider-neutral dashboard, cohort and concentration evidence, governed investigation workflow, and semantic API. M10-M12 prove the bounded cited-assistant contract, private cloud operability, public product, and complete data release. M6 Power BI work remains parked and resumable against the same contracts.

The metric contract spans disclosure quality, issuance, outstanding balance, factor, runoff, approved SMM/CPR, delinquency transitions, modifications, deferrals, credit/collateral distributions, geography, seller/servicer concentration, and mission indicators. It explicitly separates implemented, methodology-gated, and external-data metrics.

## Decision value

A nontechnical stakeholder can decide whether a release is usable, identify a material change, isolate the segment or cohort driving it, recognize corrections or comparability issues, and assign an evidence-backed investigation without SQL. Reviewers can reproduce those decisions from the [live product](https://vaibhavkhuranaaa.github.io/freddie-mac-mbs-disclosure-analytics/) and [complete data release](https://github.com/vaibhavkhuranaaa/freddie-mac-mbs-disclosure-analytics/releases/tag/data-v1).

## Boundaries

Eleven exact-method contracts remain unreleased; two field extensions and three external families remain source-gated. The product does not infer voluntary prepayment from total balance decline, relabel involuntary removals as delinquent purchases, or claim price, yield, OAS, duration, convexity, valuation, trading, hedging, loss severity, borrower decisioning, or causation without separately governed data and methods.
