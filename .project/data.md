# Data contract

Status: `authorized row-level local use; M4 contracts implemented; M5 supported-field metrics implemented locally`

## Rights and release boundary

- The project owner confirmed authorized Freddie Mac source-file use on 2026-08-01.
- Official source ZIPs remain under ignored `data/raw/` storage and are never committed or included in a public artifact.
- The reviewer-facing application receives monthly aggregates and safe quality/provenance metadata only.
- Security identifiers, CUSIPs, seller/servicer attributes, descriptions, and security-level rows are restricted to the authorized local workflow.
- The requested `fd`, `ar`, `fq`, and `ge` monthly-security history is acquired under restricted raw storage: all 48 packages for 2025, plus 22 packages through the applicable August/March 2026 family endpoints and one December 2024 Core File 1 sample.
- The requested `fu` and `au` monthly loan-level history is also acquired. The owner authorizes local row-level use; the approved M4 contracts machine-version exact fields, schemas, joins, corrections, and release modes.

## Current source family

| Property | Verified value |
| --- | --- |
| Source | Official Freddie Mac month-end issuance security files |
| File convention | `FRE_IS_YYYYMM.zip` containing exactly `FRE_IS_YYYYMM.txt` |
| Coverage | 2024-12 through 2026-06 |
| Files | 19 |
| Physical source rows | 60,604 |
| Accepted issuance observations | 59,904 |
| Documented exclusions | 700 status-`C` securities with issuance UPB, current UPB, and factor all blank |
| Rejected rows | 0 in the verified build |
| Duplicate business keys | 0 in the verified build |
| Schema versions | `fre-is-legacy-v1` through 2025-11; `fre-is-fico-v2` from 2025-12 |
| Local storage | SQLite security-period table, source manifest, and quality ledger |

## Grain and business key

- Source grain: one disclosed security row in one month-end issuance source file.
- Accepted analytical grain: one `(report_month, security_id)` issuance observation.
- Duplicate rule: a repeated `(report_month, security_id)` is quarantined and blocks publication.
- Report month is derived from the validated source filename and must be compatible with the exact header schema version.

## Current field allowlist

Only these official fields are used by the implemented issuance pipeline:

- `Security Identifier` — local business key; never published.
- `Prefix` — mapped in the aggregate layer using the approved official UMBS term taxonomy below.
- `Issuance Investor Security UPB` — issuance balance measure.
- `Current Investor Security UPB` — retained for source reconciliation; not interpreted as subsequent runoff in issuance files.
- `Security Factor` — retained for validation; issuance-date factor is not presented as performance analytics.
- `Security Data Correction Indicator` — correction count.
- `Security Status Indicator` — used only to classify the documented status-`C` blank-balance exclusion.

All other source columns are ignored by the current transformation and remain restricted.

## Approved issuance-mix taxonomy

Source: Freddie Mac Prefix Library Summary — `https://capitalmarkets.freddiemac.com/mbs/docs/prefix_library_explainer.pdf`.

| Aggregate group | Prefixes |
| --- | --- |
| 30-year UMBS / Supers family | CL, ZL |
| 20-year UMBS / Supers family | CT, ZT |
| 15-year UMBS / Supers family | CI, ZI |
| 10-year UMBS / Supers family | CN, ZN |
| Other / Unmapped prefix | Every other observed code |

The taxonomy groups official term-related prefixes for composition monitoring; it does not assert that UMBS, Supers, and reverse-REMIC securities are economically identical. In the verified M3 payload, 59,446 observations and 99.29% of issuance UPB are mapped; 458 observations and 0.71% remain explicit and unmapped.

## Quality rules

1. ZIP name, embedded member, and report period must match exactly.
2. The ordered header must match a reviewed SHA-256 schema fingerprint.
3. The legacy schema is valid only through 2025-11; the FICO/VS4 schema begins in 2025-12.
4. Security identifier and prefix are required for accepted issuance rows.
5. Issuance UPB must be positive; current UPB must be non-negative and not exceed issuance UPB.
6. Security factor must be greater than zero and at most one.
7. A status-`C` row with all three balance/factor fields blank is an informational exclusion.
8. Any other incomplete or invalid row is rejected, quarantined, and blocks publication.
9. Duplicate business keys are quarantined and block publication.
10. Input must reconcile to accepted + excluded + rejected + duplicates; published must equal accepted.

## Retention and privacy

- Restricted raw and security-level derived data are retained for seven years from acquisition and deleted earlier if authorization ends.
- Cloud retention, identity, backup, and residency require separate approval before provisioning.
- Public payloads contain no security identifiers or security-level rows.
- Quality event details contain rule descriptions and row numbers, not raw values.
- The project performs portfolio/security analytics and does not use borrower-level decisioning.

## Observed M4 candidates

The four restricted samples contain 20,447,529 physical records. `fd241205.zip` and `ar250107.zip` are 96-column headered Core files with distinct reviewed header fingerprints. `fq250107.zip` and `ge250107.zip` are headerless Supplemental multi-record files with 30 and 44 observed record types; the first field chooses a record-specific column layout. Structural validation found zero unknown record types and zero record-width failures. These are safe structural facts, not approval of row processing, measures, publication, or redistribution.

The requested monthly-security backfill is complete with 71 archives: one December 2024 Core File 1 sample, 48 packages for 2025, and 22 packages for 2026. It verifies a shared 98-column Core FICO/VS4 schema beginning with the December 2025 publication, a new Supplemental File 1 record type `52` beginning in March 2025, December Supplemental width changes, retirement of Files 2 after March 2026, and the consolidated Supplemental File 1 layout from April through August 2026.

## Observed loan-level candidates

Restricted raw storage contains twenty Monthly Loan-Level File 1 (`fu`) packages from January 2025 through August 2026 and fifteen Monthly Loan-Level File 2 (`au`) packages from January 2025 through its March 2026 retirement. The 35 archives total about 9.1 GiB compressed, pass ZIP-integrity and exact-member-name checks, and are approved for restricted local M4 conformance. Both families expose 116 headered columns; December 2025 replaces legacy credit-score/filler positions with Classic FICO and VS4 fields without changing the column count. The same FICO/VS4 header continues through the observed April 2026 consolidation and August endpoint.

## M4 implemented contract

`.project/m4-source-contract.json` and `.project/m4-loan-source-contract.json` now approve provenance, native grains, timing, corrections, keys, fields, types/nulls, sensitivity, retention, and release rules for all six acquired source families. Exact inventory and conformance pass for all 106 archives.

M4 treats supplemental records as provider-native distributions outside `FactSecurityPeriod`/`FactLoanPeriod`: all 419,478,342 are structurally accepted by inventory and explicitly dispositioned as M5-deferred exclusions from these two facts. Core and loan rows produce 9,240,038 security-period and 264,922,553 loan-period facts. Restricted values remain under ignored `local/`; only aggregate reconciliation evidence enters project records.

`scripts/source_inventory.py` inspects checksums, sizes, member names, encryption flags, physical row counts, ordered-header fingerprints, and headerless record layouts without emitting disclosure row values. Its ignored cache skips unchanged adjacent files. `scripts/m4_conformance.py` streams approved rows once into restricted facts and value-free control records.

## M5 derived metric boundary

`.project/m5-metric-catalog.json` resolves 54 complete metric contracts. `scripts/m5_metric_engine.py` reads only approved M4 conformed columns plus the existing governed issuance allowlist. Restricted output stays at `local/m5-metrics.sqlite` and contains additive numerators/denominators, segment components, original/latest security views, candidate gate results, and value-free run evidence.

The engine does not read supplemental row values or any unallowlisted core/loan value. Proposed M4 v2 field additions and exact approval questions are recorded in `.project/m5-approval-request.json`; that file grants no processing authority. Delinquent-loan-purchase fields remain unlocated in approved core/loan headers. Reviewer/public release remains unapproved.
