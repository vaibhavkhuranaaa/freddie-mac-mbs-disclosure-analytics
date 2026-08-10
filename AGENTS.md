# Project delivery rules

## Read first

Read `PROJECT.md`, `.project/architecture.md`, `.project/milestones.yml`, `.project/state.md`, and `.project/handoff.md` before editing. Complete the first unblocked milestone unless the project owner directs otherwise.

## Rules

- The project owner is an authorized Freddie Mac user. Use the official source files placed in `data/raw/` for this project; do not substitute synthetic data for the reviewer-facing dashboard.
- Preserve unrelated work and never overwrite a released dashboard with a test fixture.
- Keep the implementation precise: distinguish implemented issuance monitoring from planned factor, runoff, prepayment, and supplemental analytics.
- Apply `DESIGN.md` to every user-facing change.
- Keep secrets outside source; commit variable names only in `.env.example`.
- Use conventional commits and configured human Git identity. Never add AI/model author or co-author trailers, or AI/model names in Git branch names.
- Do not create paid resources, change public visibility, deploy, roll back, or publish without explicit human approval recorded in `.project/approvals.yml`.
- Update architecture, evidence, state, handoff, and Graphify artifacts when verified facts change.
- Run the declared verification commands before claiming a milestone is complete.
