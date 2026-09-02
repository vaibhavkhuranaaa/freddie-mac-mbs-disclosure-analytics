# 0015 - Release nine M4 v2 field metric families

Status: accepted
Date: 2026-08-25

## Decision

Promote nine field-backed contracts at formula version `m5.3.0`: weighted rates, assistance/resolution share, guarantee/MI share, LTV/CLTV/ELTV, DTI, loan/property composition, first-time-homebuyer share, mission metrics, and green/social/special eligibility.

Use one bounded-memory pass over existing loan partitions. Keep security and loan grains separate, retain missing values as visible category members, keep LTV contexts separate, and preserve provider mission values as exact-value distributions rather than inventing an aggregate score. Consumer LTV bands remain a later semantic-model choice.

Keep freshness/release lag gated until immutable acquisition events exist. Keep delinquent-loan purchases unavailable until a provider source isolates that event.

## Why

All nine promoted families now have populated M4 v2 fields, executable provider semantics, deterministic formulas, safe fixtures, full-population reconciliation, and correction handling. Exact-value distributions preserve information without adding unevidenced thresholds or averaging provider scores whose aggregation is undefined.

## Alternatives rejected

- Infer historical acquisition timestamps from publication dates: those timestamps describe different events.
- Relabel broad involuntary removals as delinquent-loan purchases: provider categories are broader.
- Average mission scores across securities: provider aggregation is not defined.
- Choose LTV bands inside M5: no approved consumer-band contract exists yet.
- Combine security and loan series: native grains and weighting contexts differ.

## Not done

This decision does not release freshness, delinquent-loan purchases, transition/history metrics, DPR-backed prepayment metrics, Power BI, deployment, or publication.

## Changed

The catalog now has 36 supported contracts and two remaining field extensions. M5 emits 1,039,079 released components from 264,922,553 loan rows and both security correction views. Immutable release `m5-6-fields-20260825` records the result.
