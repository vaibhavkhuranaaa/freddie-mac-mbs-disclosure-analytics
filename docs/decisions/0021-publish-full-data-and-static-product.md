# 0021 - Publish full data and static product

## Decision

Publish the verified browser product with GitHub Pages and publish every selected source and derived analytical artifact as GitHub Release assets under tag `data-v1`. Keep data outside Git history. Use one integrity manifest to map flattened release-asset names back to logical paths and verify every remote size and digest.

The project owner approved M12 and attested that no additional redistribution rights are required.

## Why

The static product needs no public API, server, database, identity system, or paid runtime. GitHub Releases supports the complete payload because it has fewer than 1,000 assets and every asset is under 2 GiB. One provider keeps source, live product, data, release evidence, and rollback history together at zero recurring cost.

## Alternatives rejected

- Commit data to Git or Git LFS: rejected because repository history is the wrong boundary for 43 GiB of immutable analytical artifacts.
- Deploy the authenticated semantic API publicly: rejected because the static decision workflow needs no mutation surface or request-cost exposure.
- Use a second dataset host: rejected because GitHub Releases already meets the measured file-count, file-size, total-size, and bandwidth boundaries.

## Not done

M12 does not enable the cited assistant, publish investigation records, expose arbitrary SQL or row APIs, claim production availability, or complete parked Power BI milestone M6.

## Changed

M12 adds deterministic publication selection, local and remote integrity verification, a static Pages deployment, complete dataset documentation, a public data-release link, and portfolio release contracts. Publication uses the owner-attested rights position while retaining source attribution and a downstream provider-terms warning.
