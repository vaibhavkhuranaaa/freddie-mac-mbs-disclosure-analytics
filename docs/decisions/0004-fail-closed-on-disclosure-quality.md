# 0004 Fail closed on disclosure quality

## Decision

Require exact package, member, ordered-header, schema-period, value, duplicate, and reconciliation controls before publication.

## Why

Disclosure metrics are usable only when every physical row has a documented disposition and published totals trace to accepted source records.

## Alternatives rejected

Best-effort loading and warning-only schema handling were rejected because they can publish partial or incomparable results.

## Not done

Unknown or malformed data is not coerced into an accepted schema.

## Changed

M2 added versioned source rules, explicit dispositions, reproducible lineage, and an all-pass publication gate.
