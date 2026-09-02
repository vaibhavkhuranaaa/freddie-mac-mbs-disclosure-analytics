# 0020. Use an ephemeral private Azure release candidate

Date: 2026-09-01

Status: accepted

## Why

M11 required evidence that the governed product could run behind cloud identity with durable investigation recovery, logs, bounded load, immutable image lineage, rollback, cost controls, and complete teardown. The approved boundary allowed the application, API, and derived product payload in Azure Central US under a five-dollar ceiling. AI and publication remained disabled.

## Decision

Deploy an ephemeral Azure Container Apps consumption environment with Microsoft Entra authentication, HTTPS-only ingress, a one-replica maximum, managed-identity image pull, Azure Container Registry, a one-GiB Azure Files recovery share, Log Analytics, and a resource-group budget.

Run SQLite on container-local storage and atomically mirror the closed database file to Azure Files after each committed write. Restore that mirror before schema initialization on startup. Keep revision mode single so only one revision receives traffic and writes the durable mirror. Pin every deployment to an immutable container digest.

After security, parity, backup, restore, observability, load, rollback, lineage, and cost checks pass, delete the resource group and temporary Entra application in the same session.

## Alternatives rejected

The following approaches were considered and intentionally not done for M11.

## Not done

- Running SQLite directly on Azure Files. Live trials produced repeatable lock failures even with one replica; SMB is retained only as a durable byte mirror.
- Adding a managed relational database. The release candidate does not need that cost or operational surface at its measured workload.
- Leaving a permanent private environment. M11 measures scaled deployment evidence, not a continuing hosted release.
- Enabling the cited assistant. No additional AI runtime or provider-call approval exists for M11.
- Moving source archives or row-level facts. They are outside the approved M11 data boundary.

## Changed

The release candidate passed every M11 check and was torn down. No live cloud endpoint remains. A future hosted release can reuse the templates, but must receive a new deployment and budget approval. If investigation write volume or replica count exceeds the single-writer boundary, replace the file mirror with an approved managed transactional store.
