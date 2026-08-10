# Current state

- Lifecycle: implementation-ready BI product roadmap; M0–M3 completed
- Product contract: `docs/BI_PRODUCT_SPEC.md`; executable roadmap: M0–M12 in `.project/milestones.yml`
- Next milestone: M4 — approve and implement conformed monthly-security and loan-level source contracts
- Data authorization: row-level local use approved for the owner; reviewer/public redistribution not approved
- Retention: seven years from acquisition, delete earlier if authorization ends
- Governed issuance: 19 files, 2024-12 through 2026-06; 60,604 physical rows; 59,904 accepted/published; 700 documented exclusions; 0 rejected; 0 duplicate keys
- Dashboard payload: 19 monthly and 95 mix rows; pipeline `0.3.0`; mix coverage 99.29% of issuance UPB with 458 observations explicit/unmapped
- Acquired monthly security: 71 archives through applicable August/March 2026 endpoints; schemas include December 2025 FICO/VS4 and April 2026 consolidation transitions
- Acquired monthly loan-level: 35 archives (`fu` 20, `au` 15), approximately 9.1 GiB compressed; 116-column December 2025 FICO/VS4 transition verified structurally
- M4 machine state: data is present and authorized; exact fields, correction precedence, joins, dispositions, and original/latest views must be completed and approved before governed transformation output
- Target product: certified Power BI model and nine-page trust-to-investigation workflow with full authorized detail and separate reviewer boundary
- Verification: 20 Python tests over the real inventory plus dashboard analytics, released-payload validation, static artifact smoke, Graphify synchronization, and project-record checks pass for this planning revision
- Source control: branch `product/bi-dashboard-roadmap`; local Git only; no remote; GitHub authentication currently invalid
- Deployment: local only; AI, cloud, paid resources, deployment, and publication not approved
