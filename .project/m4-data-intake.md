# M4 monthly security and loan data intake

Status: `requested security and loan acquisition complete; M4 contract implementation is next`

This record converts the acquired M4 population into a fail-closed implementation procedure. Row-level local use is authorized; exact machine fields, joins, calculations, and reviewer/public rights still require their documented gates.

## Verified acquisition progress

The owner confirmed authorized row-level Freddie Mac use for the restricted analyst workflow and acquired the requested history for all applicable monthly-security and monthly loan-level families from the authenticated disclosure source. Public redistribution or publication was not authorized.

The owner approved a seven-year retention period from acquisition for restricted raw and security-level derived data, with earlier deletion if authorization ends.

The archives are retained under ignored `data/raw/` storage. Safe structural inspection verified:

| Family | Archive/member | Rows | Structure | Archive SHA-256 |
| --- | --- | ---: | --- | --- |
| Core File 1 | `fd241205.zip` / `fd241205.txt` | 395,068 | Headered; 96 columns; header `d5115758...207f46` | `00071c3d...415fd` |
| Core File 2 | `ar250107.zip` / `ar250107.txt` | 24,539 | Headered; 96 columns; header `60d8e87d...52128` | `013db149...c8c7` |
| Supplemental File 1 | `fq250107.zip` / `fq250107.txt` | 18,948,484 | Headerless multi-record; 30 observed record types | `2947e19d...572f` |
| Supplemental File 2 | `ge250107.zip` / `ge250107.txt` | 1,079,438 | Headerless multi-record; 44 observed record types | `42479676...6267` |

The four samples contain 20,447,529 physical records and zero unknown record types or record-width failures under the observed structural layouts. The supplemental files do not contain a header row; their first field selects a record-specific layout. The intake gate now validates those record-type/column-count contracts without emitting row values.

The initial samples established packaging/layouts; the completed backfill below establishes the requested implementation window. It does not by itself define correction handling or certify M4 fields, joins, or measures.

### 2025 backfill

All 48 required 2025 packages are present: 12 monthly files for each of `fd`, `ar`, `fq`, and `ge`.

The partial backfill verifies three source-layout changes:

- Core Files 1 and 2 use their 96-column legacy layouts through the November 2025 publication and switch to the same 98-column FICO/VS4 layout in December 2025 (`03eb8bde...5a541`).
- Supplemental File 1 adds record type `52` with nine columns in March 2025.
- Supplemental File 1 changes record type `1` from 19 to 21 columns and record type `6` from eight to nine columns in December 2025, aligned to the FICO/VS4 transition.
- Supplemental File 2 changes record type `1` from 19 to 21 columns, record type `6` from eight to nine columns, and record types `32` and `39` from eight to nine columns in December 2025.

The machine contract records separate validity periods for each observed 2025 layout. Record type `35` is present through May and absent from June onward; absence is allowed because supplemental record types are optional within the approved layout set.

### 2026 backfill and consolidation

The requested 2026 backfill is complete through the latest available August publication: eight `fd`, eight `fq`, three `ar`, and three `ge` packages. Together with the 2025 backfill and the December 2024 Core File 1 sample, restricted storage contains 71 monthly-security archives.

Safe structural inspection confirms the documented consolidation boundary:

- Core File 1 and Supplemental File 1 continue from January through August 2026.
- Core File 2 and Supplemental File 2 end with the March 2026 publication.
- From April 2026, Supplemental File 1 contains the consolidated record families formerly split across Files 1 and 2.
- The shared 98-column Core FICO/VS4 layout continues across all observed 2026 Core files.
- The machine contract contains a separate April-through-August 2026 consolidated Supplemental File 1 layout. No raw field values or identifiers were emitted while profiling it.

The acquired monthly-security scope is complete for December 2024 through August 2026 under the selected family/period rules. Corrections/restatements remain a separate policy and acquisition decision.

### Adjacent source-family roadmap

The portal contains additional files, but access authority alone does not make unlike grains safely interchangeable. They are staged by analytical value and contract readiness:

| Source family | Decision | Reason |
| --- | --- | --- |
| Monthly loan-level Files 1/2 (`fu`/`au`) | Acquired: `fu` January 2025–August 2026 and `au` January 2025–March 2026 | Implement next under a distinct loan-period grain, schema, correction, and security-linkage contract. |
| Security correction/restatement packages | Acquire for every covered period in which a correction exists | Required to define original-versus-latest precedence and reproducible as-of reporting before M4 transformation approval. |
| Daily prepayment reports | Defer until monthly factor/loan measures reconcile | Separate daily grain; useful for timing and validation, but it should not define the first monthly metric contract. |
| Daily issuance files | Defer | The governed month-end `FRE_IS` history already answers the current monthly issuance workflow; daily files add intramonth timing rather than missing M4 factor fields. |
| Multiclass, resecuritization, pseudopool, mission, green, or social files | Out of the current product universe | Different products, structures, and joins; add only through an explicit scope milestone so unlike populations are not mixed silently. |

History range and retention are separate controls. The present monthly-security analytical history is the requested recent window used to establish schemas and the 2026 consolidation boundary. Seven-year retention means each acquired restricted file is kept for seven years from acquisition, with earlier deletion if authorization ends; it does not automatically create seven years of historical observations. For robust seasonality and rate-cycle prepayment analysis, extend the analytical history backward after the monthly security and loan-level parsers prove schema-safe; target at least five years and preferably seven years if the official packages and local capacity support it.

The adjacent loan-level window is complete through the applicable August/March 2026 endpoints: twenty `fu` packages covering January 2025–August 2026 and fifteen `au` packages covering January 2025–March 2026, totaling about 9.1 GiB compressed. All 35 ZIPs pass archive-integrity checks and contain exactly named `.txt` members. Header-only inspection found 116 columns throughout, a December 2025 FICO/VS4 semantic transition in both families, and no additional header change at the April 2026 File 1/File 2 consolidation boundary. These files remain outside the M4 security-source contract and are not yet approved for row transformation.

## Verified official source candidates and transition

Freddie Mac's Single-Family Disclosure Guide, version 6.2 effective 2026-04-01 and last updated 2026-04-10, documents the monthly core and supplemental layouts. Freddie Mac's 2026 consolidation notice adds the period rule that must govern a historical backfill:

| Candidate family | Official member convention | Period role | Release timing |
| --- | --- | --- | --- |
| Monthly Security Core File 1 | `fdYYMMDD.txt` | Factors for the File 1 population historically; consolidated MBS population beginning with the 2026-04-06 publication | Fourth business day, 4:30 P.M. |
| Monthly Security Core File 2 | `arYYMMDD.txt` | Historical ARM, modified, and reinstated population; last publication 2026-03-05 | Fourth business day, 4:30 P.M. |
| Monthly Security Supplemental File 1 | `fqYYMMDD.txt` | Pool-level stratifications/quartiles for File 1 historically; consolidated population beginning 2026-04-06 | Fourth business day, 4:30 P.M. |
| Monthly Security Supplemental File 2 | `geYYMMDD.txt` | Historical ARM, modified, and reinstated population; last publication 2026-03-05 | Fourth business day, 4:30 P.M. |
| Security Core Correction File 1 | `FRE_RIS_YYYYMM` | Consolidated security-core corrections beginning 2026-04-06 | As published |
| Security Supplemental Correction File 1 | `FRE_RISS_YYYYMM` | Consolidated supplemental corrections beginning 2026-04-06 | As published |

The consolidation notice says pseudopool and multiclass files were not consolidated. They are outside the candidate M4 scope unless the owner explicitly adds them. Backfill completeness therefore cannot require File 2 after its retirement, and it cannot omit File 2 for earlier periods if the approved analytical population includes those securities.

The official source page states that MBS issuance, monthly disclosures, and supplemental information are available through its MBS data access. Freddie Mac's February 2026 data-usage reminder says data consumers remain subject to their applicable contract and prohibits redistribution of disclosure data or derived products without prior consent or an executed agreement. The owner must determine the applicable terms; website availability and internal authorization are not treated as public-demo permission.

Primary references, accessed 2026-08-09:

- Freddie Mac Single-Family Disclosure Guide: `https://capitalmarkets.freddiemac.com/mbs/docs/disclosure_guide.pdf`
- Freddie Mac 2026 MBS Disclosure File Consolidation Notice: `https://capitalmarkets.freddiemac.com/mbs/docs/f490news.pdf`
- Freddie Mac 2026 Annual Data Usage Reminder: `https://capitalmarkets.freddiemac.com/mbs/docs/f492news.pdf`
- Freddie Mac Securities Data: `https://capitalmarkets.freddiemac.com/mbs/security-data/mbs-disclosure-resources`
- Freddie Mac Data License and Subscriptions: `https://capitalmarkets.freddiemac.com/mbs/info-requests/data-subscriptions`

## Owner approval checklist

Before `.project/m4-source-contract.json` may be changed to `approved`, record:

1. Exact acquired archive and embedded-member conventions for every required source family.
2. Public demo rights remain unapproved. Authorized restricted row-level use and the seven-year/authorization-end deletion boundary are confirmed.
3. Source grain, reporting/effective period, release timing, historical coverage, and the April 2026 File 1/File 2 consolidation boundary.
4. Original and correction/restatement behavior, including `FRE_RIS`/`FRE_RISS` handling and which delivery supersedes another.
5. Primary/business keys and the allowed join from issuance to security-period records.
6. Exact ordered-header fingerprints and validity periods for every observed schema version.
7. Field allowlist with meaning, type, unit, sensitivity, null/sentinel behavior, and public aggregation rule.
8. Intended measures; descriptive source fields enter the M5 catalog, while factor-derived runoff, paydown, SMM/CPR, roll/cure, and concentration formulas remain gated until golden fixtures and domain review pass.
9. Required source families and policy for optional, missing, late, unmatched, terminated, or reissued securities.

## Machine-enforced contract

`scripts/source_inventory.py` reads the JSON contract, scans restricted raw storage without emitting row values, and reports:

- archive checksum and size;
- embedded member name, size, encryption flag, physical row count, ordered-header fingerprint for headered files, and record-type/column-count coverage for headerless multi-record files;
- governed issuance, approved M4, unapproved candidate, invalid, and unrelated classifications;
- missing required families, unrecognized schemas, invalid archives, and contract blockers.

The fail-closed readiness command remains blocked until M4 approves the machine contract and every required family matches. That blocker is an implementation gate, not a missing-file request. Discovery never grants formula or release approval. Run:

```sh
npm run inventory:sources
python3 scripts/source_inventory.py --input data/raw --contract .project/m4-source-contract.json --require-ready
```

The second command intentionally exits with status 2 until the M4 contract is completed and approved.

## No-go rules

- Do not infer runoff or prepayment from the current issuance-only fields.
- Do not copy row values, security identifiers, CUSIPs, seller/servicer values, or restricted fields into Git, logs, evidence, or public payloads.
- Do not accept a schema from a filename alone.
- Do not hide a many-to-many join, correction, restatement, missing family, or unmatched security.
- Do not substitute a synthetic reviewer dataset for the missing authorized files.
