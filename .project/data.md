# Data contract

Status: `authorized row-level local use and retention approved; M4 transformation contract is next`

## Rights and release boundary

- The project owner confirmed authorized Freddie Mac source-file use on 2026-08-01.
- Official source ZIPs remain under ignored `data/raw/` storage and are never committed or included in a public artifact.
- The reviewer-facing application receives monthly aggregates and safe quality/provenance metadata only.
- Security identifiers, CUSIPs, seller/servicer attributes, descriptions, and security-level rows are restricted to the authorized local workflow.
- The requested `fd`, `ar`, `fq`, and `ge` monthly-security history is acquired under restricted raw storage: all 48 packages for 2025, plus 22 packages through the applicable August/March 2026 family endpoints and one December 2024 Core File 1 sample.
- The requested `fu` and `au` monthly loan-level history is also acquired. The owner authorizes local row-level use; M4 must machine-version exact fields, schemas, joins, corrections, and release modes before transformation output is treated as governed.

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

Restricted raw storage contains twenty Monthly Loan-Level File 1 (`fu`) packages from January 2025 through August 2026 and fifteen Monthly Loan-Level File 2 (`au`) packages from January 2025 through its March 2026 retirement. The 35 archives total about 9.1 GiB compressed, pass ZIP-integrity and exact-member-name checks, and remain outside approved transformation scope. Both families expose 116 headered columns; December 2025 replaces legacy credit-score/filler positions with Classic FICO and VS4 fields without changing the column count. The same FICO/VS4 header continues through the observed April 2026 consolidation and August endpoint.

## M4 implementation gate

M4 begins by recording provenance, rights/release boundary, native grain, timing, correction behavior, keys, field allowlist, sensitivity, retention, and authorized/reviewer rules for every security and loan family. `.project/m4-source-contract.json` is the current monthly-security machine boundary; M4 adds the corresponding loan contract and approves both before governed transformation output is released. `.project/m4-data-intake.md` records the verified acquisition and schema evidence.

`scripts/source_inventory.py` may inspect archive checksums, sizes, member names, encryption flags, physical row counts, ordered-header fingerprints, and headerless record-type/column-count distributions. It must not emit disclosure row values. A discovered file remains an unapproved candidate unless it matches an approved family, member convention, schema/layout version, validity period, and required-family contract.
