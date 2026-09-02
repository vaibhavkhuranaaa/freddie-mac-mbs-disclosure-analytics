# ADR 0012: Fingerprinted M4 v2 release bundles

## Status

Accepted on 2026-08-24.

## Decision

M4 v2 is a rebuild-only migration. Every source manifest carries one composite build fingerprint covering both source contracts, the M4 parser, the field-rule engine, the official prefix row-class contract, the SQLite schema, and the ordered gzip partition format. Incremental reuse is allowed only when that fingerprint, the archive checksum, and the partition checksum all match.

The active M4, loan partitions, issuance database, and M5 database form one immutable release bundle. A complete bundle is built and verified under `MBS_DATA_ROOT/build/<run-id>`, moved into `MBS_DATA_ROOT/releases/<release-id>`, and activated by atomically replacing one value-only release pointer. Active verification is read-only. M5 records the M4 build fingerprint and fails verification when the two releases differ.

Provider applicability uses the exact prefix taxonomy in Freddie Mac's official Prefix Library. Negative rules for ARM current rates and modified/reperforming LTV, CLTV, occupancy, and channel fields fail closed. A compact ordered status string preserves valid, blank, not-available, and not-applicable meanings without adding one status column per field.

## Why

Source checksums alone cannot detect stale output after parser, contract, rule, or schema changes. One fingerprinted immutable bundle makes reuse deterministic and prevents readers from observing a partially replaced release.

## Alternatives rejected

- In-place database and partition replacement: failure can leave mixed release generations.
- Archive-checksum-only reuse: unchanged inputs can require different outputs after code or contract changes.
- Per-file active pointers: readers could resolve inconsistent M4, loan, issuance, and M5 versions.

## Not done

This decision does not authorize rollback deletion, field-extension metric release, deployment, or publication. Each remains separately gated.

## Changed

M4 manifests now carry the composite build fingerprint, complete releases are promoted through one atomic pointer, and verification rejects stale or cross-generation M4/M5 state.

## Consequences

- Unchanged source archives cannot make stale v1 outputs appear current.
- Failed builds cannot alter the active release.
- Readers see either the complete prior bundle or the complete promoted bundle.
- Any parser, rule, contract, schema, or partition-format change requires a deterministic rebuild.
- The legacy v1 directory is moved into a named rollback location only after the promoted v2 bundle passes active read-only verification. Its later removal is a separate, explicit cleanup action after the cutover evidence is accepted.
