# 0006 Partition restricted loan facts

## Decision

Store security-period controls and facts in SQLite, keep loan-period facts in compressed period and source partitions, and process metric components with partition-local streaming.

## Why

This design preserves correction lineage and exact reconciliation while avoiding an unnecessary wide SQLite copy of the full loan population.

## Alternatives rejected

One flattened security and loan fact table would mix grains. A wide duplicate staging database would add disk cost without improving current decisions. A cloud warehouse was not approved or justified by measured limits.

## Not done

Supplemental native grains were not forced into security or loan facts. Unapproved M5 fields and formulas were not released.

## Changed

M4 added approved source contracts, immutable manifests, original and latest views, compressed loan partitions, reason-coded joins, and backfill or incremental parity evidence.
