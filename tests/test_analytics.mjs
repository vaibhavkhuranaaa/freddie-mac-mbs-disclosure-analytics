import assert from "node:assert/strict";
import { buildInvestigationPayload, deriveFindings, latestMix, monthLabel, percentChange, semanticFindings, validatePayload, validateSemanticPayload } from "../app/analytics.js";

const payload = {
  months: [
    { month: "2025-12", security_count: 2, issuance_upb: 100, current_upb: 100, average_factor: 1, correction_count: 0 },
    { month: "2026-01", security_count: 3, issuance_upb: 150, current_upb: 150, average_factor: 1, correction_count: 0 },
  ],
  mix: [
    { month: "2025-12", product_group: "Other / Unmapped prefix", security_count: 2, issuance_upb: 100, issuance_share: 1 },
    { month: "2026-01", product_group: "30-year UMBS / Supers family", security_count: 2, issuance_upb: 120, issuance_share: .8 },
    { month: "2026-01", product_group: "Other / Unmapped prefix", security_count: 1, issuance_upb: 30, issuance_share: .2 },
  ],
  metadata: {
    period_start: "2025-12",
    period_end: "2026-01",
    quality: { status: "pass" },
    mix: { unmapped_observation_count: 3 },
  },
};

assert.equal(validatePayload(payload), payload);
assert.equal(percentChange(150, 100), 50);
assert.equal(percentChange(10, 0), null);
assert.equal(monthLabel("2026-01"), "Jan 2026");
assert.equal(latestMix(payload)[0].product_group, "30-year UMBS / Supers family");
assert.equal(deriveFindings(payload).length, 3);
assert.throws(() => validatePayload({ ...payload, months: [] }), /At least two/);
assert.throws(() => validatePayload({ ...payload, metadata: { ...payload.metadata, quality: { status: "fail" } } }), /quality gate/);

const semantic = {
  schema_version: 1,
  release_id: "release-test",
  generated_at: "2026-08-25T12:00:00Z",
  correction_view: "latest",
  quality: { status: "pass", detail: "Verified release." },
  comparability: { status: "unavailable", detail: "Descriptive deltas only." },
  coverage: { period_start: "2026-01", period_end: "2026-02", period_count: 2 },
  metadata: { snapshot_sha256: "abc" },
  series: [
    { month: "2026-01", loan_count: 10, loan_upb: 100, average_loan_balance: 10, delinquency_30_rate: 0, delinquency_60_rate: 0, delinquency_90_rate: 0, modification_rate: .01, correction_count: 0 },
    { month: "2026-02", loan_count: 12, loan_upb: 120, average_loan_balance: 10, delinquency_30_rate: 0, delinquency_60_rate: 0, delinquency_90_rate: 0, modification_rate: .02, correction_count: 0 },
  ],
  concentration: [{ entity: "seller", top_10_share: .5, top_10_upb: 60, portfolio_upb: 120, hhi: .04 }],
  evidence: {
    metrics: Object.fromEntries(["issuance_change", "issuance_peak", "issuance_mix", "outstanding_upb", "modification_rate", "seller_concentration", "servicer_concentration", "state_concentration"].map((key) => [key, { contract_id: `${key}_contract`, component: `${key}_component`, report_period: "2026-02", correction_view: "latest", provenance: [{ source_file: "test.zip" }] }])),
    transitions: { rows: [{ member: "Current to Current" }], provenance: [{ source_file: "test.zip" }] },
  },
};
assert.equal(validateSemanticPayload(semantic), semantic);
assert.equal(semanticFindings(semantic).length, 3);
assert.throws(() => validateSemanticPayload({ ...semantic, release_id: "" }), /provenance/);
const investigation = buildInvestigationPayload(semantic, "servicer_concentration", { title: "Review servicer concentration", owner: "ops", priority: "high", summary: "Validate the top-ten composition." });
assert.equal(investigation.release_id, "release-test");
assert.equal(investigation.evidence[0].component, "servicer_concentration_component");
assert.throws(() => buildInvestigationPayload(semantic, "missing", { title: "x", owner: "x", priority: "high", summary: "x" }), /unavailable/);

console.log("Dashboard analytics tests: pass");
