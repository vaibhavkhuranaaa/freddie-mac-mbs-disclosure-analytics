# Decision 0018: Park Power BI and continue provider-neutral delivery

Date: 2026-08-25

Status: accepted

## Context

M5 is complete and its verified release is usable on the current macOS host. M6 Power BI authoring and acceptance require a Windows Power BI Desktop environment that is not currently available. The missing runtime blocks Power BI-specific evidence, but it does not block a provider-neutral dashboard, investigation workflow, or governed API over the same verified engine.

The project owner directed the team to keep Power BI on the side and continue with all other remaining work.

## Decision

- Park M6 without cancelling it or claiming its acceptance criteria have passed.
- Start M7 directly from the verified M5 and M5.10 release boundary.
- Deliver M7 through M9 as provider-neutral web and API capabilities whose contracts can later feed Power BI.
- Preserve M6 as a resumable lane. When a Windows Power BI Desktop runtime is available, implement and verify the PBIP/TMDL model against the same metric and API contracts.
- Keep M10 AI, M11 cloud deployment, and M12 publication behind their existing separate gates.
- Keep the publication target as complete row-level source and derived data with provenance.

## Why

M7-M9 depend on the verified M5 release and provider-neutral contracts, not on a Power BI runtime. Completing those capabilities preserves delivery momentum and produces reusable dashboard, investigation, and API evidence while keeping Power BI acceptance honest and independently resumable.

## Alternatives rejected

- Stop all delivery at M6: rejected because the missing Windows runtime does not block M7-M9.
- Mark M6 complete from specifications alone: rejected because Power BI parity and acceptance require executable evidence.
- Cancel Power BI: rejected because it remains a valid future client of the same contracts.
- Treat M7-M9 as approval for AI, cloud, deployment, or publication: rejected because those actions have separate risk and authorization gates.

## Changed

M6 moves to parked status. M7-M9 become the active provider-neutral sequence over the verified M5 boundary, while M10-M12 retain their separate approval requirements.

## Consequences

The project can continue on the current host without creating an unverifiable Power BI placeholder. The web product and semantic service become testable reference clients for the verified metric engine. Power BI-specific parity, refresh, accessibility, and access evidence remain outstanding until M6 resumes.

## Not done by this decision

This decision does not approve AI, paid services, cloud resources, deployment, push, or publication. It does not release unsupported metrics or alter the immutable M5 release.
