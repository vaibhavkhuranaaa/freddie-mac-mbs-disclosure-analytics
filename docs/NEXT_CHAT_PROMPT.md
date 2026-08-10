# Next-chat kickoff prompt

Use this only after the owner/domain reviewer records decisions for `.project/m5-approval-request.json`:

```text
Continue the Freddie Mac MBS Disclosure Intelligence project in:
/Users/vaibhavkhurana/Development/repos/Analytics/freddie-mac-mbs-disclosure-analytics

Read AGENTS.md, PROJECT.md, DESIGN.md, .project/milestones.yml, .project/approvals.yml, .project/state.md, .project/handoff.md, .project/m5-metric-catalog.json, .project/m5-approval-request.json, scripts/m5_metric_engine.py, scripts/verify_m5_metrics.py, tests/test_m5_metric_engine.py, and graphify-out/GRAPH_REPORT.md. Query Graphify first.

M5 supported engine evidence:
- 54 formula-version m5.1.0 contracts: 23 supported/implemented, 17 methodology-gated, 11 field-contract extensions, 3 external.
- 35/35 loan partitions and 264,922,553 rows; both 9,240,038-row security views.
- 256,461 released components, 240 unreleased candidates, 684 released-component parity checks, 240 candidate-formula checks, 32,538,624-byte peak RSS.
- Full/incremental SHA-256 54e128d0590f8e7c4ed1396c0d3626cb56b08390b670d10a5fbf184b15ed6341.
- No gated, extended, or external contract is released. M6 has not started.

Apply only approvals explicitly recorded in .project/approvals.yml:
1. For approved field extensions, add exact provider code/null/sentinel/range/schema rules and non-sensitive fixtures to a new M4 contract version before reading real values. Extend only the required conformed fields; do not rescan supplemental families unless their exact native-grain contract is approved.
2. Re-run M4 backfill/incremental parity, row/join reconciliation, and restricted-output safety after any contract change.
3. Implement only named methodology gates whose formula version, timing, denominator, correction treatment, edge cases, and fixtures were approved.
4. Re-run the full M5 real reconciliation and unchanged incremental parity. Keep total balance decline distinct from voluntary prepayment and keep legacy credit score, Classic FICO, and VS4 separate.
5. Update evidence/state/handoff/Graphify and close M5 only if every acceptance criterion passes. Do not begin M6 while any required M5 gate remains unresolved.

Do not provision cloud resources, use paid services, deploy, publish, add AI, create reviewer/public outputs, or infer approval beyond the recorded technical names/fields.
```
