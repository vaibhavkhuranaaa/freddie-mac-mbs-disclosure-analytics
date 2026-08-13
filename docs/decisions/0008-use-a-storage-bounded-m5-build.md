# 0008 Use a storage-bounded M5 build

## Decision

Keep product source, contracts, documentation, and safe fixtures in this repository. Move restricted source and generated analytical data to one configurable sibling data root with four classes: canonical raw, active release, temporary build, and value-free manifests.

Retain one active generated release. Build replacements in an isolated temporary path, verify them, switch atomically, then delete superseded generated artifacts. Preserve canonical compressed source archives under the approved retention policy. Never keep permanent duplicate raw archives, conformed releases, metric stores, Graphify outputs, tool copies, or legacy delivery records.

Before the M4 v2 rebuild, benchmark a compact standard-library loan partition that keeps source-level provenance in the manifest instead of repeating it on every row. Adopt it only if it reduces generated partition storage by at least 20 percent without changing rows, lineage, correction behavior, or metric results and without increasing scan time by more than 10 percent.

## Why

Current working storage is about 37 GB: 16 GB of compressed canonical source archives and 21 GB of generated local outputs. Git is only 3.2 MB. Storage control therefore depends on generated-data lifecycle and partition width, not source-history rewriting or Git cleanup.

## Alternatives rejected

Deleting canonical raw archives would break reproducibility and the approved retention boundary. Keeping every build would consume space without adding evidence. Adding Parquet, DuckDB, or a warehouse before a local benchmark proves need would add dependencies and migration cost. Treating supplemental archives as useless would discard governed source-completeness evidence and possible future native-grain measures.

## Not done

This decision does not authorize deletion before recovery checks pass. It does not approve cloud or paid archival storage. It does not claim loan-level voluntary prepayment from monthly factors. Daily Prepayment Report files remain a separately acquired provider source.

## Changed

M5 execution now has explicit storage budgets, cleanup gates, isolated builds, a compact-partition benchmark, post-cutover deletion, and a final no-clutter acceptance gate.
