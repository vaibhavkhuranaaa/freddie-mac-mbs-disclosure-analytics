# Current state

- Lifecycle: end-to-end refinement in progress; M3 issuance decision workflow implemented and under closure verification
- Data authorization: project owner confirms authorized Freddie Mac source-file use
- Observed coverage: December 2024 through June 2026
- Governed population: 60,604 physical rows; 59,904 accepted/published; 700 documented exclusions; 0 rejected; 0 duplicates
- Dashboard payload: 19 monthly rows and 95 mix rows; pipeline `0.3.0`; build `5c6977cfad48...`
- Mix coverage: 59,446 mapped observations; 458 explicit unmapped; 99.29% of issuance UPB mapped to official term families
- Product workflow: release health, dynamic trend findings, term-family composition, investigation prompts, methods, and evidence table
- Resilience/accessibility: loading/error/retry, payload validation, year-aware chart description, keyboard focus, forced colors, responsive layouts
- Verification: 12 Python tests, dashboard analytics tests, governed payload validator, Impeccable detector, and local HTTP smoke pass
- Source control: local `main`; no remote or public visibility
- Deployment: local preview only; no cloud, public host, AI service, or paid resource
- Current milestone: M3 — closure evidence commit
- Next milestone after closure: M4 — pending authorized factor/supplemental source acquisition and contract approval
