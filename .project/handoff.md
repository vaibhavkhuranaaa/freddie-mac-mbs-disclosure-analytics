# Handoff

## Outcome

M5 safe supported work is complete. The machine catalog contains 54 formula-version `m5.1.0` contracts: 23 supported/implemented, 17 methodology-gated, 11 field-contract extensions, and 3 external. No gated, extended, or external contract is released.

The restricted local engine processed all 35 compressed loan partitions and 264,922,553 rows plus both 9,240,038-row security correction views. It emits 256,461 released components and 240 explicitly unreleased candidates. The independent verifier passes 684 segment, weighted-component, and top-N/Other parity checks plus 240 candidate-formula checks. Measured peak RSS is 32,538,624 bytes. Full and unchanged incremental outputs share SHA-256 `54e128d0590f8e7c4ed1396c0d3626cb56b08390b670d10a5fbf184b15ed6341`.

M5 acceptance is blocked by genuinely external owner/domain input. M6 has not started.

## Current blockers

1. Approve, reject, or revise the exact proposed fields in `.project/m5-approval-request.json`. Until approval and exact guide code/null/range fixtures are recorded in versioned M4 contracts, the engine must not read those row values.
2. Approve methodology gates by technical name and formula version. Ending-balance bridge, runoff/paydown, SMM/CPR, cohort speed, burnout, principal categories, PSA, involuntary-removal share, delinquency threshold/transition metrics, modification rate, composite quality/comparability, and HHI remain unreleased.
3. Identify provider-supported source fields for loan origination/vintage timing and delinquent-loan purchases. Neither input was located in the approved current core/loan header contracts, so the approval request does not invent a field.
4. Cohort/vintage real-population reconciliation remains blocked until the proposed security issue date is approved and an exact loan origination/vintage source is identified. Structured golden blocker fixtures pass without reading real unallowlisted values.

Do not mark M5 complete or begin M6 until applicable approval entries change in `.project/approvals.yml` and every newly approved field/formula passes golden and real reconciliation.

## First unblocked action after approval

Amend only the approved M4 field contracts, add exact source-guide code/null/range rules and non-sensitive fixtures, then extend M4 partitions narrowly enough to expose those fields. Re-run M4 parity and safety before adding any newly supported M5 component. If only methodology gates are approved, implement/release only those named gates whose existing fields and fixtures are already sufficient.

## Recovery commands

```sh
npm run check
npm run inventory:sources
npm run verify:m4
npm run verify:m5
```

Expected M5 result:

- 54 catalog contracts; 23 released supported contracts.
- 35 loan partitions; 264,922,553 loan rows; 9,240,038 security rows.
- 684 released-component parity checks and 240 candidate-formula checks.
- Checksum `54e128d0590f8e7c4ed1396c0d3626cb56b08390b670d10a5fbf184b15ed6341`.

Restricted data remains ignored under `data/raw/` and `local/`. Reviewer/public redistribution, cloud, AI, paid services, deployment, and publication remain unapproved. The repository has no configured remote; GitHub authentication was invalid at last verification.

Use `docs/NEXT_CHAT_PROMPT.md` only after recording owner/domain decisions.
