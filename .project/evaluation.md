# Evaluation contract

Status: `M2 approved and verified locally; later-milestone targets remain proposed`

## M2 trust-foundation metrics

| Metric | Method | Target | Verified result | Decision supported | Limitation |
| --- | --- | --- | --- | --- | --- |
| Source reconciliation | Sum per-file manifest counts | Input = accepted + excluded + rejected + duplicates | 60,604 = 59,904 + 700 + 0 + 0 | Whether the aggregate build is complete enough to publish | Does not prove source-provider completeness beyond delivered files |
| Publication reconciliation | Compare accepted rows, stored observations, and published count | All equal | 59,904 = 59,904 = 59,904 | Whether the dashboard payload traces to accepted records | Aggregate-only validation does not inspect every upstream source meaning |
| Quality status | Fail-closed manifest gate | `pass` for every source | 19 of 19 pass | Whether publication is allowed | Status-`C` exclusion is a documented business rule, not an error |
| Schema recognition | Ordered-header SHA-256 plus period bounds | 100% known and period-compatible | 12 legacy-v1 files; 7 fico-v2 files | Whether transformation semantics are known | A future provider schema requires review before loading |
| Duplicate rate | Duplicate `(report_month, security_id)` / input | 0 for release | 0 / 60,604 | Whether security-period measures could be double counted | Key is issuance-specific and may change for later sources |
| Rejected-row rate | Rejected / input | 0 for release | 0 / 60,604 | Whether invalid data entered the aggregate | Valid exclusions are reported separately |
| Idempotence | Rebuild identical inputs twice and compare normalized payload | Exact match except generation timestamp | Passing automated test | Whether a rebuild is reproducible | Git revision changes legitimately change metadata |
| Released-payload safety | Compare released payload checksum around sample/check paths | Unchanged | Passing regression test | Whether reviewer data can be overwritten accidentally | Intentional `load:raw` rebuild remains authorized behavior |

## Engineering gates

- Unit/integration tests cover official success, schema transition, missing headers, period mismatch, malformed archive layout, invalid values, duplicate keys, aggregate accuracy, idempotence, sample isolation, and payload failure.
- Static preview smoke test must serve the HTML, JavaScript, CSS, and validated aggregate payload locally.
- CI must run `npm run check` on pushes and pull requests.
- Raw files must remain ignored and absent from Git tracking.

## M3 product and accessibility targets

- Five analyst tasks: confirm release health, identify peak/latest change, inspect composition, trace a finding to methodology, and identify the next investigation.
- No critical automated or manual WCAG 2.2 AA issue.
- Complete loading, empty, partial, stale, and error states.
- Every chart has an equivalent plain-language summary and accessible evidence table.
- Findings remain correct when peak, trough, latest period, and year boundary change.

Current M3 implementation evidence:

- Monthly mix security counts, UPB, and shares reconcile to every monthly total in the payload validator.
- Pure analytics tests cover payload rejection, zero-denominator handling, cross-year month labels, latest mix ordering, and derived findings.
- Loading and error states use an `aria-live` status region and a named retry action; the default HTML renders a loading explanation before JavaScript completes.
- Trend labels include month and year, the chart has a generated accessible description, and the evidence table remains available.
- Impeccable's mechanical detector returned no findings for the changed HTML, CSS, and JavaScript.
- Local HTTP smoke returned 200 for the application and served a passing 19-month/95-mix-row payload.

## M4–M6 analytical and product targets

- The M4 intake readiness gate must remain blocked while the source contract is pending, emit no disclosure row values, recognize the 19 governed issuance archives, and reject missing required families or unapproved schema fingerprints.
- Cross-source joins quantify matched, unmatched, duplicate, corrected, and late records by period.
- Every measure records definition, formula, timing, denominator, unit, desired direction, evidence, supported decision, and limitation.
- Security, cohort, portfolio, API, and dashboard totals reconcile exactly on golden fixtures.
- Public and authorized analyst access boundaries pass negative authorization tests.
- A 10x-data performance test establishes scale triggers before a managed analytical database is introduced.

Current readiness evidence: six source-inventory tests cover the pending-contract blocker, row-value non-disclosure, exact approved archive/member/schema matching, unapproved-schema failure, required governance fields, and the command's fail-closed exit status. The actual restricted inventory reports 19 governed issuance archives, zero approved M4 archives, and blocked readiness.

## M7 AI targets

These targets do not authorize an AI service:

- 100% deterministic metric agreement on the golden set.
- At least 95% grounded-answer pass rate and 98% citation precision.
- At most 1% unsupported material-claim rate.
- 100% refusal/redirect pass rate for prohibited investment, valuation, hedging, lending, and causal-advice prompts.
- No restricted raw fields in prompts, traces, retrieval documents, citations, or responses.
- A measured analyst outcome improves relative to the non-AI workflow.

## Fairness and responsible-use evaluation

The current product performs aggregate security/disclosure monitoring and does not make borrower decisions. Fairness evaluation therefore focuses on preventing unsupported subgroup interpretation, protecting restricted attributes, and ensuring the UI/AI layer does not turn descriptive portfolio fields into lending or investment recommendations. Any later use of borrower-composition fields requires a separate stakeholder, legal, privacy, fairness, and public-claims review.

## Cloud/release targets

Cloud performance, availability, recovery, security, cost, and teardown targets must be finalized only after the platform, region, tiers, usage assumptions, identity model, and budget receive explicit approval. Publication requires exact deployed revision/payload evidence and a public-artifact leakage review.
