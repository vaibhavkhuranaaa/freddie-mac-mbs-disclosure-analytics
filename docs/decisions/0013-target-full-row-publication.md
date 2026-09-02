# ADR 0013: Target full-row publication

## Status

Accepted on 2026-08-25.

## Decision

The target publication contains complete row-level source and derived data with provenance, corrections, quality states, metric definitions, and limitations.

Methodology, conformance, and verification remain identical across development and publication. Data stays in governed external storage until the publication phase.

## Preconditions

Publication requires product acceptance, integrity checks, and an owner-recorded rights position. The owner attests that no additional redistribution rights are required for M12. Downstream users remain responsible for reviewing applicable provider terms.

## Consequences

- Public architecture targets full row-level access.
- Publication tests must cover provenance, correction lineage, completeness, and source fidelity for every row.
- No data is pushed or published before the publication gate and distribution-rights evidence pass.
- Privacy safeguards still prohibit re-identification or correlation to individuals.
