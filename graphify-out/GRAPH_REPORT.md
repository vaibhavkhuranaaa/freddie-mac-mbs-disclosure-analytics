# Graph Report - freddie-mac-mbs-disclosure-analytics  (2026-08-09)

## Corpus Check
- 38 files · ~24,786 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 279 nodes · 437 edges · 33 communities (20 shown, 13 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `29db1f0c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- project_kit.py
- app.js
- scripts
- pipeline.py
- Handoff
- validate_dashboard.mjs
- PipelineTests
- Issuance Monitoring Scope
- Issuance Monitoring Business Question
- Recruiter-Facing Issuance Dashboard
- Issuance Monitoring Methodology
- Next Chat Continuation Prompt
- Verified Project Evidence
- End-to-end product refinement plan
- source_inventory.py
- 6. Milestone-by-milestone delivery plan
- test_source_inventory.py
- Data contract
- Evaluation contract
- Metric glossary
- Freddie Mac MBS Disclosure Intelligence
- Deployment decision record
- Restricted local tables
- M4 factor and supplemental data intake
- Project delivery rules
- main
- CLAUDE.md
- DESIGN.md
- category.md
- industry.md
- copilot-instructions.md
- publication.md
- state.md

## God Nodes (most connected - your core abstractions)
1. `PipelineTests` - 13 edges
2. `6. Milestone-by-milestone delivery plan` - 12 edges
3. `scripts` - 11 edges
4. `PipelineError` - 11 edges
5. `SourceBatch` - 11 edges
6. `End-to-end product refinement plan` - 10 edges
7. `render()` - 9 edges
8. `parse_official_zip()` - 9 edges
9. `load()` - 9 edges
10. `bootstrap()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Hiring Manager Review and Remediation Plan` --semantically_similar_to--> `M2 Source Quality and Provenance`  [INFERRED] [semantically similar]
  docs/HIRING_MANAGER_REVIEW.md → .project/milestones.yml
- `Freddie Mac MBS Issuance Monitoring Overview` --references--> `Hiring Manager Review and Remediation Plan`  [EXTRACTED]
  README.md → docs/HIRING_MANAGER_REVIEW.md
- `renderChart()` --indirect_call--> `money()`  [INFERRED]
  app/app.js → app/analytics.js
- `render()` --calls--> `monthLabel()`  [EXTRACTED]
  app/app.js → app/analytics.js
- `renderChart()` --calls--> `monthLabel()`  [EXTRACTED]
  app/app.js → app/analytics.js

## Import Cycles
- None detected.

## Communities (33 total, 13 thin omitted)

### Community 0 - "project_kit.py"
Cohesion: 0.28
Nodes (19): Namespace, bootstrap(), category_slug(), Charter, check(), copy_adapter(), field(), graph_sync() (+11 more)

### Community 1 - "app.js"
Cohesion: 0.27
Nodes (16): deriveFindings(), latestMix(), money(), monthLabel(), percentChange(), validatePayload(), appendFinding(), dashboard (+8 more)

### Community 2 - "scripts"
Cohesion: 0.12
Nodes (16): description, name, private, scripts, check, inventory:sources, load:raw, load:sample (+8 more)

### Community 3 - "pipeline.py"
Cohesion: 0.13
Nodes (34): Connection, Exception, Row, build_id(), build_mix(), deduplicate(), ExcludedRow, identify_official_schema() (+26 more)

### Community 4 - "Handoff"
Cohesion: 0.22
Nodes (9): Hiring Manager Review and Remediation Plan, Blocking next milestone, Current result, Guardrails, Handoff, Recovery commands, M2 Source Quality and Provenance, Milestone Plan (+1 more)

### Community 5 - "validate_dashboard.mjs"
Cohesion: 0.29
Nodes (3): monthlyMix, months, payload

### Community 6 - "PipelineTests"
Cohesion: 0.26
Nodes (4): official_row(), PipelineTests, schema_for(), write_official_zip()

### Community 13 - "End-to-end product refinement plan"
Cohesion: 0.09
Nodes (21): 1. Product goal, 2. Current-state evaluation, 3. Target product capabilities, 4. Recommended target architecture, 5. AI architecture and safety contract, 7. Cross-milestone evaluation gates, 8. Key risks and treatments, 9. Approval decision (+13 more)

### Community 14 - "source_inventory.py"
Cohesion: 0.26
Nodes (19): Any, build_inventory(), extract_report_period(), inspect_text_member(), inspect_zip(), InventoryError, load_contract(), main() (+11 more)

### Community 15 - "6. Milestone-by-milestone delivery plan"
Cohesion: 0.17
Nodes (12): 6. Milestone-by-milestone delivery plan, M0 — Verified real-data baseline, M10 — Public reviewer release and portfolio publication, M1 — Non-destructive verification, M2 — Trust foundation: repository, data contract, quality, and provenance, M3 — Complete the issuance decision workflow, M4 — Integrate monthly factor and approved supplemental sources, M5 — Implement factor, balance, runoff, and prepayment analytics (+4 more)

### Community 16 - "test_source_inventory.py"
Cohesion: 0.30
Nodes (5): approved_contract(), header_sha256(), pending_contract(), SourceInventoryTests, write_zip()

### Community 17 - "Data contract"
Cohesion: 0.20
Nodes (9): Approved issuance-mix taxonomy, Current field allowlist, Current source family, Data contract, Grain and business key, New-source gate, Quality rules, Retention and privacy (+1 more)

### Community 18 - "Evaluation contract"
Cohesion: 0.22
Nodes (8): Cloud/release targets, Engineering gates, Evaluation contract, Fairness and responsible-use evaluation, M2 trust-foundation metrics, M3 product and accessibility targets, M4–M6 analytical and product targets, M7 AI targets

### Community 19 - "Metric glossary"
Cohesion: 0.22
Nodes (8): Correction count, Documented exclusion count, Issuance mix share, Issuance UPB, Issued-security count, Metric glossary, Quality status, Source acceptance rate

### Community 20 - "Freddie Mac MBS Disclosure Intelligence"
Cohesion: 0.29
Nodes (6): Analyst use, Current workflow, Freddie Mac MBS Disclosure Intelligence, Limitations, Problem, Verified result

### Community 21 - "Deployment decision record"
Cohesion: 0.29
Nodes (6): Current state, Deployment decision record, Deployment-ready work, Hosting option, Local preview, Release verification

### Community 22 - "Restricted local tables"
Cohesion: 0.29
Nodes (6): Data dictionary, `monthly_security`, Public aggregate payload, `quality_issue`, Restricted local tables, `source_manifest`

### Community 23 - "M4 factor and supplemental data intake"
Cohesion: 0.33
Nodes (5): M4 factor and supplemental data intake, Machine-enforced contract, No-go rules, Owner approval checklist, Verified official source candidates and transition

### Community 25 - "Project delivery rules"
Cohesion: 0.50
Nodes (3): Project delivery rules, Read first, Rules

### Community 26 - "main"
Cohesion: 0.83
Nodes (3): main(), Path, verify_payload()

## Knowledge Gaps
- **108 isolated node(s):** `statusPanel`, `dashboard`, `retryButton`, `name`, `version` (+103 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `End-to-end product refinement plan` connect `End-to-end product refinement plan` to `6. Milestone-by-milestone delivery plan`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **What connects `statusPanel`, `dashboard`, `retryButton` to the rest of the system?**
  _108 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13090418353576247 - nodes in this community are weakly interconnected._
- **Should `End-to-end product refinement plan` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._