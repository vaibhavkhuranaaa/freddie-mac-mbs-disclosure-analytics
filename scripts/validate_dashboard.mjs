import { readFile } from "node:fs/promises";

const source = process.argv[2] ?? new URL("../app/data/dashboard.json", import.meta.url);
const payload = JSON.parse(await readFile(source, "utf8"));
const monthPattern = /^\d{4}-(0[1-9]|1[0-2])$/;
const semverPattern = /^\d+\.\d+\.\d+$/;
const sha256Pattern = /^[a-f0-9]{64}$/;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function isNonNegativeInteger(value) {
  return Number.isInteger(value) && value >= 0;
}

assert(payload && typeof payload === "object" && !Array.isArray(payload), "Dashboard payload must be an object.");
assert(Array.isArray(payload.months) && payload.months.length >= 2, "Dashboard payload needs at least two monthly rows.");
assert(payload.metadata && typeof payload.metadata === "object" && !Array.isArray(payload.metadata), "Dashboard payload needs metadata.");

const months = new Set();
let previousMonth = "";
let observationCount = 0;
for (const row of payload.months) {
  assert(row && typeof row === "object" && !Array.isArray(row), "Each monthly row must be an object.");
  assert(typeof row.month === "string" && monthPattern.test(row.month), `Invalid month: ${row.month ?? "unknown"}.`);
  assert(!months.has(row.month), `Duplicate month: ${row.month}.`);
  assert(row.month > previousMonth, `Months must be in ascending order: ${row.month}.`);
  months.add(row.month);
  previousMonth = row.month;

  for (const key of ["security_count", "issuance_upb", "current_upb", "average_factor", "correction_count"]) {
    assert(isFiniteNumber(row[key]), `Missing or invalid ${key} for ${row.month}.`);
  }
  assert(Number.isInteger(row.security_count) && row.security_count > 0, `security_count must be a positive integer for ${row.month}.`);
  assert(row.issuance_upb > 0, `issuance_upb must be positive for ${row.month}.`);
  assert(row.current_upb >= 0 && row.current_upb <= row.issuance_upb, `current_upb is out of range for ${row.month}.`);
  assert(row.average_factor > 0 && row.average_factor <= 1, `average_factor is out of range for ${row.month}.`);
  assert(Number.isInteger(row.correction_count) && row.correction_count >= 0, `correction_count must be a non-negative integer for ${row.month}.`);
  observationCount += row.security_count;
}

const metadata = payload.metadata;
assert(Number.isInteger(metadata.observation_count) && metadata.observation_count === observationCount, "metadata.observation_count must equal the monthly security-count total.");
assert(Number.isInteger(metadata.source_file_count) && metadata.source_file_count > 0, "metadata.source_file_count must be a positive integer.");
assert(metadata.period_start === payload.months[0].month, "metadata.period_start must match the first month.");
assert(metadata.period_end === payload.months.at(-1).month, "metadata.period_end must match the last month.");
assert(typeof metadata.generated_at === "string" && !Number.isNaN(Date.parse(metadata.generated_at)), "metadata.generated_at must be an ISO timestamp.");
assert(typeof metadata.pipeline_version === "string" && semverPattern.test(metadata.pipeline_version), "metadata.pipeline_version must use semantic versioning.");
assert(typeof metadata.pipeline_revision === "string" && metadata.pipeline_revision.length > 0, "metadata.pipeline_revision is required.");
assert(typeof metadata.build_id === "string" && sha256Pattern.test(metadata.build_id), "metadata.build_id must be a SHA-256 value.");
assert(Array.isArray(metadata.schema_versions) && metadata.schema_versions.length > 0, "metadata.schema_versions must be a non-empty array.");
assert(new Set(metadata.schema_versions).size === metadata.schema_versions.length, "metadata.schema_versions cannot contain duplicates.");
assert(metadata.schema_versions.every((value) => typeof value === "string" && value.length > 0), "Every schema version must be a non-empty string.");

const quality = metadata.quality;
assert(quality && typeof quality === "object" && !Array.isArray(quality), "metadata.quality is required.");
assert(quality.status === "pass", "Released payload quality status must be pass.");
for (const key of ["input_count", "accepted_count", "excluded_count", "rejected_count", "duplicate_count", "quarantined_count", "published_count"]) {
  assert(isNonNegativeInteger(quality[key]), `metadata.quality.${key} must be a non-negative integer.`);
}
assert(quality.input_count === quality.accepted_count + quality.excluded_count + quality.rejected_count + quality.duplicate_count, "Input quality counts do not reconcile.");
assert(quality.quarantined_count === quality.rejected_count + quality.duplicate_count, "Quarantine quality counts do not reconcile.");
assert(quality.accepted_count === observationCount, "Accepted count must equal the published observation count.");
assert(quality.published_count === quality.accepted_count, "Published count must equal accepted count.");

console.log(`Dashboard payload validation: pass (${payload.months.length} monthly rows, ${observationCount.toLocaleString("en-US")} observations, build ${metadata.build_id.slice(0, 12)}).`);
