# Decision 0011: Retain current loan partition format

## Decision

Retain the current gzip CSV loan partitions. Do not adopt the compact candidate. Request a revised steady-storage budget before starting the isolated M4 v2 build.

## Why

The standard-library candidate removed only partition-constant report, source, schema, publication, and as-of values while preserving them in an immutable sidecar manifest. Full logical rows were reconstructed for parity checks.

The large File 1 sample decreased from 1,075,182,450 to 1,004,760,584 bytes, a 6.55% saving. Scan time increased from 41.71 to 46.95 seconds, a 12.55% slowdown. The File 2 sample decreased from 11,752,240 to 10,977,497 bytes, a 6.59% saving. Scan time increased from 0.44 to 0.48 seconds, a 9.99% slowdown. Both samples preserved normalized rows and representative current-balance, correction, and join metrics exactly.

The approved gate required at least 20% storage savings and no more than 10% scan slowdown. Savings failed for both samples, and slowdown failed for the large File 1 sample.

## Alternatives rejected

- Adopt the candidate despite the miss. Rejected because it breaks the approved decision rule.
- Add Parquet, DuckDB, or a warehouse. Rejected because no approved benchmark proves a new permanent dependency is needed.
- Remove row identifiers or correction lineage. Rejected because those values are not recoverable partition constants.
- Hide the storage miss by deleting canonical source. Rejected because source retention and recovery remain mandatory.

## Not done

This decision does not revise the 34 GiB budget, start M4 v2, estimate the added v2 field footprint, or delete the current release. Those actions require an owner-approved budget exception and isolated build evidence.

## Changed

- Added a reproducible standard-library partition benchmark with logical-row and representative-metric parity checks.
- Recorded the failed adoption results instead of changing storage format.
- Made revised storage-budget approval the explicit M4 v2 prerequisite.
