# Graph Report - freddie-mac-mbs-disclosure-analytics  (2026-08-10)

## Corpus Check
- 41 files · ~36,487 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 373 nodes · 651 edges · 37 communities (24 shown, 13 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ff72912d`
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
- m4_conformance.py
- Verified Project Evidence
- Delivery sequence
- source_inventory.py
- Freddie Mac MBS Disclosure Intelligence — BI product specification
- SourceInventoryTests
- Data contract
- Evaluation contract
- Metric glossary
- Freddie Mac MBS Disclosure Intelligence
- Deployment decision record
- Data dictionary
- M4 monthly security and loan data intake
- M2 Source Quality and Provenance
- Project delivery rules
- main
- CLAUDE.md
- User-facing design rules
- Freddie Mac MBS Issuance Monitoring Overview
- category.md
- industry.md
- copilot-instructions.md
- publication.md
- state.md
- test_m4_conformance.py
- verify_m4_safety.py

## God Nodes (most connected - your core abstractions)
1. `scripts` - 14 edges
2. `iter_loan_rows()` - 14 edges
3. `build()` - 13 edges
4. `build_inventory()` - 13 edges
5. `PipelineTests` - 13 edges
6. `ConformanceError` - 11 edges
7. `SourceResult` - 11 edges
8. `PipelineError` - 11 edges
9. `SourceBatch` - 11 edges
10. `Data contract` - 11 edges

## Surprising Connections (you probably didn't know these)
- `build()` --indirect_call--> `connection()`  [INFERRED]
  scripts/m4_conformance.py → tests/test_m4_conformance.py
- `load()` --indirect_call--> `connection()`  [INFERRED]
  scripts/pipeline.py → tests/test_m4_conformance.py
- `renderChart()` --indirect_call--> `money()`  [INFERRED]
  app/app.js → app/analytics.js
- `render()` --calls--> `monthLabel()`  [EXTRACTED]
  app/app.js → app/analytics.js
- `renderChart()` --calls--> `monthLabel()`  [EXTRACTED]
  app/app.js → app/analytics.js

## Import Cycles
- None detected.

## Communities (37 total, 13 thin omitted)

### Community 0 - "project_kit.py"
Cohesion: 0.26
Nodes (20): Namespace, bootstrap(), category_slug(), Charter, check(), copy_adapter(), field(), graph_sync() (+12 more)

### Community 1 - "app.js"
Cohesion: 0.27
Nodes (16): deriveFindings(), latestMix(), money(), monthLabel(), percentChange(), validatePayload(), appendFinding(), dashboard (+8 more)

### Community 2 - "scripts"
Cohesion: 0.10
Nodes (19): description, name, private, scripts, check, inventory:sources, load:m4, load:raw (+11 more)

### Community 3 - "pipeline.py"
Cohesion: 0.13
Nodes (34): Exception, Row, build_id(), build_mix(), deduplicate(), ExcludedRow, identify_official_schema(), insert_batch() (+26 more)

### Community 4 - "Handoff"
Cohesion: 0.33
Nodes (5): External blockers, Handoff, M5 implementation order, Outcome, Recovery commands

### Community 5 - "validate_dashboard.mjs"
Cohesion: 0.29
Nodes (3): monthlyMix, months, payload

### Community 6 - "PipelineTests"
Cohesion: 0.26
Nodes (4): official_row(), PipelineTests, schema_for(), write_official_zip()

### Community 11 - "m4_conformance.py"
Cohesion: 0.18
Nodes (34): build(), cell(), classify_join(), ConformanceError, create_manifest(), field_positions(), finalize_manifest(), insert_batches() (+26 more)

### Community 13 - "Delivery sequence"
Cohesion: 0.11
Nodes (18): BI product principles, Critical design decisions for M4/M5, Current evidence, Delivery sequence, End-to-end product refinement plan, M10 — optional cited assistant, M11 — private cloud release candidate, M12 — reviewer publication (+10 more)

### Community 14 - "source_inventory.py"
Cohesion: 0.21
Nodes (26): build_inventory(), contract_signature(), expected_periods(), extract_report_period(), inspect_text_member(), inspect_zip(), InventoryError, load_contract() (+18 more)

### Community 15 - "Freddie Mac MBS Disclosure Intelligence — BI product specification"
Cohesion: 0.10
Nodes (20): Authoritative references, Credit, collateral, mission, and concentration, Credit, delinquency, and loss mitigation, Decision workflow and information architecture, Definition of usable, Dimensions, Facts, Freddie Mac MBS Disclosure Intelligence — BI product specification (+12 more)

### Community 16 - "SourceInventoryTests"
Cohesion: 0.28
Nodes (5): approved_contract(), header_sha256(), pending_contract(), SourceInventoryTests, write_zip()

### Community 17 - "Data contract"
Cohesion: 0.17
Nodes (11): Approved issuance-mix taxonomy, Current field allowlist, Current source family, Data contract, Grain and business key, M4 implemented contract, Observed loan-level candidates, Observed M4 candidates (+3 more)

### Community 18 - "Evaluation contract"
Cohesion: 0.18
Nodes (10): Cloud/release gates, Evaluation contract, M10 optional AI gates, M4 source and conformance gates, M5 metric gates, M6 semantic-model gates, M7–M8 stakeholder and UX gates, M8–M9 governance/API gates (+2 more)

### Community 19 - "Metric glossary"
Cohesion: 0.20
Nodes (9): Change and comparison rules, Composition and concentration metrics, Credit and servicing metrics, Current verified results, External-only metric family, Issuance and balance metrics, Metric glossary, Prepayment metrics (+1 more)

### Community 20 - "Freddie Mac MBS Disclosure Intelligence"
Cohesion: 0.29
Nodes (6): Boundaries, Decision value, Freddie Mac MBS Disclosure Intelligence, Problem, Product expansion, Verified result

### Community 21 - "Deployment decision record"
Cohesion: 0.40
Nodes (4): Current state, Deployment decision record, Deployment gates, Local workflow

### Community 22 - "Data dictionary"
Cohesion: 0.17
Nodes (11): Classification, Conformed dimensions, Data dictionary, Implemented restricted tables, M4 implemented and downstream target facts, M4 restricted control and facts, `monthly_security`, Public aggregate payload currently implemented (+3 more)

### Community 23 - "M4 monthly security and loan data intake"
Cohesion: 0.18
Nodes (10): 2025 backfill, 2026 backfill and consolidation, Adjacent source-family roadmap, M4 monthly security and loan data intake, Machine-enforced contract, No-go rules, Owner approval checklist, Verified acquisition progress (+2 more)

### Community 25 - "Project delivery rules"
Cohesion: 0.50
Nodes (3): Project delivery rules, Read first, Rules

### Community 26 - "main"
Cohesion: 0.83
Nodes (3): main(), Path, verify_payload()

### Community 28 - "User-facing design rules"
Cohesion: 0.22
Nodes (8): Accessibility and polish, Audience and outcome, Governance, Information hierarchy, Interaction, Language and interpretation, User-facing design rules, Visual selection

### Community 35 - "test_m4_conformance.py"
Cohesion: 0.25
Nodes (6): add_manifest(), add_security(), connection(), fixture_contract(), M4ConformanceTests, write_zip()

### Community 37 - "verify_m4_safety.py"
Cohesion: 0.60
Nodes (4): main(), Path, sampled_restricted_tokens(), tracked_files()

## Knowledge Gaps
- **138 isolated node(s):** `statusPanel`, `dashboard`, `retryButton`, `name`, `version` (+133 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `statusPanel`, `dashboard`, `retryButton` to the rest of the system?**
  _138 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13090418353576247 - nodes in this community are weakly interconnected._
- **Should `Delivery sequence` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Freddie Mac MBS Disclosure Intelligence — BI product specification` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._