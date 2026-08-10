# Metric glossary

## Issued-security count

- Definition: accepted security rows in a validated month-end issuance file.
- Method: count unique `(report_month, security_id)` records after exclusions and quality gates.
- Business meaning: scale and cadence of new securitization activity.
- Desired direction: contextual; unusual movement prompts investigation rather than a good/bad judgment.
- Baseline/result: 59,904 observations across 19 months in the verified 2024-12 to 2026-06 build.
- Supported decision: where issuance activity changed enough to review capacity, comparability, or source quality.
- Limitation: security count does not measure credit performance, market value, or investor demand.

## Issuance UPB

- Definition: total `Issuance Investor Security UPB` for accepted issuance observations.
- Method: sum by report month after the source quality gate.
- Business meaning: dollar scale of observed new issuance.
- Desired direction: contextual; peaks and troughs are investigation signals.
- Baseline/result: approximately $1.106 trillion across the verified observed period.
- Supported decision: which periods require operational or market-activity review.
- Limitation: does not measure later balance runoff, valuation, returns, or causal drivers.

## Correction count

- Definition: accepted rows whose source correction indicator is true.
- Method: sum normalized boolean correction flags by month.
- Business meaning: visible source correction activity in the accepted issuance population.
- Desired direction: lower is generally operationally simpler, but zero does not prove the absence of upstream corrections.
- Baseline/result: zero in the verified accepted issuance build.
- Supported decision: whether a period merits source-revision review.
- Limitation: limited to the indicator supplied in the issuance file.

## Source acceptance rate

- Definition: accepted issuance observations divided by physical source rows.
- Method: `accepted_count / input_count` from the reconciled source manifest.
- Business meaning: share of delivered rows entering issuance aggregates.
- Desired direction: stable and explained; a change requires investigation.
- Baseline/result: 59,904 / 60,604 = approximately 98.84%.
- Supported decision: whether a release population is comparable and publishable.
- Limitation: the remaining 700 rows are documented status-`C` exclusions, not invalid data.

## Documented exclusion count

- Definition: status-`C` source rows with issuance UPB, current UPB, and factor all blank.
- Method: exact status and all-three-fields-blank rule; event is recorded with informational severity.
- Business meaning: securities delivered in the source that do not belong in balance-based issuance aggregates.
- Desired direction: contextual and monitored for unexpected change.
- Baseline/result: 700 across 19 source files.
- Supported decision: whether accepted totals reconcile to the physical source without silent row loss.
- Limitation: the rule is specific to the observed issuance source and must be reviewed if provider semantics change.

## Quality status

- Definition: release gate for every source file.
- Method: `pass` only when schema/period validation succeeds, no rejected or duplicate rows exist, counts reconcile, and at least one accepted row exists.
- Business meaning: whether the governed aggregate publication may proceed.
- Desired direction: all source files `pass`.
- Baseline/result: 19 of 19 source files pass in build `7c0f195305e1...`.
- Supported decision: publish or stop and investigate.
- Limitation: proves implemented rules and reconciliation, not every possible source-provider error.

## Issuance mix share

- Definition: a term-family group's issuance UPB divided by total accepted issuance UPB for the month.
- Method: map CL/ZL, CT/ZT, CI/ZI, and CN/ZN using the Freddie Mac Prefix Library Summary; aggregate every other prefix as `Other / Unmapped prefix`.
- Business meaning: identifies which term family contributes to a monthly issuance change.
- Desired direction: contextual; a mix shift is an investigation signal, not good/bad performance.
- Baseline/result: 99.29% of observed-period issuance UPB is mapped; 0.71% remains explicit and unmapped.
- Supported decision: whether the latest total movement is broad or concentrated in a term family.
- Limitation: term-family grouping does not make different structures economically identical and does not replace security-level review.
