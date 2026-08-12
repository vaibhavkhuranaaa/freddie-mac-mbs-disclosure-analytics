# 0007 Release the first approved M5 methodologies

## Decision

Release HHI concentration, 30+/60+/90+ delinquency rates, modification rate, and involuntary-removal share for restricted local use at formula version `m5.1.0`.

HHI uses complete visible state, seller, or servicer components on separate count and UPB bases. Delinquency thresholds exclude the explicit missing-days population and keep count and UPB bases separate. Modification rate uses the matching active loan population. Involuntary-removal share uses current-month disclosed removals over the adjacent prior-month active disclosed loan count or security UPB, with original and latest correction views separate.

## Why

These four methodologies have approved inputs in the current M4 facts, exact additive components, deterministic denominators, golden edge cases, and independent real-data reconciliation. They can advance M5 without changing or rebuilding the M4 source contract.

## Alternatives rejected

Releasing all approved methodologies at once would require guessing missing principal movements, cohort vintage, transition windows, comparability rules, or quality weights. Treating the approved M4-v2 field list as parsed data would bypass provider code, sentinel, range, and applicability controls.

## Not done

The remaining approved methodologies stay unreleased until their source and rule prerequisites pass. The v2 source fields remain outside conformed facts until exact provider rules and safe fixtures are implemented. Loan vintage and delinquent-loan-purchase inputs remain deferred. Reviewer, public, cloud, and deployment release modes remain unapproved.

## Changed

The supported M5 catalog boundary increases from 23 to 27 contracts. The metric engine emits and independently verifies the four derived measures while preserving the supported-contract/released-contract invariant.
