# Hiring-manager review and remediation plan

**Review lens:** senior technical hiring manager assessing a recruiter-facing data and analytics portfolio project.  
**Reviewed:** 2026-08-01  
**Current evidence:** 19 official month-end issuance files, 59,904 security observations, local SQLite processing, and a static monthly-aggregate dashboard.

## Executive assessment

The project has a credible core: it ingests official Freddie Mac month-end issuance security-level ZIP files, preserves local provenance, and turns 59,904 observations into a restrained monthly analytics experience. The dashboard is clear and business-led.

At the time of review, project records still described a synthetic, pre-approval demo while the dashboard used real data. The project-record synchronization in this remediation pass resolves that documentation conflict. The verification path was made non-destructive on 2026-08-04: sample output is isolated under ignored local files, the released dashboard payload is validated in place, and checksum regression tests protect it. The delivered analysis is issuance monitoring only; it does not currently implement balance runoff, prepayment, timeliness, or disclosure-completeness monitoring.

## What demonstrates capability

- Official `FRE_IS_YYYYMM.zip` parsing with expected-header checks in `scripts/pipeline.py`.
- Local SQLite ingestion and SHA-256 source manifest.
- Monthly-only browser export; the browser no longer receives security-level records.
- A business question, trends, evidence table, and findings rather than an undirected dashboard.
- No paid database, hosted service, or external API dependency.

## Findings

### P0 — correct before recruiter sharing

| Finding | Why it matters | Correction |
| --- | --- | --- |
| Legacy project records described synthetic data, pending approvals, and no acquisition while the working dashboard used real local issuance files. | Contradictory claims are a credibility failure. | **Resolved 2026-08-01:** `PROJECT.md`, `.project/`, `DEPLOYMENT.md`, `AGENTS.md`, `docs/METHODOLOGY.md`, and `portfolio/project.json` now state the authorized real-data issuance-monitoring model. |
| `npm run check` ran `load:sample`, which wrote to `app/data/dashboard.json`. | A routine check could replace the real recruiter demo with sample data. | **Resolved 2026-08-04:** sample output and SQLite state are isolated under ignored `local/` paths; `check` validates the released payload without sample loading; checksum regression tests prove the release file remains unchanged. |
| The implemented source set is issuance only. CPR is set to `0`, and factor/current-UPB values from issuance records do not provide a runoff or prepayment analysis. | The project must not claim analysis it does not perform. | Name the delivered project “MBS Issuance Monitoring”; state balance runoff/prepayment as the next integration using monthly factor and supplemental files. |
| The README does not yet provide one non-destructive, verified reviewer sequence. | A reviewer should be able to run and assess the project confidently. | Document: test → load approved local files → preview → expected dashboard state → current limits. |

### P1 — strengthen engineering and analytical evidence

| Finding | Why it matters | Correction |
| --- | --- | --- |
| Findings hard-code April and March 2026; titles assume the 2025 peak remains the peak. | A refresh can make findings wrong. | Generate peak, trough, latest trend, and comparability language dynamically from the loaded periods. |
| The factor chart is not informative for issuance-at-issuance records. | It reads as an unused metric rather than insight. | Remove it until monthly factor files are integrated, or label it as issuance-date factor expected to equal 1.0. |
| ZIP rows failing basic conditions are silently skipped. | Silent loss weakens data-quality assurance. | Track accepted/rejected rows by source file and include counts in safe output metadata. |
| Test coverage has only one happy-path fixture. | Recruiters cannot see robust ingestion behavior. | Add official-ZIP, missing-header, invalid-value, empty/multi-file ZIP, duplicate, aggregate-total, and non-destructive-output tests. |
| Generated metadata lacks period range, rejection count, generated timestamp, and pipeline version. | Limits reproducibility and auditability. | Publish these safe metadata fields with monthly aggregates. |
| The CI workflow checks project-record shape but does not prove the dashboard. | The project lacks delivery evidence. | Run tests, dashboard-schema validation, and static-site smoke checks in CI. |
| There is no visible Git repository in the intended project location. | Source-control history is expected for an engineering portfolio. | Initialize or restore the intended repository, retain raw ZIPs as ignored files, and add concise meaningful commits. |

### P2 — improve story and polish

| Finding | Why it matters | Correction |
| --- | --- | --- |
| The January 2025 peak has no comparability context. | A hiring manager will ask whether it is a true change or reporting effect. | Add a visible “investigate comparability” note until the source-period explanation is documented. |
| The findings say what moved but not why an operations team would act. | Insight should connect to an operational use. | Frame issuance monitoring around capacity planning, market-activity review, and release validation; do not imply investment advice. |
| Monthly chart labels omit year and there is no fetch-error or empty state. | Limits usability and resilience. | Use year-aware labels, accessible text summaries, and loading/error/empty states. |
| The dashboard has no issuance-mix view. | One additional permitted segmentation would show deeper analytical judgment. | If approved, aggregate by security prefix/product group and add a composition trend. |

## Remediation sequence

### Phase 1 — establish a trustworthy release path

1. Separate fixture/sample output from `app/data/dashboard.json`.
2. Update package scripts so `npm run check` cannot mutate published dashboard data.
3. Add validation for the actual monthly aggregate payload.
4. Update all project records and public copy to the actual issuance-monitoring scope.
5. Confirm a clean reviewer journey from clone/project folder to local preview.

**Exit criteria:** test commands leave the real dashboard untouched, public wording is consistent, and the README has one verified run path.

### Phase 2 — make the data pipeline defensible

1. Add accepted/rejected/duplicate accounting per input file.
2. Make official ZIP validation strict and explain errors clearly.
3. Publish safe provenance metadata: file count, observation count, period range, rejection count, generated timestamp, and pipeline version.
4. Expand unit fixtures and add aggregate-accuracy tests.
5. Make CI run the same checks a reviewer relies on.

**Exit criteria:** a source file problem is visible and testable; dashboard numbers have a repeatable provenance path.

### Phase 3 — sharpen the portfolio story

1. Generate findings from the active data rather than fixed months.
2. Remove non-informative issuance-factor analysis.
3. Add a comparability note for unusual periods and an explicit operational interpretation.
4. Add one permitted mix segmentation only after its definition and data use are documented.
5. Add loading, error, and empty states plus year-aware chart labels.

**Exit criteria:** the page answers what changed, why the monitoring matters, and what the analyst would investigate next.

### Phase 4 — extend scope only with the right files

1. Ingest monthly security-factor files to measure factor/balance movement.
2. Add supplemental files only after a documented field allowlist and business question.
3. Implement runoff/prepayment metrics only when their source fields are truly available and validated.

**Exit criteria:** any claim about balances, paydowns, prepayment, or disclosure quality is backed by an integrated source and a tested calculation.

## Recommended project positioning

Use this concise positioning until the monthly factor and supplemental integrations are complete:

> A local-first Freddie Mac MBS issuance-monitoring case study that converts official month-end security-level files into reproducible monthly issuance, security-count, correction, and issuance-mix analytics. It demonstrates ingestion validation, provenance, aggregate publication, and a recruiter-facing decision-support dashboard without paid infrastructure.

Do not position the current build as a prepayment, runoff, trading, valuation, or borrower analytics platform.
