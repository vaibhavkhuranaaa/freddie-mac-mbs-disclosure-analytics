# Freddie Mac MBS Disclosure Intelligence — BI product specification

Status: implementation-ready product contract

Prepared: 2026-08-10

Audience: disclosure operations, MBS analytics leadership, data governance, and portfolio reviewers

## Product outcome

Build a governed Power BI decision product that lets a nontechnical stakeholder answer five questions in order:

1. Can the latest disclosure be trusted and compared with prior periods?
2. What changed in issuance, outstanding balance, factor, performance, or composition?
3. Which products, vintages, geographies, sellers, servicers, or borrower/property segments explain the change?
4. Is the movement economic, operational, or caused by a correction, schema change, or missing population?
5. What investigation should be assigned, with which source evidence?

The product has two isolated modes:

- **Authorized analyst mode:** full approved security-period and loan-period detail, governed drill-through, row-level evidence, export controls, issue notes, and all approved descriptive metrics.
- **Reviewer mode:** explicitly approved aggregates and safe provenance only. It never inherits access merely because the analyst model exists.

The current static issuance dashboard remains the verified baseline until the Power BI replacement proves metric parity and the owner approves a release change.

## Decision workflow and information architecture

```mermaid
flowchart LR
  A["Trust the release"] --> B["Detect material change"]
  B --> C["Explain the drivers"]
  C --> D["Validate corrections and comparability"]
  D --> E["Assign an investigation"]
  E --> F["Record evidence and outcome"]
```

| Page | Business question | Primary visuals | Decision output |
| --- | --- | --- | --- |
| 1. Executive overview | What changed, can I trust it, and where should I look? | KPI cards with period delta and sparkline; issuance/outstanding-balance trend; driver waterfall; top-three callouts | Prioritized review queue |
| 2. Release health and revisions | Is the release complete, timely, structurally valid, and restated? | release scorecard; source-family matrix; accepted/excluded/rejected bridge; correction timeline; unmatched-reason table | Publish, hold, or investigate |
| 3. Issuance and outstanding balance | How are new issuance and the active book changing? | UPB/count trends; product-share small multiples; term/vintage matrix; new-issuance-to-book ratio; change waterfall | Capacity and composition review |
| 4. Factor, paydown, and prepayment | Where is principal runoff changing? | factor/paydown trend; cohort CPR/SMM heatmap; refinance-incentive scatter only when external rates are approved; exception table | Cohorts requiring prepayment analysis |
| 5. Delinquency and assistance | Where is credit performance weakening or curing? | 30+/60+/90+ trends; roll-rate matrix; cure flow; modification/deferral/assistance small multiples | Servicing or cohort investigation |
| 6. Collateral and credit composition | Has the risk profile shifted? | FICO/VS4, LTV/CLTV, DTI distributions; purpose/occupancy/property/channel shares; mix-shift contribution chart | Underwriting/composition review |
| 7. Geography and counterparties | Where is exposure concentrated? | state matrix/map with table alternative; seller/servicer concentration; top-N plus Other; concentration trend | Concentration review |
| 8. Vintage and cohort explorer | Which origination/issuance cohorts behave differently? | vintage heatmap; cohort curves; WALA/WAM bands; segment selector; drill-through | Comparable cohort selection |
| 9. Investigation and methods | What evidence supports this finding? | governed detail table; source lineage; formula/version panel; filter context; investigation note | Reproducible handoff |

Every page owns one primary question, one plain-language takeaway, and no more than seven decision-bearing visuals. Page 9 is authorized-only.

## Metric catalog

Availability labels:

- **Now:** verified in the issuance pipeline.
- **Acquired:** fields exist in staged monthly security or loan-level files; implementation requires the versioned M4/M5 contract and tests.
- **Methodology gate:** source fields exist, but the formula, timing, denominator, or correction treatment must be approved before publication.
- **External:** requires a separately licensed and governed market, macroeconomic, valuation, liquidation, or recovery source.

### Release trust and data operations

| Metric | Definition / business use | Availability |
| --- | --- | --- |
| Expected, received, accepted, excluded, rejected, duplicate, quarantined, and published records | Complete population accounting by file, family, and period | Now for issuance; acquired for other families |
| Source acceptance and exclusion rates | Each disposition divided by physical input rows | Now |
| File completeness and family coverage | Received required packages divided by contract expectation | Acquired |
| Schema recognition and transition flags | Known schema/layout share and period-validity result | Now/acquired |
| Join coverage and unmatched reasons | Matched security/loan rows divided by eligible rows, with reason codes | Acquired |
| Correction/restatement volume and UPB | Count and balance affected by provider corrections; original/latest views | Acquired |
| Freshness and release lag | Publication/acquisition date minus reporting date | Acquired when timestamps are contracted |
| Comparability status | Pass/warn/fail for schema, population, correction, and coverage changes | Methodology gate |
| Data-quality score | Transparent component score; never hides component failures | Methodology gate |

### Issuance, balance, and portfolio structure

| Metric | Definition / business use | Availability |
| --- | --- | --- |
| Issuance UPB and security count | New observed issuance by period and segment | Now |
| Average/median security size | Issuance UPB divided by count plus distribution statistics | Acquired |
| Month-over-month, quarter-over-quarter, year-over-year change | Absolute and percentage change only when periods are comparable | Now/acquired |
| Rolling 3/6/12-month issuance | Trend stabilization and seasonality | Now; 12-month comparisons limited by history |
| Product/term mix and mix-shift contribution | Segment share and contribution to total period change | Now for approved prefix groups; acquired for more attributes |
| Current outstanding UPB and security/loan count | Active balance and population by reporting period | Acquired |
| New issuance as share of ending book | Issuance UPB divided by ending outstanding UPB | Acquired |
| Average/median loan balance | Current UPB divided by active loans plus distribution statistics | Acquired |
| WAC / weighted rates | UPB-weighted gross, net, issuance, and current rates | Acquired |
| WALA and WAM | UPB-weighted loan age and remaining maturity | Acquired |
| Factor level and factor change | Current factor and period-over-period movement | Acquired |
| Ending-balance bridge | Beginning balance + issuance/adjustments − principal reductions = ending balance | Methodology gate |
| Gross and net paydown/runoff | Balance reduction with explicit issuance, correction, removal, and termination treatment | Methodology gate |
| Involuntary removal count/UPB/share | Provider-disclosed involuntary removals relative to beginning population | Acquired |

### Prepayment and cash-flow behavior

| Metric | Definition / business use | Availability |
| --- | --- | --- |
| Single Monthly Mortality (SMM) | Approved unscheduled principal reduction divided by approved surviving balance denominator | Methodology gate |
| Conditional Prepayment Rate (CPR) | `1 - (1 - SMM)^12`, after SMM source/timing approval | Methodology gate |
| Paydown rate | Total principal reduction divided by beginning balance; not labeled voluntary prepayment | Methodology gate |
| Cohort CPR/SMM | Approved speed by vintage, product, WALA, coupon, FICO, LTV, purpose, state, and servicer | Methodology gate |
| Burnout / seasoning curve | Speed by WALA and prior cumulative paydown for comparable cohorts | Methodology gate |
| Voluntary versus involuntary principal reduction | Separate provider-supported categories; never infer one from the other | Methodology gate |
| Refinance incentive and S-curve | Borrower/security rate relative to approved market mortgage rate | External |
| PSA speed | CPR relative to the approved PSA benchmark | Methodology gate/external convention review |

Freddie Mac's Daily Prepayment Report publishes daily voluntary total prepayments as SMM and CPR and states that these figures exclude scheduled principal, curtailments, and involuntary prepayments. It is a separate grain and calculation from monthly factors, so it is a validation/extension source rather than a substitute for the monthly contract.

### Credit, delinquency, and loss mitigation

| Metric | Definition / business use | Availability |
| --- | --- | --- |
| Days-delinquent distribution | Current, 1–29, 30–59, 60–89, 90+, and approved severe bands | Acquired |
| 30+/60+/90+ delinquency rate | Delinquent active-loan count and UPB divided by eligible active population | Methodology gate |
| Roll and cure rates | Movement between delinquency states on a consistent beginning cohort | Methodology gate |
| New delinquency and re-default | Newly entering a delinquency band and returning after cure/modification | Methodology gate |
| Modification count/rate and capitalized amount | Modified loans and amounts divided by eligible population | Acquired/methodology gate |
| Deferred UPB/share | Non-interest-bearing and total deferral balances relative to current UPB | Acquired |
| Borrower-assistance and alternative-resolution share | Loans with disclosed assistance/resolution indicators | Acquired |
| Government-guarantee and MI share | Current UPB/count by guarantee and insurance status | Acquired |
| Delinquent loan purchases | Provider-disclosed count/UPB where available | Acquired after field contract |
| Loss severity, recovery, and realized loss | Liquidation loss net of recoveries divided by resolved exposure | External; current files are insufficient |

### Credit, collateral, mission, and concentration

| Metric | Definition / business use | Availability |
| --- | --- | --- |
| Weighted-average and distributional FICO/VS4 | Current or origination score, with score-model version explicit | Acquired |
| Weighted-average and distributional LTV/CLTV/ELTV | Approved denominator and current/origination context explicit | Acquired |
| Weighted-average DTI | UPB-weighted original DTI | Acquired |
| Purpose, occupancy, units, property type, channel | Count/UPB/share and period mix shift | Acquired |
| First-time-homebuyer share | Count/UPB share using disclosed indicator | Acquired |
| State concentration | Count/UPB/share and change by property state | Acquired |
| Seller and servicer concentration | Top-N share and segment exposure | Acquired |
| HHI concentration | Sum of squared entity or geography shares; formula/version displayed | Methodology gate |
| Mission Density Score / Mission Criteria Share | Provider-disclosed mission metrics | Acquired for applicable securities |
| Green, social, and special-eligibility shares | Provider-disclosed flags; no impact claim without separate evidence | Acquired |

### Metrics explicitly outside the current disclosure product

Price, yield, total return, OAS, Z-spread, option cost, duration, convexity, dollar duration, WAL, hedge ratio, TBA roll economics, MSR value, benchmark-relative performance, home-price stress, unemployment sensitivity, and causal attribution require separately approved market, cash-flow-model, benchmark, or macroeconomic data. They belong in a later governed extension, not as blank or simulated dashboard tiles.

## Metric contract standard

Every published measure must record:

- business name, technical name, plain-language meaning, and decision supported;
- formula, numerator, denominator, unit, sign convention, aggregation behavior, and desired direction when meaningful;
- source family, field lineage, grain, as-of timing, eligibility, exclusions, missing-value treatment, and correction policy;
- filter behavior, additive/semi-additive/non-additive classification, valid comparison windows, and minimum population rule;
- formula version, owner, effective date, test fixture, reconciliation tolerance, limitation, and approved release modes.

No visual may introduce a calculation that is absent from the semantic model and glossary.

## Power BI semantic model

Use a star schema with explicit measures and conformed dimensions. Avoid bidirectional relationships and implicit measures.

### Facts

- `FactIssuance`: one accepted security at issuance month.
- `FactSecurityPeriod`: one security per reporting period, latest/original correction views.
- `FactLoanPeriod`: one authorized loan per reporting period; restricted.
- `FactSupplementalDistribution`: provider distribution records at their documented grain.
- `FactSourceQuality`: file/family/period counts, freshness, schema, and disposition.
- `FactRestatement`: original-to-latest changes and affected measures.
- `FactInvestigation`: analyst-owned note, status, priority, evidence reference, and resolution.

### Dimensions

`DimDate`, `DimSecurity`, `DimLoan` (restricted), `DimProduct`, `DimVintage`, `DimGeography`, `DimSeller`, `DimServicer`, `DimCreditBand`, `DimLtvBand`, `DimLoanPurpose`, `DimOccupancy`, `DimPropertyType`, `DimChannel`, `DimAssistanceProgram`, `DimSourceFile`, and `DimSchemaVersion`.

Use surrogate warehouse keys, retain source keys only in restricted dimensions, and implement role-playing dates where issue, origination, maturity, acquisition, and reporting dates differ.

### Model behavior

- Import mode is the local baseline; use incremental refresh only after period-boundary and correction tests pass.
- Provide `As reported` and `Latest known` calculation views. Never overwrite the evidence of an original publication.
- Use field parameters for controlled measure/segment switching, not arbitrary data access.
- Use aggregations or summary facts for executive pages while retaining authorized drill-through to governed detail.
- Define row-level security by analyst role/population only when Power BI Service is approved. Object-level security hides restricted identifiers/fields. Workspace write roles are not treated as RLS-protected consumers.
- Disable or constrain underlying-data export, Analyze in Excel, and Build permissions for restricted datasets when service deployment is approved.

## Interaction and visual standards

- Global filters: reporting month, comparison period, product/term, vintage, purpose, occupancy, property type, state, seller, servicer, FICO/VS4 band, LTV band, delinquency band, and correction view.
- Persistent controls: reset filters, last refresh, coverage, quality/comparability status, metric definition, and export classification.
- Use KPI cards, lines, small multiples, 100% stacked bars, waterfall bridges, cohort heatmaps, conditional matrices, scatterplots, and drill-through tables according to the analytical question.
- Use maps only when location is the question and always provide an equivalent sortable table.
- Avoid 3D charts, decorative gauges, unlabeled pies, dual axes with unlike units, rainbow palettes, and dashboards that rely on hover.
- Every color encoding has a text/icon equivalent. Keyboard order, focus, alt text, high contrast, 200% zoom, and screen-reader labels are release criteria.
- Show `Why this matters`, `What changed`, and `Next review` in plain language. Describe association, not causation.

## Governance, privacy, and retention

- Row-level use is approved for the authorized local product. Raw and derived restricted data are retained seven years from acquisition and deleted earlier if authorization ends.
- Seven-year retention is a lifecycle rule, not an analytical-history claim. The current analytical history begins with the acquired files; extend it only through verified packages and schemas.
- Restricted data stays out of Git, public artifacts, screenshots, logs, prompts, traces, and reviewer exports.
- Public/demo redistribution remains unapproved. A public model must be generated from an explicit allowlist and pass disclosure review.
- AI, cloud services, paid resources, deployment, and publication remain separate approval gates.

## History recommendation

The current 2024/2025–2026 acquisition is enough to build and validate the model but is short for stable seasonality and rate-cycle interpretation. After M4–M6 prove schema-safe backfill, target at least five years of monthly history and preferably the full approved seven-year analytical window. Retain each acquired file for seven years from acquisition; do not confuse that retention clock with a promise that seven years of observations are already present.

## Authoritative references

- [Freddie Mac Single-Family Disclosure Guide v6.2](https://capitalmarkets.freddiemac.com/mbs/docs/disclosure_guide.pdf)
- [Freddie Mac Security-Level Disclosure glossary](https://capitalmarkets.freddiemac.com/mbs/docs/pc_disclosure_glossary.pdf)
- [Freddie Mac MBS disclosure resources](https://capitalmarkets.freddiemac.com/mbs/security-data/mbs-disclosure-resources)
- [Freddie Mac Daily Prepayment Report](https://capitalmarkets.freddiemac.com/mbs/daily-prepayment-report)
- [Microsoft Power BI star-schema guidance](https://learn.microsoft.com/en-ie/power-bi/guidance/star-schema)
- [Microsoft Power BI accessibility guidance](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports)
- [Microsoft Power BI semantic-model security](https://learn.microsoft.com/en-us/training/modules/enforce-semantic-model-security/)
- [Microsoft Power BI incremental refresh](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure)
- [Microsoft Power BI field parameters](https://learn.microsoft.com/en-nz/power-bi/create-reports/power-bi-field-parameters)

## Definition of usable

The BI product is usable when a nontechnical stakeholder can complete the trust-to-investigation workflow without SQL, all displayed totals reconcile to the governed model, every change can be explained through filters and evidence, restricted detail is accessible only to authorized users, and a failed quality/comparability gate is more prominent than the business result it invalidates.
