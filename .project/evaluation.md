# Evaluation contract

Status: M0–M4 verified; M5 supported contracts verified and acceptance blocked by external gates

## Verified baseline

| Gate | Target | Verified result |
| --- | --- | --- |
| Source reconciliation | input = accepted + excluded + rejected + duplicate | 60,604 = 59,904 + 700 + 0 + 0 |
| Publication reconciliation | accepted = stored = published | 59,904 = 59,904 = 59,904 |
| Source quality | all files pass | 19/19 pass |
| Schema recognition | all period-compatible | 12 legacy-v1; 7 fico-v2 |
| Duplicate/rejected rate | zero for release | zero |
| Idempotence | normalized rebuilds equal | automated test passes |
| Released-payload safety | check/sample paths do not alter release | regression test passes |
| Issuance mix | group totals reconcile; unknown explicit | 95 rows; 99.29% UPB mapped |
| UI behavior | derived findings and resilient accessible states | automated/static checks pass |

## M4 source and conformance gates

| Gate | Verified result |
| --- | --- |
| Exact source inventory | 106/106 approved M4 archives; 71 security + 35 loan; 0 invalid/missing |
| Row reconciliation | 693,640,933 = 274,162,591 accepted/published + 419,478,342 excluded + 0 rejected + 0 duplicate |
| Conformed facts | 9,240,038 security-period + 264,922,553 loan-period |
| Join reconciliation | 264,922,553 matched; 0 unmatched/ambiguous/late/ineligible/terminated in real population |
| Correction/as-of | 73,280 provider-corrected security rows; 0 same-period replacement versions in acquired set; golden original/latest correction fixtures pass |
| Backfill/incremental parity | identical SHA-256 `ec3862e9f6c1f4531424a26e4d3934b12b4e690ebb14fe58e8fd343c81074528` |
| Restricted-output safety | 228 sampled restricted tokens; 0 tracked matches; 0 tracked restricted paths |

- All 71 monthly-security and 35 loan-level archives must pass exact package, member, schema/layout, validity-period, row, and reconciliation rules.
- Every physical record receives one documented disposition; accepted records reconcile to conformed facts.
- Eligible joins reconcile to matched, unmatched, ambiguous, late, ineligible, and terminated reasons by family/period.
- Backfill and incremental processing produce identical normalized conformed outputs for the same as-of view.
- Original-publication and latest-known correction views reproduce golden correction fixtures.
- No restricted row value appears in Git, public artifacts, logs, command summaries, or test failure snapshots.
- Tests include each schema transition, the April 2026 consolidation, malformed/unknown layouts, duplicate keys, missing periods, corrections, and join failures.

All M4 gates above pass. Supplemental native-grain distributions remain explicit M5-deferred exclusions from the two M4 fact outputs; no M5 business formula is released.

## M5 metric gates

- 100% of released measures have the complete metric contract required by `docs/BI_PRODUCT_SPEC.md`.
- Security, loan, cohort, vintage, segment, and portfolio totals reconcile to additive components within a documented tolerance; count/UPB bridges target exact equality.
- Weighted measures reproduce independently calculated golden numerators and denominators.
- Snapshot metrics are not summed across time; zero/invalid denominators are suppressed and explained.
- Corrections, issuance, removals, terminations, missing periods, low balances, schema transitions, and score-model transitions are covered.
- SMM/CPR, runoff, roll/cure, and HHI remain unreleased until a domain reviewer approves their formula fixtures.
- Voluntary, scheduled, curtailment, involuntary, and correction principal movements are never silently combined.

### Verified supported-contract result

| Gate | Verified result |
| --- | --- |
| Contract coverage | 54 complete resolved contracts: 23 supported, 17 methodology-gated, 11 contract-extension-required, 3 external |
| Supported implementation | 23/23 supported contracts emit released components; no gated/external contract is released |
| Real loan reconciliation | 35/35 partitions; 264,922,553/264,922,553 rows |
| Real security reconciliation | 9,240,038 latest rows and 9,240,038 original rows |
| Additive/weighted parity | 564 segment and weighted numerator/denominator checks pass |
| Idempotence | full and unchanged incremental checksum `7f83b73d126631fe16bfa13e205dec1d4bd2ec3c22c4efa21d21252543d5d6d3` |
| Bounded memory | measured peak RSS 29,196,288 bytes while scanning the full loan population |
| Release safety | 256,355 supported components released locally; 180 candidates explicitly unreleased; restricted-output inspection passes |

M5 milestone acceptance is not complete. Cohort/vintage and eleven other measures need approved field-contract extensions; seventeen formulas need recorded domain approval. `.project/m5-approval-request.json` is pending and does not self-approve either gate.

## M6 semantic-model gates

- Every certified Power BI measure matches the metric engine exactly under representative filter combinations.
- Relationship direction/cardinality, unknown members, role-playing dates, and many-to-many exceptions are tested.
- Restricted fields are absent from unauthorized metadata, visuals, exports, drill-through, and role tests.
- Full and incremental refresh agree across range boundaries and late corrections.
- Executive pages meet the agreed refresh and interaction target on current and synthetic 10x structural fixtures; actual thresholds are recorded before release.

## M7–M8 stakeholder and UX gates

Test at least five representative users or conduct a documented expert walkthrough when access is limited.

| Task | Target |
| --- | --- |
| Confirm whether the release is usable | at least 90% correct without coaching |
| Identify the largest material change and period | at least 90% correct |
| Identify a primary driver/cohort | at least 85% correct |
| Recognize a correction/non-comparable period | at least 90% correct |
| Reach evidence and state a next investigation | at least 85% complete within 3 minutes |
| Interpret metric direction/limitation | no material misunderstanding in final round |

Accessibility gates: WCAG 2.2 AA contrast, complete keyboard order, visible focus, screen-reader labels, high-contrast mode, 200% zoom, color-independent status, and an accessible alternative for every visual conclusion. No page exceeds seven decision-bearing visuals.

## M8–M9 governance/API gates

- Every executive exception drills to a reproducible filter/evidence context.
- Investigation create/update actions preserve source facts and produce audit records.
- Authorized and reviewer modes pass negative access and artifact-inspection tests.
- API, metric engine, and Power BI totals match exactly; no arbitrary SQL/raw-row endpoint exists.
- Contract, filter, pagination, concurrency, error, and 10x performance tests pass.

## M10 optional AI gates

These targets do not authorize an AI service:

- 100% deterministic metric agreement on the golden set.
- At least 95% grounded-answer pass rate and 98% citation precision.
- At most 1% unsupported material-claim rate.
- 100% refusal/redirect for investment, valuation, hedging, lending, and unsupported causal prompts.
- No restricted raw fields in prompts, traces, retrieval, citations, or responses.
- Measurable improvement in investigation time or accuracy versus the non-AI workflow.

## Responsible use

The product is descriptive security/portfolio analytics, not borrower decisioning. Segment fields must not be turned into lending, protected-class, investment, or causal judgments. Any expanded borrower use requires separate legal, privacy, fairness, stakeholder, and public-claims review.

## Cloud/release gates

Performance, availability, recovery, security, cost, and teardown thresholds are finalized only after provider/region/tier/usage approval. Publication requires exact source and deployment revisions, approved payload/model checksum, accessibility and live verification, restricted-artifact inspection, rollback proof, and recorded owner approval.
