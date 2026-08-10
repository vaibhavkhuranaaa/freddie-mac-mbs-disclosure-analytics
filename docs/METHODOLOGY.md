# Methodology

## Current verified issuance method

1. Discover only exact `FRE_IS_YYYYMM.zip` packages and matching text members.
2. Validate filename/member period, archive structure, exact ordered-header fingerprint, and schema validity window.
3. Normalize approved fields and apply required-key, balance, factor, correction, status, and duplicate rules.
4. Record every physical row as accepted, documented exclusion, rejected, or duplicate/quarantined.
5. Store accepted restricted observations, immutable source manifests, and value-free quality events locally.
6. Reconcile physical input to dispositions and accepted records to the aggregate payload.
7. Block publication unless every source passes.
8. Generate monthly issuance, term-family composition, safe metadata, findings, and investigation prompts from active data.

The implemented release treats status-`C` rows with blank issuance UPB, current UPB, and factor as documented informational exclusions. Every other invalid/incomplete balance combination blocks publication.

## M4 source method

The value-free inventory hashes archives and records member names, encryption flags, physical row counts, header fingerprints, and headerless record-type widths without emitting disclosure values. The acquired set contains 71 monthly-security and 35 monthly loan-level archives for the requested window.

M4 must approve and implement, in order:

1. source family, native grain, period/as-of meaning, exact schema/layout validity, and sensitive-field classification;
2. field allowlist, type/null/range rules, business/surrogate keys, and duplicate semantics;
3. correction precedence plus immutable `As reported` and `Latest known` views;
4. security-period and loan-period linkage with matched, unmatched, ambiguous, late, ineligible, and terminated reasons;
5. disposition and join reconciliation by source/period;
6. historical-backfill/incremental parity and restricted-output inspection.

Discovery proves availability, not metric correctness or redistribution rights.

## Metric method

All measures follow `docs/BI_PRODUCT_SPEC.md` and `docs/metric-glossary.md`. Each carries numerator, denominator, unit, source grain/timing, eligibility, exclusions, null behavior, filter behavior, formula version, owner, comparison window, test evidence, and limitation.

- Snapshot balances are semi-additive across time.
- Weighted averages use additive weighted numerators and eligible-UPB denominators.
- Original/current/updated attributes and Classic FICO/VS4 score systems remain explicit.
- Corrections are calculated under both original-publication and latest-known views.
- Roll/cure and cohort measures use a fixed eligible beginning population.
- Paydown must reconcile through the approved balance bridge.
- SMM/CPR remain unavailable until unscheduled principal, scheduled principal, involuntary removal, corrections, and denominator timing are approved and tested.
- External market, valuation, macroeconomic, liquidation, and recovery metrics remain absent without separate sources.

The implemented M5 engine resolves `.project/m5-metric-catalog.json`, streams each compressed loan partition independently, stores exact additive/weighted components, then consolidates them across source families. It reuses unchanged partition components only when partition checksum, catalog checksum, expected rows, and engine version match. Security calculations run separately for original-publication and latest-known views. Candidate HHI and delinquency-threshold components carry `released=0`; no bridge, runoff, SMM/CPR, roll/cure, or external metric is released.

## BI and interpretation method

The Power BI model uses native-grain facts, conformed dimensions, explicit measures, single-direction relationships, controlled field parameters, and certified filter behavior. No report-local calculation may create a new business measure.

Dashboard findings describe observed changes and concentration. They do not assert causation, investment quality, borrower risk decisions, or valuation conclusions. A quality/comparability failure suppresses or visibly qualifies the affected comparison.

## Reproducibility

```sh
npm run check
npm run inventory:sources
npm run load:raw
npm run load:m4
npm run load:m5
npm run verify:m5
npm run check
```

Raw files and local databases are restricted and ignored. The released payload contains aggregates and approved safe metadata only.
