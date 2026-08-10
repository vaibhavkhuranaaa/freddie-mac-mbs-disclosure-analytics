# Handoff

## Outcome

M4 is complete. Approved security and loan contracts govern all 106 acquired archives. Real backfill reconciles 693,640,933 physical records to 274,162,591 accepted/published facts and 419,478,342 explicit supplemental exclusions, with zero rejected, duplicate, or quarantined rows. All 264,922,553 loan/security joins match. Backfill and unchanged incremental snapshots share SHA-256 `ec3862e9f6c1f4531424a26e4d3934b12b4e690ebb14fe58e8fd343c81074528`.

Restricted control/security facts and 35 compressed loan partitions remain ignored under `local/`. Reviewer/public redistribution remains unapproved.

## M5 implementation order

1. Read project records and query refreshed Graphify.
2. Define complete metric contracts before implementing each M5 formula.
3. Reuse conformed M4 facts; do not reopen raw archives unless a source-contract defect requires it.
4. Keep Classic FICO, VS4, and legacy score systems separate.
5. Keep runoff/paydown, SMM/CPR, roll/cure, and HHI unreleased until their explicit formula fixtures and domain gates pass.
6. Reconcile every metric numerator/denominator across security, loan, cohort, segment, and portfolio grains.

Do not implement M5 formulas inside M4 except the reconciliation measures required to prove conformance. Do not treat Classic FICO and VS4 as one score, April consolidation as an economic event, total balance decline as prepayment, or source discovery as public-release permission.

## Recovery commands

```sh
npm run check
npm run inventory:sources
npm run verify:m4
```

All three commands are expected to pass without rereading unchanged raw archives beyond safe inventory metadata checks.

## External blockers

- GitHub cannot be updated until `gh auth login -h github.com` succeeds and a target repository/remote is selected.
- Cloud, AI, paid resources, deployment, and publication require the approvals recorded in `.project/approvals.yml`.
