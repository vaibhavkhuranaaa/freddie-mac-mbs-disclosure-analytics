# 0014 — Approve fail-closed M5 methodology

Status: accepted
Date: 2026-08-25
Approval: `M5.5-EXACT-METHODOLOGY-2026-08-25`

## Decision

Use methodology contract `m5-exact-methodology-v1` and formula version `m5.2.0`.

- Comparability is `fail` when a required component is missing or invalid, `warn` when all components are valid but fewer than 30 observations qualify, and `pass` otherwise. No composite quality score or component weights are published.
- Loan transitions use `(source_family, loan_id, security_id)`, adjacent reporting months, and both original and latest correction views. Attrition is explicit and remains in the beginning-cohort denominator.
- Cure means 30-plus delinquent to current; new delinquency means current to 30-plus delinquent. Redefault is observed for 12 months after cure and is right-censored when the window is incomplete.
- PSA remains deferred. No convention is inferred without a contracted Daily Prepayment Report source.

The rules are release-mode neutral and fail closed. They authorize deterministic implementation and testing; they do not by themselves release the gated measures.

## Why

These choices make every comparison and transition outcome reproducible while keeping missing population, attrition, corrections, and incomplete observation windows visible. They avoid false precision from an arbitrary quality score and avoid survivor-only bias.

## Alternatives rejected

- Weighted composite quality score: rejected because no defensible weights are evidenced.
- Survivor-only transition denominators: rejected because disappearing loans would silently improve rates.
- Inferred PSA convention: rejected because the required provider-native cohort source is not yet contracted.

## Not done

No gated comparison, transition, redefault, or PSA measure is released by this decision. Field-extension and transition implementation remain M5.6 and M5.7 work; DPR acquisition or reduced scope remains M5.8 work.

## Changed

The machine catalog now contains the approved exact methodology contract and formula version. Golden fixtures and catalog validation enforce the parameters, and immutable release `m5-5-methodology-20260825` records the resulting catalog fingerprint.

## Consequences

M5.6 may implement the approved field-extension measures. M5.7 may implement loan-history transitions against this exact contract. M5.8 still requires authorized Daily Prepayment Report files or an explicit reduced-scope decision.
