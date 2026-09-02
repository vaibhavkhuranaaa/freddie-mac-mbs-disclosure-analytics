# Freddie Mac MBS Disclosure Analytics Data

This release contains the complete source and derived data used by the published product. Files remain in their native ZIP, gzip-compressed CSV, JSON, and SQLite formats so every published result can be traced back to the verified release.

## Contents

- `raw--*`: 125 source disclosure archives.
- `releases--*`: active issuance, M4, loan-partition, and M5 outputs.
- `manifests--*`: source inventory, active-release pointer, and storage ceiling.
- `product--dashboard.json`: derived payload used by the static product.
- `publication-manifest.json`: logical path, byte count, and SHA-256 digest for every data asset.

Release assets flatten directory separators to `--`. `publication-manifest.json` restores each logical path and provides exact integrity values.

## Verification

```sh
python3 -B scripts/prepare_m12_publication.py verify-remote \
  --manifest /path/to/publication-manifest.json \
  --repository vaibhavkhuranaaa/freddie-mac-mbs-disclosure-analytics \
  --tag data-v1
```

## Scope and limitations

This dataset supports descriptive disclosure operations and MBS analytics. It does not provide borrower decisions, investment recommendations, valuation, trading, hedging, causal inference, or certified measures for contracts marked unreleased.

The project owner attests that no additional redistribution rights are required for this publication. Source materials remain attributable to Freddie Mac, and downstream users remain responsible for reviewing applicable provider terms.

Mutable investigation records, private delivery records, credentials, temporary build files, rollback files, and SQLite WAL/shared-memory files are excluded because they are not source or derived analytical data.
