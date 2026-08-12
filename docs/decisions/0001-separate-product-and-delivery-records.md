# 0001 Separate product and delivery records

## Decision

Keep product code, value-free machine contracts, public documentation, and safe fixtures in this repository. Keep approvals, milestone state, restricted evidence, cost records, and handoff material in a private sibling delivery workspace.

## Why

Product artifacts must remain reproducible while private operational records and restricted-data context stay outside any future public repository.

## Alternatives rejected

Keeping all records in a tracked `.project` folder would expose internal delivery state. Moving machine contracts out of the product would break validation and metric reproduction.

## Not done

Git history was not rewritten. Publication, remote creation, and public visibility were not authorized.

## Changed

Source and metric contracts now live under `contracts/`. Public documents reference stable product paths. Delivery records live in the private sibling workspace.
