# Data contract

Status: `approved authorized issuance baseline; new source families require separate approval`

## Rights and release boundary

- The project owner confirmed authorized Freddie Mac source-file use on 2026-08-01.
- Official source ZIPs remain under ignored `data/raw/` storage and are never committed or included in a public artifact.
- The reviewer-facing application receives monthly aggregates and safe quality/provenance metadata only.
- Security identifiers, CUSIPs, seller/servicer attributes, descriptions, and security-level rows are restricted to the authorized local workflow.
- Monthly factor and supplemental files are not yet acquired or approved under this contract.

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
- `Prefix` — current security-type label; aggregate taxonomy use awaits M3 approval.
- `Issuance Investor Security UPB` — issuance balance measure.
- `Current Investor Security UPB` — retained for source reconciliation; not interpreted as subsequent runoff in issuance files.
- `Security Factor` — retained for validation; issuance-date factor is not presented as performance analytics.
- `Security Data Correction Indicator` — correction count.
- `Security Status Indicator` — used only to classify the documented status-`C` blank-balance exclusion.

All other source columns are ignored by the current transformation and remain restricted.

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

- Raw files and the detailed SQLite database remain local/restricted until an approved cloud data-retention and identity decision exists.
- Public payloads contain no security identifiers or security-level rows.
- Quality event details contain rule descriptions and row numbers, not raw values.
- The project performs portfolio/security analytics and does not use borrower-level decisioning.

## New-source gate

Before M4 begins, every factor or supplemental source must record provenance, license/demo rights, grain, timing, correction behavior, keys, field allowlist, sensitivity, retention, and public aggregation rules.
