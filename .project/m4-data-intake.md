# M4 factor and supplemental data intake

Status: `pending owner file acquisition and data-contract approval`

This record converts the M4 dependency into a fail-closed intake procedure. It does not approve a source, field, calculation, public claim, or distribution right.

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
2. Authorized-use basis, reviewer/public demo rights, retention, and deletion boundary.
3. Source grain, reporting/effective period, release timing, historical coverage, and the April 2026 File 1/File 2 consolidation boundary.
4. Original and correction/restatement behavior, including `FRE_RIS`/`FRE_RISS` handling and which delivery supersedes another.
5. Primary/business keys and the allowed join from issuance to security-period records.
6. Exact ordered-header fingerprints and validity periods for every observed schema version.
7. Field allowlist with meaning, type, unit, sensitivity, null/sentinel behavior, and public aggregation rule.
8. Intended measures; factor, balance, runoff, paydown, and prepayment remain unapproved until M5 formulas receive domain review.
9. Required source families and policy for optional, missing, late, unmatched, terminated, or reissued securities.

## Machine-enforced contract

`scripts/source_inventory.py` reads the JSON contract, scans restricted raw storage without emitting row values, and reports:

- archive checksum and size;
- embedded member name, size, encryption flag, physical row count, column count, and ordered-header fingerprint;
- governed issuance, approved M4, unapproved candidate, invalid, and unrelated classifications;
- missing required families, unrecognized schemas, invalid archives, and contract blockers.

Readiness remains blocked unless the contract is approved and every required family has at least one archive/member/schema match. Discovery never grants approval. Run:

```sh
npm run inventory:sources
python3 scripts/source_inventory.py --input data/raw --contract .project/m4-source-contract.json --require-ready
```

The second command intentionally exits with status 2 while M4 dependencies remain unsatisfied.

## No-go rules

- Do not infer runoff or prepayment from the current issuance-only fields.
- Do not copy row values, security identifiers, CUSIPs, seller/servicer values, or restricted fields into Git, logs, evidence, or public payloads.
- Do not accept a schema from a filename alone.
- Do not hide a many-to-many join, correction, restatement, missing family, or unmatched security.
- Do not substitute a synthetic reviewer dataset for the missing authorized files.
