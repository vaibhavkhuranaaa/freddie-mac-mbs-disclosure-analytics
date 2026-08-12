# 0002 Use official local issuance data

## Decision

Use owner-authorized Freddie Mac issuance archives as the reviewer-facing baseline and process them locally into restricted facts plus an aggregate dashboard payload.

## Why

Official files provide real schema transitions, corrections, exclusions, and lineage needed for credible disclosure analytics.

## Alternatives rejected

Synthetic or aggregate substitute data would not evidence real package, schema, row, duplicate, correction, or reconciliation behavior.

## Not done

Raw archives and row-level facts were not added to Git or approved for redistribution.

## Changed

M0 established a reproducible real-data baseline with official files, local SQLite storage, and governed monthly aggregates.
