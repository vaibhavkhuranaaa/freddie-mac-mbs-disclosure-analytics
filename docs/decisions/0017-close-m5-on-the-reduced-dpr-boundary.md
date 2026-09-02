# 0017 - Close M5 on the reduced DPR boundary

Status: accepted
Date: 2026-08-25
Approval: `M5-REDUCED-DPR-BOUNDARY-2026-08-25`

## Decision

Close M5 without acquiring the Freddie Mac Daily Prepayment Report. Keep every DPR-dependent or otherwise source-gated contract unreleased. Do not derive voluntary principal reduction, SMM, CPR, cohort prepayment speed, or PSA from monthly security factors or loan attrition.

M5.8 is satisfied by the owner-approved reduced boundary. M5.9 is resolved by explicit deferral rather than a synthetic or relabeled implementation. M5.10 closes after the active M4/M5 release, storage, repository, and delivery records pass final verification.

## Why

The active disclosure sources fully support 38 catalog contracts, including field-backed measures and loan-history transitions. They do not identify the provider-native DPR cohort inputs needed for voluntary prepayment measures. Closing on a precise reduced boundary preserves all verified value without weakening source, grain, or formula rules.

## Alternatives rejected

- Infer prepayment from monthly factor decline: rejected because factor movement does not separate scheduled principal, curtailments, voluntary payoff, and involuntary removal.
- Treat disappearing loans as voluntary payoff: rejected because attrition has no provider-supported cause.
- Create placeholder DPR tables or formulas: rejected because they would add code without governed source evidence.
- Leave M5 open indefinitely: rejected because all selected-boundary measures are implemented and verified.

## Not done

This decision does not release the 11 methodology-gated contracts, the 2 field-contract extensions, or the 3 external-data contracts. It does not add Power BI, deployment, or publication. DPR-backed work may return only as a later approved source extension.

## Changed

M5.8 and M5.9 are closed by explicit deferral. M5.10 verifies the immutable `m5-7-history-20260825` release, 38 supported contracts, one active release, zero temporary or rollback files, and 45,675,380,656 stable bytes under the approved 46,170,898,432-byte ceiling. M6 becomes active.
