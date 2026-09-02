# 0016 - Use temporary disk-backed loan history

Status: accepted
Date: 2026-08-25
Approval: `M5.5-EXACT-METHODOLOGY-2026-08-25`

## Decision

Implement M5.7 with one temporary SQLite workspace holding current and prior loan-identity slices plus open redefault cohorts. Use `(source_family, loan_id, security_id)` identity, resolve original and latest source precedence independently, keep attrition in beginning denominators, and right-censor incomplete 12-month redefault windows. Persist only compact transition components in the immutable M5 release.

A modification cohort begins only when the history observes a blank-to-disclosed modification-program transition. No earlier modification date is inferred.

## Why

Adjacent-state and 12-month cohort measures cannot be calculated safely from independent partition totals. A disk-backed stage preserves exact identity and ordering while keeping memory bounded and avoiding a second durable copy of 264,922,553 loan rows.

## Alternatives rejected

- In-memory identity maps: rejected because the full population exceeds the approved memory target.
- A permanent loan-history database: rejected because it duplicates governed facts and exceeds stable storage needs.
- Cross-family identity continuity: rejected because the approved methodology includes source family in the key.
- Survivor-only denominators: rejected because disappearing or ineligible destinations would bias transition rates.
- Inferred historical modification dates: rejected because the source exposes status, not an authoritative event timestamp.

## Not done

This decision does not implement balance bridges, SMM, CPR, PSA, freshness, delinquent-loan purchases, external market measures, Power BI, deployment, or publication. DPR-backed measures still require authorized source files or an approved reduced boundary.

## Changed

The catalog now has 38 supported contracts. Immutable release `m5-7-history-20260825` adds 1,052 transition components after scanning 264,922,553 loan rows. Independent verification passes 1,816 parity checks and 1,068 formula checks with zero candidate components. Peak RSS is 48,447,488 bytes; the temporary history workspace peaks at 5,817,237,504 bytes and is removed before promotion.
