# 0003 Keep verification nondestructive

## Decision

Separate sample, test, validation, smoke, and released-payload paths so routine verification cannot overwrite the governed dashboard release.

## Why

Checks must be safe to run repeatedly. A test fixture replacing a reviewer artifact would invalidate evidence and create a misleading release.

## Alternatives rejected

One shared output path was rejected because command order could silently change the released payload.

## Not done

Verification does not rebuild authorized raw-data outputs unless an explicit load command is run.

## Changed

M1 added distinct local targets, regression tests, released-payload validation, and a static smoke path.
