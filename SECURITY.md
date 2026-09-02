# Security Policy

## System and Scope

This repository contains Freddie Mac disclosure ingestion, validation,
analytics, a static dashboard, an investigation store, an authenticated
semantic API, optional cited-assistant code, and Azure deployment templates.

Security review covers application code, source and metric contracts,
investigation and audit integrity, API authorization, AI-provider boundaries,
deployment templates, secrets handling, and protection of external data roots.
There is currently no live cloud endpoint.

## Threat Model and Trust Boundaries

Treat source archives, uploaded or downloaded files, HTTP inputs, actor
headers, AI-provider output, and deployment parameters as attacker-controlled.
Trusted identities are the local bearer-token holder on loopback or a principal
authenticated by the configured Microsoft Entra platform boundary.

Raw archives, row-level facts, databases, credentials, and private operational
records remain outside the public repository unless separately approved for
publication.

## Security Invariants

- Unknown, malformed, duplicate, mismatched, or unsupported source data must
  fail closed before publication.
- Protected API routes and every mutation require authorization.
- Cloud identity headers are trusted only behind the checked-in Entra
  `authConfigs` boundary; cloud audit actors come from the trusted principal.
- Arbitrary SQL, unrestricted raw-row routes, and mutation of release
  provenance or immutable investigation evidence are prohibited.
- Secrets must use environment variables or secure deployment parameters and
  must never enter source control, responses, request audit, or logs.
- Request bodies remain bounded to 64 KiB.
- AI is disabled by default. When enabled by separate approval, only
  allowlisted derived context may leave the repository, and provider output
  must pass deterministic citation, privacy, and safety validation.
- HTTPS and fail-closed authentication are required for external deployment.
- The SQLite recovery-mirror design permits one active writer and one replica
  maximum. Scaling beyond that boundary requires an approved transactional
  store.

## Reportable Findings and Severity Context

Report authorization bypass, credential disclosure, unauthorized source or
row-level data exposure, arbitrary query execution, provenance or audit
tampering, unsafe AI-context disclosure, path traversal, injection, deployment
misconfiguration, or realistic integrity and availability failures.

Unauthenticated mutation, material credential compromise, or exposure of
unapproved row-level data is high or critical depending on reach and impact.
Actor spoofing, durable audit corruption, and remotely exploitable resource
exhaustion are security findings even when analytical outputs remain correct.

## Out of Scope, Exclusions, and Accepted Risk

Ordinary metric-definition or business-interpretation disagreements without a
security or integrity consequence are not security findings.

The local shared bearer token is accepted only for loopback development.
The public application health route is acceptable on loopback; exposing the
application directly to the internet without platform authentication is not.

The single-writer SQLite design is accepted for the measured one-replica
release-candidate boundary. Concurrency or durability failures caused by
deploying it outside that boundary remain reportable.

No live M11 infrastructure exists. Findings requiring a currently running M11
endpoint are not presently reachable, but reusable application and template
weaknesses remain in scope.

## Known Limitations and Compensating Controls

Tests and prior release-candidate evidence demonstrate intended controls but do
not prove future deployments are secure. Every deployment requires fresh
identity, budget, recovery, rollback, observability, and teardown approval.

Complete row-level publication requires the owner-recorded rights position,
security review, exact artifact lineage, and publication approval. M12 uses a
read-only static site and immutable release assets; no public mutation API or
cost-bearing runtime is enabled.
