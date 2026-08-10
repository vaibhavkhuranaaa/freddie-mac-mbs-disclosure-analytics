import assert from "node:assert/strict";
import { deriveFindings, latestMix, monthLabel, percentChange, validatePayload } from "../app/analytics.js";

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

console.log("Dashboard analytics tests: pass");
