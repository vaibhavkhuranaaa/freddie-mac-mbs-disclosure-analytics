# 0009 Enforce the external storage boundary

## Decision

Resolve restricted paths from absolute `MBS_DATA_ROOT`, defaulting to a sibling data directory outside the product repository. Keep one checksummed canonical raw archive set, one active issuance/M4/M5 release, isolated future builds, and one value-free recovery ledger.

Fail before writing when the data root overlaps the repository or free space is below the current release estimate plus 10 GiB. Final storage checks reject repository analytical files, canonical duplicates, multiple active releases, build residue, abandoned temporary files, or missing ledger coverage.

## Why

Repository ignore rules prevent commits but do not create a storage or recovery boundary. Explicit paths, checksum parity, producer and consumer records, retention rules, and cleanup actions make cutover and recovery deterministic.

## Alternatives rejected

Environment-only paths without a safe default would make routine commands fragile. Keeping data under ignored repository folders would preserve accidental coupling. Adding a storage service or new analytical dependency would exceed current need and approval.

## Not done

This change does not compact the M4 loan partitions, change metric contracts, provision backup infrastructure, or approve cloud processing. The 34 GiB steady target remains assigned to the measured compact-partition decision before M4 v2.

## Changed

Inventory, issuance, M4, M5, verification, safety, and package commands now share the external storage resolver. Checksum migration and cleanup are recorded in the private value-free recovery ledger.
