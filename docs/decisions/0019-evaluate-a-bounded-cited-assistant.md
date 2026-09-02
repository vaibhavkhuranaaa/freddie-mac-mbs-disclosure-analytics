# 0019 - Evaluate a bounded cited assistant

## Decision

Accept the optional cited assistant at the M10 boundary. The application classifies supported intents before provider input, sends only canonical questions and an allowlisted released-evidence catalog, requires exact evidence selection, and renders every user-facing factual statement itself. Advice, causal, unsupported-comparison, identifier-bearing, and unknown intents fail closed before inference.

## Why

The six-case challenger reached a 1.0 decision-ready rate against the 0.8333 manual-navigation baseline, with 1.0 citation validity, safety, and privacy rates. It reduced the fixed workflow from twelve steps to six, recorded 1.703-second p95 latency, and stayed at $0.0036135 cumulative paid-tier-equivalent cost under the $0.01 gate.

## Alternatives rejected

An unrestricted conversational interface was rejected because prose and citations could drift from released facts. Sending original user questions was rejected because arbitrary text could contain identifiers. Letting the provider calculate or rewrite values was rejected because exact evidence could be altered. A general query or SQL surface remains prohibited.

## Not done

M10 does not deploy or publish the assistant, enable provider search or grounding, send raw rows, accept borrower, loan, or security identifiers, or provide investment, valuation, trading, hedging, lending, causal, or certified adjacent-period recommendations. The six fixed cases are not a general model benchmark.

## Changed

Added the cited-assistant contract, Gemini 3.5 Flash-Lite adapter, deterministic intent and refusal boundary, authenticated opt-in API route, fixed evaluation fixture, evidence-bound report verifier, hard request/token/cost caps, and environment-variable contract. The feature remains disabled by default.
