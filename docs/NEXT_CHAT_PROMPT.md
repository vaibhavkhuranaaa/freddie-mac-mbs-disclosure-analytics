# Next-chat kickoff prompt

Copy and paste this into a new chat:

```text
Continue the Freddie Mac MBS Disclosure Intelligence project in:
/Users/vaibhavkhurana/Development/repos/Analytics/freddie-mac-mbs-disclosure-analytics

Work in goal mode and complete M4 end to end. Read AGENTS.md, PROJECT.md, DESIGN.md, README.md, docs/BI_PRODUCT_SPEC.md, .project/architecture.md, .project/refinement-plan.md, .project/milestones.yml, .project/data.md, .project/evaluation.md, .project/evidence.yml, .project/approvals.yml, .project/state.md, .project/handoff.md, .project/m4-data-intake.md, .project/m4-source-contract.json, and graphify-out/GRAPH_REPORT.md before editing. Query Graphify first. Use Caveman for concise updates and Ponytail where it prevents unnecessary complexity.

Context and authority:
- I am authorized to use the acquired Freddie Mac data at row level for this local analyst product; do not restrict the authorized model to aggregates.
- Retain restricted raw and derived data for seven years from acquisition and delete earlier if authorization ends.
- The requested inputs are already under ignored data/raw/: 71 monthly-security fd/fq/ar/ge archives and 35 monthly loan-level fu/au archives.
- Reviewer/public redistribution is not approved. Keep raw/detail values out of Git, logs, screenshots, public artifacts, prompts, and traces.
- Do not provision cloud resources, use paid services, deploy, publish, or add AI without the approvals in .project/approvals.yml.

Implement M4 only:
1. Finalize and approve the machine-readable monthly-security contract and add the loan-level contract: exact archive/member patterns, schema validity windows, field allowlists, native grains, types/null rules, keys, correction precedence, original/latest views, sensitivity, retention, and authorized/reviewer boundaries.
2. Add small non-sensitive golden fixtures for legacy versus FICO/VS4 schemas, the April 2026 consolidation, corrections, duplicates, missing periods, malformed layouts, and unmatched/ambiguous joins.
3. Implement fail-closed restricted staging, manifests, row dispositions, correction/restatement lineage, and conformed FactSecurityPeriod and FactLoanPeriod outputs at native grain.
4. Implement reason-coded security/loan joins: matched, unmatched, ambiguous, late, ineligible, and terminated. Reconcile every source period/family and never silently drop or double-count records.
5. Prove historical-backfill versus incremental parity, idempotence, original/latest as-of behavior, and restricted-output safety. Optimize large-file processing without reading adjacent files more than necessary.
6. Do not implement M5 business formulas beyond conformance/reconciliation measures. Do not combine Classic FICO and VS4, treat the April consolidation as economic activity, or call total balance decline prepayment.
7. Run all declared checks against the real local inventory, refresh Graphify, update every affected project record/evidence/state/handoff, remove any superseded artifact rather than archiving it, commit with a conventional human-authored message, and push/open a draft PR only if an authenticated remote exists.

Continue autonomously until M4 acceptance criteria pass or a genuinely external approval/input blocker remains. Report exact row/source/join reconciliation evidence and the first unblocked next milestone.
```
