# Methodology

## Current governed data flow

1. The authorized project owner places official `FRE_IS_YYYYMM.zip` files under ignored `data/raw/` storage.
2. The pipeline requires exactly one matching `FRE_IS_YYYYMM.txt` member.
3. The ordered header must match a reviewed schema fingerprint and the schema must be valid for the report period.
4. Each row is classified as accepted, documented exclusion, rejected, or duplicate.
5. Accepted records, the source manifest, and value-free quality events are stored in local SQLite.
6. Publication is blocked unless every source passes and physical input reconciles exactly.
7. The pipeline writes monthly aggregate JSON with safe period, build, schema, pipeline, and quality metadata.
8. The browser renders issuance trends and monthly evidence from that aggregate-only payload.

Before a new factor or supplemental parser is allowed, the M4 source inventory hashes the archive and records value-free package/header metadata. It remains blocked until the machine-readable contract is approved and every required family matches an exact archive/member convention and schema fingerprint. It does not emit disclosure row values and does not infer authorization from file discovery.

## Population rule

Accepted issuance observations require a security identifier, Prefix, positive issuance UPB, non-negative current UPB not exceeding issuance UPB, factor in `(0,1]`, and a valid correction flag. The business key is `(report_month, security_id)`.

A status-`C` row with issuance UPB, current UPB, and factor all blank is a documented informational exclusion. Any other incomplete balance combination is a rejected row and blocks publication. Duplicate business keys also block publication.

## Current measures

- Issuance UPB
- Issued-security count
- Issuance-file correction count
- Source and period coverage
- Input, accepted, excluded, rejected, duplicate, quarantined, and published counts
- Monthly issuance UPB and security-count mix by approved official UMBS term family, with all unsupported prefixes explicit

## Interpretation

The dashboard describes observed issuance activity. A peak, trough, schema change, exclusion change, or composition shift is a prompt for source/comparability and operational investigation—not a causal conclusion or investment signal.

## Mix method

The aggregate layer uses Freddie Mac's Prefix Library Summary for CL/ZL (30-year), CT/ZT (20-year), CI/ZI (15-year), and CN/ZN (10-year) term families. All other codes are grouped as `Other / Unmapped prefix`. Monthly group counts, UPB, and UPB shares reconcile exactly to the monthly issuance totals.

## Scope boundary

Issuance-date factor and current UPB do not provide longitudinal runoff or prepayment analytics. Those measures begin only after approved monthly factor and supplemental sources have documented keys, timing, formulas, tests, and limitations. The intake/readiness mechanism exists, but the contract and source files remain absent.
