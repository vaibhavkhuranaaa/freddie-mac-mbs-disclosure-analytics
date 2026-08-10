# Freddie Mac MBS Disclosure Intelligence

## Charter

- **Industry:** mortgage-backed securities disclosure analytics
- **Current verified release:** governed month-end Freddie Mac issuance monitoring
- **Target product:** authorized row-level Power BI decision product for issuance, balance/factor, prepayment, credit, collateral, concentration, correction, quality, and investigation workflows
- **Primary stakeholder:** MBS disclosure operations or market-data analyst; executive summaries support nontechnical leadership
- **Authorized data use:** the owner is authorized to use the acquired Freddie Mac source files at row level for this project
- **Retention:** seven years from acquisition; delete earlier if authorization ends
- **Current delivery:** local Python/SQLite/static dashboard with a $0 operating baseline
- **Current governed issuance coverage:** 19 files, 2024-12 through 2026-06
- **Current acquired expansion:** 71 monthly-security and 35 monthly loan-level archives in restricted ignored storage

## Purpose

Help a stakeholder decide whether a disclosure release is trustworthy, what changed, which segments drove the movement, whether correction or comparability issues explain it, and what investigation to assign. Calculations, lineage, quality, and limitations must be reproducible from source to decision.

## Product modes

- **Authorized analyst mode:** full approved security-period and loan-period detail, certified metrics, governed drill-through, and investigation evidence.
- **Reviewer mode:** a separately generated, explicitly approved aggregate boundary. Internal row-level authorization does not grant public redistribution.

## Implemented baseline

- Exact archive/member, ordered-header, schema-period, value, duplicate, and reconciliation controls.
- 60,604 physical issuance rows reconciled to 59,904 accepted observations and 700 documented exclusions; zero rejected and duplicate keys.
- Restricted SQLite observations, source manifests, value-free quality events, and aggregate-only release payload.
- Issuance UPB/count, corrections, approved term-family composition, active-data findings, investigation prompts, evidence, and limitations.
- Loading/error/retry, year-aware descriptions, keyboard focus, forced colors, responsive layout, automated tests, and static smoke verification.
- Value-free inventory of the acquired monthly-security and loan-level source population.

## Target decision product

The complete page, metric, semantic-model, visual, accessibility, governance, and history contract is `docs/BI_PRODUCT_SPEC.md`. The executable M0–M12 sequence is `.project/milestones.yml`.

The target covers:

- release completeness, schema, revisions, freshness, reconciliation, join coverage, and comparability;
- issuance, outstanding balances, security/loan counts, WAC, WALA, WAM, factors, removals, and balance bridges;
- approved paydown, runoff, SMM/CPR, seasoning, and cohort behavior;
- delinquency bands, transitions, cures, modifications, deferrals, assistance, and guarantees;
- FICO/VS4, LTV/CLTV/ELTV, DTI, purpose, occupancy, property, channel, geography, seller, servicer, mission, green, and social composition;
- executive summaries, cohort exploration, evidence drill-through, and governed investigation notes.

Price, yield, OAS, spreads, duration, convexity, WAL, market return, MSR, macro sensitivity, and loss severity remain external-data extensions. They must not be simulated or implied from the current disclosures.

## Current implementation boundary

M0–M3 are complete. M4 is next and is authorized for local implementation: finalize the monthly-security and loan-level field/join/correction contract, parse all approved families, create conformed security-period and loan-period records, and prove reconciliation/backfill parity. The acquired files alone do not authorize an unverified formula or public claim.

AI services, cloud infrastructure, paid resources, deployment, and publication are not approved. The product is descriptive operational analytics and does not make borrower, investment, valuation, trading, hedging, or causal recommendations.

## Success criteria

The product is complete when every M0–M12 acceptance gate applicable to the selected release passes, a nontechnical stakeholder completes the trust-to-investigation workflow without SQL, all displayed metrics reconcile to the certified model, restricted data stays inside the authorized boundary, and public claims match verified evidence.
