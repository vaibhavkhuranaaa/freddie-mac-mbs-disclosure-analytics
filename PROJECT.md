# Freddie Mac MBS Disclosure Intelligence

## Charter

- **Industry:** mortgage-backed securities disclosure analytics
- **Current verified release:** governed month-end Freddie Mac issuance monitoring plus M4 facts and the supported M5 metric engine
- **Target product:** authorized provider-neutral decision product for issuance, balance/factor, prepayment, credit, collateral, concentration, correction, quality, and investigation workflows; Power BI remains an optional client
- **Primary stakeholder:** MBS disclosure operations or market-data analyst; executive summaries support nontechnical leadership
- **Authorized data use:** the owner is authorized to use the acquired Freddie Mac source files at row level for this project
- **Retention:** seven years from acquisition; delete earlier if authorization ends
- **Current delivery:** provider-neutral Python/SQLite/browser product with a $0 operating baseline
- **Current governed issuance coverage:** 19 files, 2024-12 through 2026-06
- **Current acquired expansion:** 71 monthly-security and 35 monthly loan-level archives in restricted ignored storage

## Purpose

Help a stakeholder decide whether a disclosure release is trustworthy, what changed, which segments drove the movement, whether correction or comparability issues explain it, and what investigation to assign. Calculations, lineage, quality, and limitations must be reproducible from source to decision.

## Publication target

Publish complete row-level source and derived data with certified metrics, governed drill-through, provenance, and investigation evidence.

## Implemented baseline

- Exact archive/member, ordered-header, schema-period, value, duplicate, and reconciliation controls.
- 60,604 physical issuance rows reconciled to 59,904 accepted observations and 700 documented exclusions; zero rejected and duplicate keys.
- SQLite observations, source manifests, quality events, and release payload.
- Approved monthly-security and monthly-loan contracts, 9,240,038 security-period facts, and 264,922,553 loan-period facts in governed external storage.
- 693,640,933 M4 source rows reconciled with zero rejected, duplicate, or quarantined rows; every loan/security join is reason coded.
- Issuance UPB/count, corrections, approved term-family composition, active-data findings, investigation prompts, evidence, and limitations.
- Loading/error/retry, year-aware descriptions, keyboard focus, forced colors, responsive layout, automated tests, and static smoke verification.
- Value-free inventory of the acquired monthly-security and loan-level source population.
- Versioned 54-measure M5 catalog: 38 supported and implemented, 11 methodology-gated, 2 field-contract extensions, and 3 external families.
- Fingerprinted M4 v2 facts populate all 45 approved field additions, retain invalid provider mission values as explicit unavailable states, and enforce the current-population invariant that all 264,922,553 loan joins are matched.
- Streaming and disk-backed M5 components across all 264,922,553 loan-period and 9,240,038 security-period facts with 1,816 parity checks, 1,068 formula checks, and idempotent checksum evidence.

## Target decision product

The complete page, metric, semantic-model, visual, accessibility, governance, and history contract is `docs/BI_PRODUCT_SPEC.md`. The executable M0-M12 sequence is maintained in the private delivery workspace.

The target covers:

- release completeness, schema, revisions, freshness, reconciliation, join coverage, and comparability;
- issuance, outstanding balances, security/loan counts, WAC, WALA, WAM, factors, removals, and balance bridges;
- approved paydown, runoff, SMM/CPR, seasoning, and cohort behavior;
- delinquency bands, transitions, cures, modifications, deferrals, assistance, and guarantees;
- FICO/VS4, LTV/CLTV/ELTV, DTI, purpose, occupancy, property, channel, geography, seller, servicer, mission, green, and social composition;
- executive summaries, cohort exploration, evidence drill-through, and governed investigation notes.

Price, yield, OAS, spreads, duration, convexity, WAL, market return, MSR, macro sensitivity, and loss severity remain external-data extensions. They must not be simulated or implied from the current disclosures.

## Current implementation boundary

M0-M5 and M7-M9 are complete. Nine field-backed metric families and disk-backed original/latest loan transitions feed a provider-neutral dashboard with release, issuance, portfolio, credit, concentration, cohort, and investigation workflows, explicit comparability limits, and complete release provenance. The authenticated semantic API carries the same governed contract and records request and investigation audit evidence. Freshness remains prospective; delinquent-loan purchases remain unavailable because disclosed involuntary removals are broader. DPR-backed and other source-gated measures remain explicitly unreleased. M6 Power BI work is parked under decision 0018.

The bounded M10 AI evaluation is approved and complete; its runtime route remains disabled by default. Cloud infrastructure, deployment, and publication are not approved. Full-data publication is planned for the publication phase after integrity and redistribution-rights gates pass. The product is descriptive operational analytics and does not make borrower, investment, valuation, trading, hedging, or causal recommendations.

## Success criteria

The product is complete when every M0-M12 acceptance gate applicable to the selected release passes, a nontechnical stakeholder completes the trust-to-investigation workflow without SQL, all displayed metrics reconcile to the certified model, full-data publication preserves provenance and integrity, and public claims match verified evidence.
