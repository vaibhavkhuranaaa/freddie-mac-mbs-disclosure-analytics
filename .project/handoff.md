# Handoff

## Current result

M2 implementation is complete and awaiting its source-control/evidence closure. The pipeline now enforces exact official schema fingerprints and period bounds, maintains a reconciled source manifest and quality ledger, documents status-`C` blank-balance exclusions, quarantines invalid/duplicate rows, and blocks publication on any error.

The authorized rebuild reconciles 60,604 source rows into 59,904 accepted/published observations and 700 documented exclusions, with zero rejected and duplicate rows. The aggregate payload carries source period, generated time, pipeline revision, build ID, schema versions, and quality counts.

## Exact next action

1. Commit the M2 implementation with the configured human Git identity.
2. Rebuild the authorized aggregate so `pipeline_revision` names the implementation commit.
3. Record final M2 evidence, refresh Graphify/signature, run `npm run check`, and commit the verified evidence payload.
4. Mark M2 complete and begin M3 from `.project/milestones.yml`.

## Guardrails

- Raw ZIPs and local SQLite state remain ignored and restricted.
- Current public claims remain issuance-only.
- Factor, runoff, prepayment, AI, cloud, deployment, and publication remain gated.
- Do not create a remote, push, provision, spend, deploy, or publish without the corresponding recorded approval.

## Recovery commands

```sh
npm run load:raw
npm run check
npm run serve
```

Open `http://127.0.0.1:4173` after the checks for a local preview.
