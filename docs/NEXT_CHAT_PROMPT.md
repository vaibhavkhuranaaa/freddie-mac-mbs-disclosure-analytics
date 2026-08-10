# Next-chat kickoff prompt

Copy and paste the following into a new chat:

```text
Continue work on /Users/vaibhavkhurana/Development/repos/freddie-mac-mbs-disclosure-analytics.

Read AGENTS.md, PROJECT.md, README.md, .project/architecture.md, .project/milestones.yml, .project/evidence.yml, .project/state.md, .project/handoff.md, docs/HIRING_MANAGER_REVIEW.md, and graphify-out/GRAPH_REPORT.md before editing.

Context: I am an authorized Freddie Mac user. The project already has 19 official month-end issuance files (Dec 2024–Jun 2026), 59,904 loaded security observations, a local SQLite pipeline, and a local dashboard at http://127.0.0.1:4173. It is an issuance-monitoring case study; do not claim runoff, prepayment, balance movement, timeliness, or supplemental analytics until their data sources are integrated and tested. Do not use synthetic data in the recruiter-facing dashboard.

Complete M2 in .project/milestones.yml end to end:
1. Add accepted, rejected, and duplicate accounting for every official source file.
2. Add strict official ZIP success/failure tests, including malformed layouts and source-period rules.
3. Add safe provenance and quality metadata to the released monthly aggregate payload.
4. Preserve M1: sample/test commands must never overwrite app/data/dashboard.json, and npm run check must validate the released payload.
5. Run the full verification path against the real local data and keep the preview available.
6. Update Graphify incrementally after changes, then update .project/evidence.yml, .project/state.md, and .project/handoff.md with verified facts.

Do not deploy, publish, create paid resources, or change public visibility unless I explicitly ask. Use apply_patch for edits, preserve unrelated files, and give me the final localhost preview link plus a concise verification summary.
```
