# Handoff

## Outcome

The repository now defines one implementation-ready BI product rather than separate stale prototype plans. `docs/BI_PRODUCT_SPEC.md` is the canonical product/metric/visual/semantic-model contract, `.project/refinement-plan.md` explains the delivery rationale, and `.project/milestones.yml` defines M0–M12 acceptance gates.

M0–M3 remain verified. The next milestone is M4: implement approved, fail-closed conformed monthly-security and loan-level inputs using the already acquired 71 security and 35 loan archives. Row-level local use and seven-year retention are approved. Reviewer/public redistribution is not approved.

## M4 implementation order

1. Read the required project records and query Graphify before editing.
2. Update `.project/m4-source-contract.json` and create a loan-level machine contract with exact schema validity, fields, keys, correction precedence, sensitivity, and release modes.
3. Add golden fixtures for the legacy/FICO-VS4 transitions, April 2026 consolidation, corrections, duplicates, missing periods, and unmatched joins.
4. Implement restricted staging, immutable manifests, dispositions, and correction lineage.
5. Build native-grain conformed `FactSecurityPeriod` and `FactLoanPeriod` outputs with original/latest views and reason-coded joins.
6. Prove source, row, join, backfill, incremental, restricted-output, and idempotence gates.
7. Update data dictionary, architecture, evaluation, evidence, state, handoff, and Graphify from verified results.

Do not implement M5 formulas inside M4 except the reconciliation measures required to prove conformance. Do not treat Classic FICO and VS4 as one score, April consolidation as an economic event, total balance decline as prepayment, or source discovery as public-release permission.

## Recovery commands

```sh
npm run check
npm run inventory:sources
python3 scripts/source_inventory.py --input data/raw --contract .project/m4-source-contract.json --require-ready
```

The final command is expected to remain blocked until the M4 machine contract is approved during implementation.

## External blockers

- GitHub cannot be updated until `gh auth login -h github.com` succeeds and a target repository/remote is selected.
- Cloud, AI, paid resources, deployment, and publication require the approvals recorded in `.project/approvals.yml`.
