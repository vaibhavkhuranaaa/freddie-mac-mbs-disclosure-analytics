# Data dictionary

Status: current issuance schema, verified M4 conformed facts, and restricted M5 metric components. Exact mappings remain machine-versioned in approved source/metric contracts.

## Classification

| Class | Examples | Authorized analyst | Reviewer/public |
| --- | --- | --- | --- |
| Restricted identifier | loan identifier, security identifier, CUSIP, source row | Yes | No |
| Restricted detail | loan/security-period row, seller/servicer detail, correction detail | Yes | No unless separately approved |
| Governed aggregate | approved count, UPB, rate, distribution, quality summary | Yes | Only by explicit release allowlist |
| Safe metadata | schema version, period, build ID, quality status | Yes | Yes when approved |

## Implemented restricted tables

### `monthly_security`

| Field | Meaning | Type/unit | Release boundary |
| --- | --- | --- | --- |
| `report_month` | validated issuance source period | `YYYY-MM` | aggregate grouping |
| `security_id` | Freddie Mac security identifier | text | restricted |
| `security_type` | source Prefix | text | approved taxonomy aggregate only |
| `issuance_upb` | investor security UPB at issuance | USD | aggregate only |
| `current_upb` | current UPB carried by the issuance source | USD | not longitudinal performance |
| `factor` | factor carried by the issuance source | ratio | validation only in current release |
| `revision_flag` | normalized source correction indicator | boolean | aggregate count |
| `source_file`, `source_row` | local lineage | text/integer | restricted |
| `schema_version` | reviewed input contract version | text | safe metadata |

The sample fixture contains compatibility-only fields used by pipeline tests. They are not certified business measures and do not appear in the reviewer metric catalog.

### `source_manifest`

Identity fields record file/family, report period, archive/member checksum, acquisition/load time, schema/layout version, pipeline revision, and build ID. Reconciliation fields record physical input, accepted, excluded, rejected, duplicate, quarantined, conformed, and published counts. `quality_status` must pass before release.

### `quality_issue`

Records source, row/record reference, severity, rule code, and a value-free explanation. Informational exclusions remain visible; errors block publication.

### M4 restricted control and facts

| Object | Storage/grain | Implemented fields | Boundary |
| --- | --- | --- | --- |
| `source_manifest`, `row_disposition`, `source_issue` | one source/version and value-free disposition/issue summaries | source checksum/schema/period, accepted/excluded/rejected/duplicate/quarantine/published counts, partition checksum | restricted local; aggregate evidence only in Git |
| `FactSecurityPeriodOriginal`, `FactSecurityPeriodLatest` | one security/factor period under original/latest precedence | restricted keys, status/correction, UPB/factor components, loan count, separate legacy/Classic FICO/VS4 fields, involuntary removal components | authorized only |
| `FactLoanPeriod` compressed partitions | one loan/security/report period/source version | restricted keys, correction, UPB components, term/age, separate score systems, delinquency/modification/deferral, geography, seller/servicer, join reason, record/source hash | authorized only |
| `join_reconciliation` | source family/report period/reason | matched, unmatched, ambiguous, late, ineligible, terminated counts | aggregate evidence; reviewer release still unapproved |
| `restatement_lineage` | original-to-replacement source version | hashed business key, as-of precedence, changed-record flag | authorized only |

Supplemental files remain at record-type-specific native grains. M4 validates and explicitly excludes their 419,478,342 records from `FactSecurityPeriod`/`FactLoanPeriod`; M5 may add a separate supplemental fact without flattening unlike grains.

### M5 restricted metric store

| Object | Grain / purpose | Boundary |
| --- | --- | --- |
| `input_partition` | one compressed loan partition with checksum, expected/scanned rows, active/all UPB components, peak RSS, and catalog hash | restricted local; safe counts/checksums may enter evidence |
| `partition_component` | one additive or weighted component per source partition, period, contract, dimension, and member | restricted local; seller/servicer members never enter tracked artifacts |
| `metric_component` | consolidated security, loan, segment, and portfolio numerator/denominator with explicit released flag | restricted local; reviewer/public release not approved |
| `run_metadata` | value-free catalog, count, memory, and normalized-snapshot evidence | safe metadata after verification |

`numerator` and `denominator` are decimal-integer text so weighted products cannot overflow SQLite 64-bit integers. `value` is derived; reconciliation uses exact components. Balance snapshots remain period-grained and are never rolled up as additive flows.

## M4 implemented and downstream target facts

| Fact | Grain | Core measures/attributes | Classification |
| --- | --- | --- | --- |
| `FactIssuance` | one accepted security at issuance month | issuance UPB, prefix/product, correction, source lineage | restricted detail |
| `FactSecurityPeriod` | one security per reporting period and source version; original/latest views | M4 conformance fields now; wider approved analytical fields may enter M5 only through contract/version changes | restricted detail |
| `FactLoanPeriod` | one loan/security per reporting period and source version | M4 approved fields, correction/source lineage, and join reason | restricted detail |
| `FactSupplementalDistribution` | provider-defined record type and period | bucket/distribution counts, balances, and source keys | restricted detail |
| `FactSourceQuality` | file/family/period/load | dispositions, schema, freshness, coverage, join results | safe metadata/aggregate |
| `FactRestatement` | original record/version to latest record/version | affected fields, count, UPB, reason, as-of times | restricted detail |
| `FactInvestigation` | one analyst-created investigation | owner, priority, status, filters, evidence, note, outcome | restricted operational |

## Conformed dimensions

| Dimension | Representative fields | Notes |
| --- | --- | --- |
| `DimDate` | reporting, issuance, origination, maturity, acquisition calendars | role-playing dates |
| `DimSecurity` | restricted security/CUSIP keys, prefix, structure flags | identifiers hidden outside authorized detail |
| `DimLoan` | restricted loan key | authorized detail only |
| `DimProduct` | prefix, term family, security type, eligibility | unknown remains explicit |
| `DimVintage` | issuance/origination month, quarter, year | stable cohort comparisons |
| `DimGeography` | state and approved region | map plus accessible table |
| `DimSeller`, `DimServicer` | source names/locations and governed display groups | top-N/Other rules versioned |
| `DimCreditBand` | score model, score band, unknown/not-applicable | Classic FICO and VS4 never blended silently |
| `DimLtvBand` | metric type, approved band, unknown/not-applicable | LTV/CLTV/ELTV context explicit |
| `DimLoanPurpose` | purchase/refinance/other source categories | source meanings preserved |
| `DimOccupancy` | primary/second/investment/unknown | source meanings preserved |
| `DimPropertyType` | source property categories | source meanings preserved |
| `DimChannel` | source origination channel | source meanings preserved |
| `DimAssistanceProgram` | modification, deferral, alternative resolution, plan | no causal/success inference |
| `DimSourceFile`, `DimSchemaVersion` | file/family/version/validity and acquisition metadata | lineage and comparability |

## Public aggregate payload currently implemented

| Field | Meaning | Type/unit |
| --- | --- | --- |
| `month` | reporting month | `YYYY-MM` |
| `security_count` | accepted issued securities | count |
| `issuance_upb` | accepted issuance UPB | USD |
| `current_upb` | current UPB in accepted issuance records | USD; not runoff |
| `average_factor` | unweighted issuance-source factor | ratio; not a performance insight |
| `correction_count` | accepted source correction flags | count |
| `mix[].product_group` | approved term family or explicit unmapped group | text |
| `mix[].security_count`, `issuance_upb`, `issuance_share` | monthly group measures | count/USD/ratio |
| `metadata.period_start/end`, `generated_at` | coverage and build time | period/UTC timestamp |
| `metadata.pipeline_version/revision`, `build_id`, `schema_versions` | transformation lineage | text/hash/list |
| `metadata.quality`, `metadata.mix` | release reconciliation and taxonomy coverage | objects |

## Source-field domains for M4/M5

- Identity/structure: Prefix, security identifier, CUSIP, status, correction, notification, issue/maturity, issuer/description, resecuritization/IO/ARM/step flags.
- Balances/factors: issuance/current security UPB, factor, original/issuance/current loan UPB, interest-bearing and deferred amounts, removal count/UPB.
- Rates/term: original/issuance/current/net rates, term, WAM/WALA, margins, indexes, caps, floors, adjustments.
- Credit/collateral: Classic FICO, VS4, LTV, CLTV, ELTV, DTI, loan amount, units, purpose, occupancy, property type, valuation method, channel, state, first-time buyer, MI, guarantee.
- Counterparty: seller and servicer names/locations.
- Performance/assistance: days delinquent, loan performance history, modifications/program/type/count/capitalized amount, deferrals, alternative resolution, borrower assistance.
- Mission: mission density/criteria, green/social, eligibility-program indicators.

Exact official labels, types, null rules, validity windows, sensitivity, and transformations belong in the M4 machine contracts. Presence in a header does not by itself approve a metric.
