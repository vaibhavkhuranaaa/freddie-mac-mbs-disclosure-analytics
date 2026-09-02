# Decision 0010: Contract provider semantics before M4 v2

## Decision

Version the security and loan source contracts at v2 with executable Freddie Mac Disclosure Guide v6.2 rules before expanding conformed storage. Contract all 45 approved additions, including the checksum-keyed acquisition event, and keep them outside active M4 facts until the isolated M4 v2 build passes.

Security core rules apply to `fd` and retired `ar` families and are explicitly absent from supplemental `fq` and `ge` families. Loan rules apply to `fu` and retired `au` families across both observed score-schema eras. Every field records provider ID, format, code set, sentinel, range, schema window, conditional applicability, correction behavior, restriction class, release boundary, and limitation.

`First Payment Date` is the general first scheduled payment month. `Origination First Payment Date` applies only to reperforming, modified fixed-rate, and modified step-rate loans and cannot replace the general field. Delinquent-loan purchases remain unavailable because disclosed involuntary removals combine delinquency, loss mitigation, and lender repurchase.

## Why

Observed header presence proves only structural availability. It does not prove code meanings, null handling, valid ranges, family scope, timing, correction treatment, or release rights. Executable rules and safe fixtures make invalid or inapplicable values fail closed before restricted rows enter new facts.

## Alternatives rejected

- Parse every observed header immediately. Rejected because it promotes fields without semantic controls.
- Treat supplemental layouts as equivalent to core fields. Rejected because they have different native grains and no matching core attribute contract.
- Infer acquisition time from publication date, filesystem metadata, or migration time. Rejected because none records the owner's acquisition event.
- Relabel involuntary removals as delinquent-loan purchases. Rejected because the provider definition is broader.

## Not done

This decision does not expand SQLite or partition schemas, populate historical acquisition timestamps, release field-extension metrics, or approve publication. Those actions remain gated by M5.4, M5.6, owner events, and the publication gate.

## Changed

- Security and loan contracts are now v2 semantic contracts.
- A separate immutable acquisition-metadata contract defines `acquired_at` without inventing historical values.
- Contract signatures now cover semantic rules and invalidate stale inventory caches.
- Forty-five synthetic field cases exercise formats, codes, sentinels, boundaries, schema families, applicability, corrections, and release modes.
