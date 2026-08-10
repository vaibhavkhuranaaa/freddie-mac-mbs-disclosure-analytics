# Graph Report - freddie-mac-mbs-disclosure-analytics  (2026-08-09)

## Corpus Check
- 34 files · ~21,514 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 240 nodes · 360 edges · 29 communities (16 shown, 13 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8f47aad0`
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
- 6. Milestone-by-milestone delivery plan
- Data contract
- Evaluation contract
- Metric glossary
- Freddie Mac MBS Disclosure Intelligence
- Deployment decision record
- Restricted local tables
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
3. `PipelineError` - 11 edges
4. `SourceBatch` - 11 edges
5. `scripts` - 10 edges
6. `bootstrap()` - 10 edges
7. `End-to-end product refinement plan` - 10 edges
8. `render()` - 9 edges
9. `parse_official_zip()` - 9 edges
10. `load()` - 9 edges

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

## Communities (29 total, 13 thin omitted)

### Community 0 - "project_kit.py"
Cohesion: 0.27
Nodes (20): Namespace, bootstrap(), category_slug(), Charter, check(), copy_adapter(), field(), graph_sync() (+12 more)

### Community 1 - "app.js"
Cohesion: 0.27
Nodes (16): deriveFindings(), latestMix(), money(), monthLabel(), percentChange(), validatePayload(), appendFinding(), dashboard (+8 more)

### Community 2 - "scripts"
Cohesion: 0.12
Nodes (15): description, name, private, scripts, check, load:raw, load:sample, serve (+7 more)

### Community 3 - "pipeline.py"
Cohesion: 0.14
Nodes (33): Connection, Exception, Row, build_id(), build_mix(), deduplicate(), ExcludedRow, identify_official_schema() (+25 more)

### Community 4 - "Handoff"
Cohesion: 0.22
Nodes (9): Hiring Manager Review and Remediation Plan, Current result, Exact next action, Guardrails, Handoff, Recovery commands, M2 Source Quality and Provenance, Milestone Plan (+1 more)

### Community 5 - "validate_dashboard.mjs"
Cohesion: 0.29
Nodes (3): monthlyMix, months, payload

### Community 6 - "PipelineTests"
Cohesion: 0.26
Nodes (4): official_row(), PipelineTests, schema_for(), write_official_zip()

### Community 13 - "6. Milestone-by-milestone delivery plan"
Cohesion: 0.06
Nodes (33): 1. Product goal, 2. Current-state evaluation, 3. Target product capabilities, 4. Recommended target architecture, 5. AI architecture and safety contract, 6. Milestone-by-milestone delivery plan, 7. Cross-milestone evaluation gates, 8. Key risks and treatments (+25 more)

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

### Community 25 - "Project delivery rules"
Cohesion: 0.50
Nodes (3): Project delivery rules, Read first, Rules

### Community 26 - "main"
Cohesion: 0.83
Nodes (3): main(), Path, verify_payload()

## Knowledge Gaps
- **103 isolated node(s):** `statusPanel`, `dashboard`, `retryButton`, `name`, `version` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineError` connect `pipeline.py` to `project_kit.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `statusPanel`, `dashboard`, `retryButton` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13655761024182078 - nodes in this community are weakly interconnected._
- **Should `6. Milestone-by-milestone delivery plan` be split into smaller, more focused modules?**
  _Cohesion score 0.058823529411764705 - nodes in this community are weakly interconnected._