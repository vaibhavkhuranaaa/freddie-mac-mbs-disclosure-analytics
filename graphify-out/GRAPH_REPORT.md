# Graph Report - .  (2026-08-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 403 nodes · 794 edges · 32 communities (28 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `90bb4e82`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- M5 Metric Engine
- Issuance Pipeline
- M4 Conformance
- Source Inventory
- Package Scripts
- Project Delivery
- Dashboard Analytics
- Issuance Tests
- Inventory Tests
- M4 Tests
- Dashboard Interface
- Deployment and BI
- Data Contracts
- M5 Verification Evidence
- Milestone Roadmap
- BI Product Specification
- M5 Tests
- M5 Approval Blockers
- Data Dictionary
- M5 Verifier
- MBS Disclosure Analytics Rules
- Dashboard Validation
- Product Modes
- Evidence Registry
- Metric Glossary
- M5 Architecture
- Data Safety
- Static Smoke Test
- Approvals and Publication
- Project Delivery Rules
- CI Quality
- M5 Governance

## God Nodes (most connected - your core abstractions)
1. `scripts` - 16 edges
2. `build()` - 15 edges
3. `iter_loan_rows()` - 14 edges
4. `build()` - 13 edges
5. `build_inventory()` - 13 edges
6. `PipelineTests` - 13 edges
7. `BI Product Specification` - 12 edges
8. `ConformanceError` - 11 edges
9. `SourceResult` - 11 edges
10. `PipelineError` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Bounded-Memory Streaming Components` --semantically_similar_to--> `M5 Supported Metric Engine`  [INFERRED] [semantically similar]
  docs/METHODOLOGY.md → .project/architecture.md
- `Verified M5 Metric Engine` --semantically_similar_to--> `M5 Industry Metric Engine`  [INFERRED] [semantically similar]
  README.md → .project/milestones.yml
- `Trust Change Driver Comparability Action Hierarchy` --semantically_similar_to--> `Trust-to-Investigation Workflow`  [INFERRED] [semantically similar]
  DESIGN.md → docs/BI_PRODUCT_SPEC.md
- `Reviewer Mode` --semantically_similar_to--> `Reviewer Release Boundary`  [INFERRED] [semantically similar]
  PROJECT.md → .project/data.md
- `Verified M4 Conformance` --semantically_similar_to--> `M4 Conformed Source Contracts`  [INFERRED] [semantically similar]
  README.md → .project/milestones.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **M5 Supported Engine Evidence Chain** — _project_architecture_m5_supported_metric_engine, _project_evaluation_supported_contract_verification, _project_evidence_e_032_metric_catalog_evidence, _project_evidence_e_033_streaming_engine_evidence, _project_evidence_e_034_m5_reconciliation_evidence, readme_verified_m5_metric_engine [INFERRED 0.95]
- **M5 External Approval Gate** — _project_handoff_external_approval_blockers, _project_state_m5_blocked_state, _project_milestones_m5_industry_metric_engine, docs_methodology_formula_release_gates, docs_next_chat_prompt_approval_conditioned_continuation [INFERRED 0.95]
- **Governed Native-Grain Metric Flow** — _project_data_m4_implemented_contract, _project_architecture_native_grain_fact_design, docs_methodology_m4_source_method, docs_methodology_m5_metric_method, _project_data_m5_derived_metric_boundary [INFERRED 0.85]
- **Trust-to-Investigation Product Flow** — design_trust_change_driver_comparability_action, docs_bi_product_spec_trust_to_investigation_workflow, app_index_investigation_workflow_ui [INFERRED 0.95]

## Communities (32 total, 4 thin omitted)

### Community 0 - "M5 Metric Engine"
Cohesion: 0.14
Nodes (33): add_top_n_components(), adjacent_month(), build(), build_candidate_metrics(), build_issuance_metrics(), build_security_metrics(), build_trust_metrics(), catalog_sha256() (+25 more)

### Community 1 - "Issuance Pipeline"
Cohesion: 0.13
Nodes (34): Exception, build_id(), build_mix(), deduplicate(), ExcludedRow, identify_official_schema(), insert_batch(), load() (+26 more)

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

### Community 8 - "Inventory Tests"
Cohesion: 0.28
Nodes (5): approved_contract(), header_sha256(), pending_contract(), SourceInventoryTests, write_zip()

### Community 9 - "M4 Tests"
Cohesion: 0.25
Nodes (6): add_manifest(), add_security(), connection(), fixture_contract(), M4ConformanceTests, write_zip()

### Community 10 - "Dashboard Interface"
Cohesion: 0.18
Nodes (13): One Governed Calculation Many Presentations, Investigation Workflow UI, Issuance Dashboard Shell, Issuance Trend UI, Monthly Evidence UI, Release Health UI, Term-Family Mix UI, Accessible Evidence Drill-Through (+5 more)

### Community 11 - "Deployment and BI"
Cohesion: 0.20
Nodes (11): Deployment Approval Gates, Deployment Decision Record, GitHub Actions Verification Path, Local Static Dashboard Workflow, Power BI Local Import Model, Power BI Star Schema, Conformed Dimensions, Business Intelligence Delivery Rules (+3 more)

### Community 12 - "Data Contracts"
Cohesion: 0.20
Nodes (10): Project Instructions, Architecture Decision, M4 Conformed Architecture, Data Contract, Issuance Source Contract, M4 Implemented Contract, M4 Monthly Security and Loan Data Intake, Current State (+2 more)

### Community 13 - "M5 Verification Evidence"
Cohesion: 0.20
Nodes (10): M5 Derived Metric Boundary, Evaluation Contract, M4 Conformance Gates, M5 Metric Gates, M6 Semantic Model Gates, Responsible Use Boundary, Supported Contract Verification, Freddie Mac MBS Disclosure Intelligence Case Study (+2 more)

### Community 14 - "Milestone Roadmap"
Cohesion: 0.27
Nodes (10): M4 Conformed Source Contracts, M5 Industry Metric Engine, M6 Governed Power BI Model, M0-M12 Milestone Roadmap, Credit Score System Separation, M5 Delivery Stage, End-to-End Product Refinement Plan, Project Overview (+2 more)

### Community 15 - "BI Product Specification"
Cohesion: 0.29
Nodes (7): BI Product Specification, Definition of a Usable BI Product, Freddie Mac Daily Prepayment Report, Freddie Mac Single-Family Disclosure Guide v6.2, Metric Contract Standard, Microsoft Power BI Accessibility Guidance, Microsoft Power BI Star-Schema Guidance

### Community 16 - "M5 Tests"
Cohesion: 0.29
Nodes (4): add_m4_manifest(), loan_row(), M5MetricEngineTests, write_partition()

### Community 17 - "M5 Approval Blockers"
Cohesion: 0.22
Nodes (9): External Field and Methodology Approval Blockers, Post-Approval Recovery Path, Bounded-Memory Streaming Components, Formula Release Gates, M4 Source Method, M5 Metric Method, Methodology, Approval-Conditioned Continuation (+1 more)

### Community 18 - "Data Dictionary"
Cohesion: 0.20
Nodes (10): Isolated Analyst and Reviewer Modes, Explicit Reviewer Aggregate Boundary, Data Dictionary, Fact Loan Period, M5 Restricted Metric Store, Monthly Security Table, Native-Grain Supplemental Separation, Public Aggregate Payload (+2 more)

### Community 19 - "M5 Verifier"
Cohesion: 0.33
Nodes (8): main(), Connection, Path, ValueError, M5 metric evidence failed., scalar(), VerificationError, verify()

### Community 20 - "MBS Disclosure Analytics Rules"
Cohesion: 0.29
Nodes (7): As Reported and Latest Known Views, Original and Latest Security-Period Facts, Release Data Classification, MBS Disclosure Analytics Rules, Native Grain and As-Of Timing, Preserved Restatement Evidence, Restricted Data Boundary

### Community 21 - "Dashboard Validation"
Cohesion: 0.29
Nodes (3): monthlyMix, months, payload

### Community 22 - "Product Modes"
Cohesion: 0.47
Nodes (6): Authorized Row-Level Local Use, Reviewer Release Boundary, Authorized Analyst Mode, Metric Scope Boundary, Project Charter, Reviewer Mode

### Community 23 - "Evidence Registry"
Cohesion: 0.33
Nodes (6): E-032 Metric Catalog Evidence, E-033 Streaming Engine Evidence, E-034 M5 Reconciliation Evidence, Evidence Registry, M5 Handoff, M5 Safe Supported Outcome

### Community 24 - "Metric Glossary"
Cohesion: 0.25
Nodes (8): Classic FICO and VS4 Separation, External-Only Metric Family, Governed Record Dispositions, M5 Contract Status, Metric Glossary, Semi-Additive Balance Treatment, SMM and CPR, Prepayment Claim Gate

### Community 25 - "M5 Architecture"
Cohesion: 0.40
Nodes (5): Cloud AI Deployment and Publication Approval Boundary, Correction and As-Of Design, M5 Supported Metric Engine, Native-Grain Fact Design, Power BI Target Architecture

### Community 26 - "Data Safety"
Cohesion: 0.60
Nodes (4): main(), Path, sampled_restricted_tokens(), tracked_files()

### Community 27 - "Static Smoke Test"
Cohesion: 0.83
Nodes (3): main(), Path, verify_payload()

## Knowledge Gaps
- **58 isolated node(s):** `statusPanel`, `dashboard`, `retryButton`, `name`, `version` (+53 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BI Product Specification` connect `BI Product Specification` to `Dashboard Interface`, `Deployment and BI`, `Data Dictionary`, `MBS Disclosure Analytics Rules`, `Metric Glossary`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `Trust-to-Investigation Workflow` connect `Dashboard Interface` to `Milestone Roadmap`, `BI Product Specification`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `M5 Industry Metric Engine` connect `Milestone Roadmap` to `M5 Approval Blockers`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `statusPanel`, `dashboard`, `retryButton` to the rest of the system?**
  _58 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `M5 Metric Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.13765182186234817 - nodes in this community are weakly interconnected._
- **Should `Issuance Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.13090418353576247 - nodes in this community are weakly interconnected._
- **Should `Package Scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._