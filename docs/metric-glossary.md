# Metric glossary

The complete catalog and availability classification are in `docs/BI_PRODUCT_SPEC.md`. This glossary defines the certified metric families and prevents ambiguous report wording.

## M5 implementation status

The machine catalog is `contracts/m5-metric-catalog.json`: 54 complete contracts. Thirty-eight supported contracts are implemented. Exact comparability and transition rules use approved formula version `m5.2.0`; field-backed formulas use `m5.3.0`. Eleven methodology-gated contracts, two field extensions, and three external families remain unreleased. Approval records remain in the private delivery workspace.

Released components include release/accounting controls, governed issuance flow, security/loan ending populations, factor level/change, WALA/WAM, model-separated credit scores, delinquency-band and threshold rates, modification volume/rate, involuntary-removal volume/share, deferred balance/share, state/counterparty composition, Top-10/Other components, and HHI concentration.

## Release metrics

- **Physical input:** records delivered by a validated source member before business disposition.
- **Accepted / excluded / rejected / duplicate / quarantined:** mutually exclusive governed dispositions. An exclusion is documented and valid; a rejection or duplicate blocks release unless the contract explicitly defines otherwise.
- **Published/conformed:** accepted records represented in the intended release/conformed fact. Counts must reconcile to accepted population under the documented grain.
- **Acceptance/exclusion/rejection rate:** disposition count divided by physical input. Stability and explanation matter more than a universal direction.
- **Family completeness:** received required source packages divided by contract expectations for a reporting period.
- **Join coverage:** eligible records matched to the conformed key divided by eligible records. Unmatched, ambiguous, late, ineligible, and terminated reasons remain separate.
- **Correction/restatement volume:** records and UPB whose latest-known representation differs from the original-publication representation.
- **Comparability status:** rule-based pass/warn/fail for source coverage, schema, correction, population, and metric-eligibility changes. It is not a statistical claim.

## Issuance and balance metrics

- **Issued-security count:** unique accepted `(report_month, security_id)` issuance records.
- **Issuance UPB:** sum of `Issuance Investor Security UPB` for accepted issuance records.
- **Issuance mix share:** approved segment issuance UPB divided by monthly issuance UPB; unknown/unmapped remains explicit.
- **Current outstanding UPB:** sum of eligible current security or loan balance at the selected reporting date. It is semi-additive across time and must not be summed across reporting months.
- **Average security/loan size:** current or issuance UPB divided by the matching count. Report median/percentiles where concentration makes the mean misleading.
- **WAC / weighted attribute:** sum of eligible UPB × attribute divided by eligible UPB. The attribute context (original, issuance, updated, or current) must be named.
- **WALA / WAM:** UPB-weighted loan age / remaining maturity in months at the reporting date.
- **Factor:** provider-disclosed current factor for a security and reporting date. Issuance-date factor is not longitudinal performance.
- **Factor change:** current factor minus prior comparable factor for the same security; aggregate with approved balance weighting.
- **Ending-balance bridge:** beginning balance plus approved additions/adjustments less approved principal reductions/removals equals ending balance. Unexplained residual is visible and blocks derived speed claims above tolerance.
- **Paydown/runoff:** approved balance reduction under the bridge. It is not synonymous with voluntary prepayment.

## Prepayment metrics

- **SMM:** approved unscheduled principal reduction divided by the approved surviving-balance denominator for one month.
- **CPR:** `1 - (1 - SMM)^12`, after SMM inputs and timing pass. It is annualized, not a forecast.
- **Voluntary prepayment:** provider-supported borrower payoff/prepayment; excludes scheduled principal, curtailments, and involuntary removals when using the Freddie Mac Daily Prepayment definition.
- **Involuntary removal:** provider-disclosed count/UPB removed for involuntary reasons; report separately from voluntary behavior.
- **Seasoning curve:** approved speed by WALA for comparable cohorts.
- **Burnout:** change in speed for a seasoned/surviving cohort after prior refinance opportunities; requires an approved cohort and history definition.
- **PSA speed:** CPR expressed relative to the approved PSA convention; publish only after convention and eligibility review.

## Credit and servicing metrics

- **30+/60+/90+ delinquency rate:** eligible delinquent loan count or UPB divided by the eligible active population at the same as-of date. Count and UPB rates are distinct.
- **Roll rate:** beginning-cohort share moving from one delinquency state to another over the approved interval.
- **Cure rate:** beginning delinquent cohort returning to the approved current state over the approved interval.
- **Modification rate:** loans or UPB with a disclosed modification divided by the approved eligible population.
- **Deferred UPB share:** approved deferred balance divided by current UPB.
- **Assistance/resolution share:** eligible loan count or UPB with the disclosed assistance or alternative-resolution indicator.
- **Re-default:** a previously cured/modified loan re-entering the approved delinquency state within the approved window.

## Composition and concentration metrics

- **Weighted-average FICO/VS4, LTV/CLTV/ELTV, and DTI:** eligible UPB-weighted measures with model/type and original/current context named. Classic FICO and VS4 are never silently combined.
- **Segment share:** eligible count or UPB in a product, vintage, purpose, occupancy, property, channel, geography, seller, servicer, credit, or collateral category divided by its visible eligible total.
- **Mix-shift contribution:** segment current-period measure minus its prior comparable measure; contributions reconcile to total change.
- **Top-N share:** concentration held by the N largest entities/regions under current filters, with the remainder labeled `Other`.
- **HHI:** sum of squared segment shares using an explicitly named population and unit scale.
- **Mission/green/social share:** count or UPB with provider-disclosed flags; descriptive only and not an impact claim.

## Change and comparison rules

- **MoM/QoQ/YoY change:** current minus prior comparable period; percentage change is suppressed for zero/invalid denominators.
- **Rolling measure:** approved measure over a trailing period; balances use end-of-period or approved average rather than summing snapshots.
- **Cohort/vintage:** population fixed by an approved issuance/origination period and eligibility rule.
- **As reported / latest known:** metric calculated from original publication / the latest approved correction available at the selected as-of time.

## Current verified results

- 59,904 issued-security observations across 19 months.
- Approximately $1.106 trillion of issuance UPB in the verified window.
- 60,604 physical rows reconcile to 59,904 accepted, 700 documented exclusions, zero rejected, and zero duplicate keys.
- 99.29% of observed issuance UPB maps to the approved term-family taxonomy; 0.71% remains explicit and unmapped.

These are baseline evidence, not targets or statements of investment quality.

## External-only metric family

Price, yield, total return, OAS, Z-spread, option cost, duration, convexity, dollar duration, WAL, hedge ratios, TBA roll economics, MSR value, refinance incentive, benchmark-relative performance, macro sensitivity, and loss severity require separately governed sources/models. They must not appear as simulated, zero-filled, or disclosure-derived metrics.
