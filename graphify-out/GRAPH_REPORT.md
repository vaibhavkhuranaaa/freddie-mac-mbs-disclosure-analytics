# Graph Report - .  (2026-08-10)

## Corpus Check
- Corpus is ~47,806 words - fits in a single context window. You may not need a graph.

## Summary
- 391 nodes · 777 edges · 31 communities (26 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Issuance Pipeline
- M5 Metric Engine
- M4 Conformance
- Source Inventory
- Package Scripts
- Project Delivery
- Dashboard Analytics
- Issuance Tests
- Metric Methodology
- Inventory Tests
- Project Governance
- M4 Tests
- Dashboard Interface
- Deployment and BI
- M5 Tests
- Product Modes
- Product Specification
- Data Model
- M5 Verification
- Dashboard Validation
- Case Study
- M5 Documentation
- Data Safety
- Milestone Handoff
- Static Smoke Test
- Semantic Model Roadmap
- Approvals and Publication
- Data Rights
- Evaluation Gates
- CI Quality
- Evidence Registry

## God Nodes (most connected - your core abstractions)
1. `scripts` - 16 edges
2. `build()` - 15 edges
3. `BI Product Specification` - 15 edges
4. `iter_loan_rows()` - 14 edges
5. `build()` - 13 edges
6. `build_inventory()` - 13 edges
7. `PipelineTests` - 13 edges
8. `ConformanceError` - 11 edges
9. `SourceResult` - 11 edges
10. `PipelineError` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Evidence-Backed Investigation Decision` --semantically_similar_to--> `Definition of a Usable BI Product`  [INFERRED] [semantically similar]
  CASE-STUDY.md → docs/BI_PRODUCT_SPEC.md
- `Trust Change Driver Comparability Action Hierarchy` --semantically_similar_to--> `Trust-to-Investigation Workflow`  [INFERRED] [semantically similar]
  DESIGN.md → docs/BI_PRODUCT_SPEC.md
- `M5 Contract Status` --semantically_similar_to--> `Supported M5 Metric Engine`  [INFERRED] [semantically similar]
  docs/metric-glossary.md → PROJECT.md
- `Verified M5 Supported Metric Engine` --semantically_similar_to--> `Supported M5 Metric Engine`  [INFERRED] [semantically similar]
  README.md → PROJECT.md
- `build()` --indirect_call--> `connection()`  [INFERRED]
  scripts/m4_conformance.py → tests/test_m4_conformance.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **M5 Acceptance Approval Gate** — _project_approvals_m5_external_approval_gates, _project_evaluation_m5_metric_gates, _project_handoff_m5_acceptance_blockers, _project_milestones_m5_industry_metric_engine, _project_state_m5_blocked_state [INFERRED 0.95]
- **Trust-to-Investigation Product Flow** — design_trust_change_driver_comparability_action, docs_bi_product_spec_trust_to_investigation_workflow, app_index_investigation_workflow_ui, case_study_evidence_backed_investigation [INFERRED 0.95]
- **Governed Analyst and Reviewer Release Boundary** — project_authorized_analyst_mode, project_reviewer_mode, docs_bi_product_spec_reviewer_aggregate_boundary, docs_data_dictionary_release_classification, docs_rules_industry_restricted_data_boundary [INFERRED 0.95]
- **Certified Metric Governance** — docs_bi_product_spec_metric_contract_standard, docs_methodology_metric_governance_method, docs_metric_glossary_metric_glossary, docs_rules_category_certified_semantic_model [INFERRED 0.95]

## Communities (31 total, 5 thin omitted)

### Community 0 - "Issuance Pipeline"
Cohesion: 0.13
Nodes (34): Exception, build_id(), build_mix(), deduplicate(), ExcludedRow, identify_official_schema(), insert_batch(), load() (+26 more)

### Community 1 - "M5 Metric Engine"
Cohesion: 0.14
Nodes (33): add_top_n_components(), adjacent_month(), build(), build_candidate_metrics(), build_issuance_metrics(), build_security_metrics(), build_trust_metrics(), catalog_sha256() (+25 more)

### Community 2 - "M4 Conformance"
Cohesion: 0.18
Nodes (34): build(), cell(), classify_join(), ConformanceError, create_manifest(), field_positions(), finalize_manifest(), insert_batches() (+26 more)

### Community 3 - "Source Inventory"
Cohesion: 0.21
Nodes (26): build_inventory(), contract_signature(), expected_periods(), extract_report_period(), inspect_text_member(), inspect_zip(), InventoryError, load_contract() (+18 more)

### Community 4 - "Package Scripts"
Cohesion: 0.09
Nodes (21): description, name, private, scripts, check, inventory:sources, load:m4, load:m5 (+13 more)

### Community 5 - "Project Delivery"
Cohesion: 0.26
Nodes (20): Namespace, bootstrap(), category_slug(), Charter, check(), copy_adapter(), field(), graph_sync() (+12 more)

### Community 6 - "Dashboard Analytics"
Cohesion: 0.27
Nodes (16): deriveFindings(), latestMix(), money(), monthLabel(), percentChange(), validatePayload(), appendFinding(), dashboard (+8 more)

### Community 7 - "Issuance Tests"
Cohesion: 0.26
Nodes (4): official_row(), PipelineTests, schema_for(), write_official_zip()

### Community 8 - "Metric Methodology"
Cohesion: 0.14
Nodes (15): Aggregate-Only Reproducibility Boundary, Bounded-Memory M5 Component Engine, Fail-Closed Issuance Pipeline, M4 Source Contract Method, Methodology, Metric Governance Method, Classic FICO and VS4 Separation, External-Only Metric Family (+7 more)

### Community 9 - "Inventory Tests"
Cohesion: 0.28
Nodes (5): approved_contract(), header_sha256(), pending_contract(), SourceInventoryTests, write_zip()

### Community 10 - "Project Governance"
Cohesion: 0.14
Nodes (14): Project Instructions, M5 External Approval Gates, Architecture Decision, Verified M4 Conformance, Verified M5 Supported Engine, M4 Implemented Contract, M5 Derived Metric Boundary, M5 Acceptance Blockers (+6 more)

### Community 11 - "M4 Tests"
Cohesion: 0.25
Nodes (6): add_manifest(), add_security(), connection(), fixture_contract(), M4ConformanceTests, write_zip()

### Community 12 - "Dashboard Interface"
Cohesion: 0.20
Nodes (12): Investigation Workflow UI, Issuance Dashboard Shell, Issuance Trend UI, Monthly Evidence UI, Release Health UI, Term-Family Mix UI, Accessible Evidence Drill-Through, Certified Semantic Model Only (+4 more)

### Community 13 - "Deployment and BI"
Cohesion: 0.20
Nodes (11): Deployment Approval Gates, Deployment Decision Record, GitHub Actions Verification Path, Local Static Dashboard Workflow, Power BI Local Import Model, Power BI Star Schema, Conformed Dimensions, Business Intelligence Delivery Rules (+3 more)

### Community 14 - "M5 Tests"
Cohesion: 0.29
Nodes (4): add_m4_manifest(), loan_row(), M5MetricEngineTests, write_partition()

### Community 15 - "Product Modes"
Cohesion: 0.25
Nodes (9): First Unblocked Milestone Rule, Project Delivery Adapter, Isolated Analyst and Reviewer Modes, Explicit Reviewer Aggregate Boundary, Public Aggregate Payload, Authorized Analyst Mode, Descriptive Operational Analytics Boundary, Freddie Mac MBS Disclosure Intelligence Project Charter (+1 more)

### Community 16 - "Product Specification"
Cohesion: 0.22
Nodes (9): BI Product Specification, Freddie Mac Daily Prepayment Report, Freddie Mac Single-Family Disclosure Guide v6.2, Metric Contract Standard, As Reported and Latest Known Views, Microsoft Power BI Accessibility Guidance, Microsoft Power BI Star-Schema Guidance, Original and Latest Security-Period Facts (+1 more)

### Community 17 - "Data Model"
Cohesion: 0.22
Nodes (9): Data Dictionary, Fact Loan Period, M5 Restricted Metric Store, Monthly Security Table, Native-Grain Supplemental Separation, Quality Issue Table, Release Data Classification, Source Manifest (+1 more)

### Community 18 - "M5 Verification"
Cohesion: 0.33
Nodes (8): main(), Connection, Path, ValueError, M5 metric evidence failed., scalar(), VerificationError, verify()

### Community 19 - "Dashboard Validation"
Cohesion: 0.29
Nodes (3): monthlyMix, months, payload

### Community 20 - "Case Study"
Cohesion: 0.33
Nodes (6): Evidence-Backed Investigation Decision, Freddie Mac MBS Disclosure Intelligence Case Study, Issuance-Only Reviewer Release Boundary, Trust Before Analysis, Verified Issuance Product, Definition of a Usable BI Product

### Community 21 - "M5 Documentation"
Cohesion: 0.33
Nodes (6): M5 Contract Status, Supported M5 Metric Engine, Freddie Mac MBS Disclosure Intelligence README, Local Verification Path, Verified M4 Conformance, Verified M5 Supported Metric Engine

### Community 22 - "Data Safety"
Cohesion: 0.60
Nodes (4): main(), Path, sampled_restricted_tokens(), tracked_files()

### Community 23 - "Milestone Handoff"
Cohesion: 0.50
Nodes (4): Approval-Gated M5 Continuation, M5 Evidence Snapshot, M6 Start Gate, Next-Chat Kickoff Prompt

### Community 24 - "Static Smoke Test"
Cohesion: 0.83
Nodes (3): main(), Path, verify_payload()

### Community 25 - "Semantic Model Roadmap"
Cohesion: 0.67
Nodes (3): Power BI Semantic Model, M5 Industry Metric Engine, M6 Governed Power BI Semantic Model

## Knowledge Gaps
- **61 isolated node(s):** `statusPanel`, `dashboard`, `retryButton`, `name`, `version` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BI Product Specification` connect `Product Specification` to `Metric Methodology`, `Dashboard Interface`, `Deployment and BI`, `Product Modes`, `Case Study`, `M5 Documentation`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `statusPanel`, `dashboard`, `retryButton` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Issuance Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.13090418353576247 - nodes in this community are weakly interconnected._
- **Should `M5 Metric Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.13630229419703105 - nodes in this community are weakly interconnected._
- **Should `Package Scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `Metric Methodology` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Project Governance` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._