# Handoff

## Current result

M2 is complete. Pipeline revision `b0a4cf876448` enforces exact official schema fingerprints and period bounds, maintains a reconciled source manifest and quality ledger, documents status-`C` blank-balance exclusions, quarantines invalid/duplicate rows, and blocks publication on any error.

Build `7c0f195305e1...` reconciles 60,604 source rows into 59,904 accepted/published observations and 700 documented exclusions, with zero rejected and duplicate rows. Twelve automated tests, the governed payload validator, the static preview smoke path, project-record checks, and Graphify health checks pass.

## Exact next milestone

Complete **M3 — Complete the issuance decision workflow** from `.project/milestones.yml`.

1. Replace fixed March/April findings with data-derived comparisons and investigation prompts.
2. Remove the uninformative issuance-date factor view.
3. Define and test a Prefix-to-product taxonomy with explicit `Unknown/Unmapped` coverage.
4. Publish issuance-mix aggregates plus quality, freshness, methodology, and limitations.
5. Implement loading, empty, partial, stale, and error states; year-aware chart labels and summaries; keyboard and responsive behavior.
6. Apply Impeccable's incumbent-system refinement and run its detector once after UI edits.

## Guardrails

- Raw ZIPs and local SQLite state remain ignored and restricted.
- Current claims remain issuance-only; mix begins only after its taxonomy is documented and tested.
- Factor, runoff, prepayment, AI, cloud, deployment, and publication remain gated.
- Do not create a remote, push, provision, spend, deploy, or publish without the corresponding recorded approval.

## Recovery commands

```sh
npm run load:raw
npm run check
npm run serve
```
