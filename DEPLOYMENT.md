# Deployment decision record

## Current state

The dashboard runs locally at `http://127.0.0.1:4173`. A local Git repository now provides revision lineage, but no remote, public hosting, account connection, or paid resource has been created.

## Deployment-ready work

Before public deployment, complete the P0 and P1 milestones in `.project/milestones.yml`:

1. Complete the remaining M3–M9 product, analytical, security, and release-candidate gates.
2. Choose and approve the exact aggregate release payload; raw files and security-level rows are prohibited.
3. Approve a host, expected visibility, cost ceiling, domain, screenshots, and teardown procedure.

## Local preview

```sh
npm run load:raw
npm run check
npm run serve
```

## Hosting option

`netlify.toml` is included for a no-build static deployment of `app/`. Hosting remains a human decision; this document does not authorize a deployment or publication.

## Release verification

CI now runs the complete local `npm run check` path, including tests, released-payload validation, static preview smoke, and project-record checks. Deployment remains incomplete until the deployed revision, payload checksum, source period, approvals, and verified live URL are recorded.
