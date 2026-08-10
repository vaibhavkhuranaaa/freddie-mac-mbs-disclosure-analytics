# Architecture decision

## Decision

- **Status:** governed real-data local issuance product; end-to-end roadmap approved 2026-08-09
- **Data access:** authorized Freddie Mac user; restricted official files remain local and out of Git/public artifacts
- **Current delivery:** local static reviewer application backed by local SQLite and an aggregate payload
- **Current cost:** $0 operating baseline
- **Cloud authority:** not approved; the Azure-first reference remains a proposal
- **AI authority:** not approved; deterministic metric and evidence APIs must precede any assistant

## Implemented trust architecture

```text
Authorized FRE_IS ZIPs
        ↓
Archive/member + exact ordered-header fingerprint + period validation
        ↓
Row rules + documented exclusion + duplicate detection
        ├── accepted security observations (restricted local SQLite)
        ├── source manifest and count reconciliation
        └── value-free quality events
        ↓
All sources pass? ── no → block publication and investigate
        │
       yes
        ↓
Versioned monthly aggregate JSON → static reviewer dashboard
```

The verified build processes 60,604 physical rows from 19 files. It publishes 59,904 issuance observations, records 700 status-`C` blank-balance exclusions, and reports zero rejected and duplicate rows. Twelve files use `fre-is-legacy-v1`; seven use `fre-is-fico-v2` beginning in December 2025.

## Current technical choices

| Choice | Reason | Scale trigger |
| --- | --- | --- |
| Python standard library pipeline | Direct ZIP/CSV/SQLite support with no runtime dependency install | Multiple source families, complex orchestration, or performance evidence requires a pinned container dependency set |
| Exact header fingerprints | Any provider schema change is visible and reviewed | Add a new version only with data-contract and fixture evidence |
| SQLite | Reproducible restricted local analytical store at current size | Concurrent authorized analysts, API query load, scheduled jobs, or 10x test failure |
| Static HTML/CSS/JS | Fast, low-cost reviewer mode with no server data exposure | Analyst drill-down and saved investigations require an authenticated API |
| Aggregate JSON | Deterministic public/reviewer boundary | Larger segment payloads or governed queries require a versioned semantic API |

## Approved logical target

```text
Restricted landing → versioned validation/quarantine → conformed security-period data
        → governed metric transformations → approved aggregate products
        → public static reviewer mode
        → authenticated analyst API/UI

Approved documentation/evidence → governed retrieval index
Authenticated metric/evidence tools + retrieval → optional cited assistant

Identity, secrets, CI/CD, IaC, logs, alerts, budgets, backup, and recovery govern every cloud component.
```

## Azure-first proposal (not authorized to provision)

| Capability | Proposed service | Boundary |
| --- | --- | --- |
| Restricted storage | ADLS Gen2 | Immutable landing and curated zones |
| Monthly jobs | Event Grid + Container Apps Jobs | Serverless batch; no continuously running cluster |
| Serving | Materialized aggregates first; Functions API when needed | Managed analytical database only after a measured scale trigger |
| UI and identity | Static Web Apps + Entra ID | Public and authorized modes remain separated |
| Secrets/telemetry | Key Vault + managed identity + Application Insights | No committed secrets; auditable job/API behavior |
| AI after M7 approval | Azure OpenAI/AI Foundry + AI Search | Tool-only deterministic metrics and approved cited documents |
| Delivery after M8 approval | GitHub Actions + Bicep | Reviewed revision-to-environment lineage |

The platform, region, services, tiers, cost ceiling, identity, retention, backup, teardown, and data-residency choices require explicit approval before infrastructure is applied.

## Public claims

Current claims are limited to authorized local issuance ingestion, exact schema/period validation, reconciled quality/provenance, monthly aggregates, automated verification, and the static local dashboard. Issuance mix, factor/runoff/prepayment, authenticated APIs, AI, cloud, and hosted release remain planned until their milestone evidence exists.
