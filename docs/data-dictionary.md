# Data dictionary

## Restricted local tables

### `monthly_security`

| Field | Meaning | Unit/type | Public? | Limitation |
| --- | --- | --- | --- | --- |
| `report_month` | Validated source period | `YYYY-MM` | Aggregate only | Derived from filename |
| `security_id` | Freddie Mac security identifier | Text | No | Restricted business key |
| `security_type` | Source Prefix | Text | Approved aggregate only | Product taxonomy not yet approved |
| `issuance_upb` | Investor security UPB at issuance | US dollars | Aggregate only | Describes issuance, not later balance runoff |
| `current_upb` | Current UPB carried in the issuance source | US dollars | Aggregate only | Not a longitudinal performance measure in the current source |
| `factor` | Security factor in the issuance source | Ratio `(0,1]` | Aggregate only | Commonly 1.0 at issuance; not a performance insight yet |
| `cpr_pct` | Placeholder used only by the sample schema | Percent | No current public claim | Official issuance ingestion sets this to 0 and does not claim CPR |
| `published_files` | Sample-only disclosure count | Integer | No current public claim | Official issuance ingestion sets this to 1 |
| `expected_files` | Sample-only expected count | Integer | No current public claim | Official issuance ingestion sets this to 1 |
| `release_lag_days` | Sample-only lag | Days | No current public claim | Official issuance ingestion sets this to 0 |
| `revision_flag` | Source correction indicator | Boolean integer | Aggregate count | Meaning is limited to the source indicator |
| `source_file` | Originating local filename | Text | No | Local provenance only |
| `source_row` | Originating row number | Integer | No | Local investigation aid |
| `schema_version` | Reviewed input contract version | Text | Safe metadata | Does not replace source documentation |

### `source_manifest`

| Field group | Meaning |
| --- | --- |
| Identity | Source file, report period, SHA-256, load time, pipeline version, schema version |
| Reconciliation | Input, accepted, excluded, rejected, duplicate, quarantined, and published counts |
| Gate | `quality_status` is `pass` or `fail`; only all-pass manifests can publish |

### `quality_issue`

Stores source file, row number, severity, rule code, and a value-free explanation. Informational exclusions remain visible; error events block publication.

## Public aggregate payload

| Field | Meaning | Unit/type |
| --- | --- | --- |
| `month` | Reporting month | `YYYY-MM` |
| `security_count` | Accepted issued securities | Count |
| `issuance_upb` | Sum of accepted issuance UPB | US dollars |
| `current_upb` | Sum of current UPB in accepted issuance rows | US dollars |
| `average_factor` | Unweighted mean source factor | Ratio |
| `correction_count` | Sum of source correction flags | Count |
| `metadata.period_start/end` | Aggregate coverage | `YYYY-MM` |
| `metadata.generated_at` | Build time | UTC ISO-8601 |
| `metadata.pipeline_version/revision` | Transformation lineage | Text |
| `metadata.build_id` | Deterministic source/pipeline fingerprint | SHA-256 |
| `metadata.schema_versions` | Reviewed schemas used | List of text values |
| `metadata.quality` | Reconciled release counts and pass status | Object |
| `mix[].product_group` | Approved official term-family group or explicit unmapped group | Text |
| `mix[].security_count` | Accepted securities in month/group | Count |
| `mix[].issuance_upb` | Issuance UPB in month/group | US dollars |
| `mix[].issuance_share` | Group issuance UPB / monthly issuance UPB | Ratio `(0,1]` |
| `metadata.mix` | Taxonomy version/source plus mapped and unmapped coverage | Object |
