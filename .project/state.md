# Current state

- Lifecycle: end-to-end refinement in progress; M3 issuance decision workflow completed
- Data authorization: project owner confirms authorized Freddie Mac issuance source-file use
- Observed coverage: December 2024 through June 2026
- Governed population: 60,604 physical rows; 59,904 accepted/published; 700 documented exclusions; 0 rejected; 0 duplicates
- Dashboard payload: 19 monthly rows and 95 mix rows; pipeline `0.3.0`; revision `c72602c3febd`; build `5c6977cfad48...`
- Mix coverage: 59,446 mapped observations; 458 explicit unmapped; 99.29% of issuance UPB mapped to official term families
- Product workflow: release health, dynamic trend findings, term-family composition, investigation prompts, methods, and evidence table
- Resilience/accessibility: loading/error/retry, payload validation, year-aware chart description, keyboard focus, forced colors, responsive layouts
- M4 readiness: fail-closed source inventory and machine-readable contract implemented; 19 issuance archives recognized, 0 approved M4 archives, contract pending, readiness blocked
- Verification: 18 Python tests, dashboard analytics tests, governed payload validator, Impeccable detector, project records, and local HTTP smoke pass
- Source control: local `main`; M3 implementation revision `c72602c3febd`; M4 intake revision `29db1f055d32`; no remote or public visibility
- Deployment: local preview only; no cloud, public host, AI service, or paid resource
- Current completed milestone: M3 — issuance decision workflow, verified 2026-08-09
- Next milestone: M4 — blocked pending authorized factor/supplemental files and approved data contract
