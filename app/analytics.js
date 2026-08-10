const monthPattern = /^\d{4}-(0[1-9]|1[0-2])$/;

export function monthLabel(month, style = "long") {
  const options = style === "short"
    ? { month: "short", year: "2-digit", timeZone: "UTC" }
    : { month: "short", year: "numeric", timeZone: "UTC" };
  return new Intl.DateTimeFormat("en-US", options).format(new Date(`${month}-01T00:00:00Z`));
}

export function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function percentChange(now, then) {
  if (!Number.isFinite(now) || !Number.isFinite(then) || then === 0) return null;
  return (now / then - 1) * 100;
}

export function validatePayload(payload) {
  if (!payload || !Array.isArray(payload.months) || !Array.isArray(payload.mix) || !payload.metadata) {
    throw new Error("The release payload is missing required sections.");
  }
  if (payload.months.length < 2) throw new Error("At least two monthly observations are required.");
  let previous = "";
  for (const row of payload.months) {
    if (!monthPattern.test(row.month) || row.month <= previous) throw new Error("Monthly observations are not ordered correctly.");
    for (const key of ["security_count", "issuance_upb", "current_upb", "average_factor", "correction_count"]) {
      if (!Number.isFinite(row[key])) throw new Error(`Monthly observation ${row.month} has an invalid ${key}.`);
    }
    previous = row.month;
  }
  if (payload.metadata.quality?.status !== "pass") throw new Error("The release payload did not pass its source-quality gate.");
  if (payload.metadata.period_start !== payload.months[0].month || payload.metadata.period_end !== payload.months.at(-1).month) {
    throw new Error("The release period metadata does not reconcile.");
  }
  return payload;
}

export function latestMix(payload) {
  const month = payload.months.at(-1).month;
  return payload.mix.filter((row) => row.month === month).sort((a, b) => b.issuance_upb - a.issuance_upb);
}

export function deriveFindings(payload) {
  const months = payload.months;
  const latest = months.at(-1);
  const prior = months.at(-2);
  const peak = months.reduce((best, row) => row.issuance_upb > best.issuance_upb ? row : best);
  const trough = months.reduce((best, row) => row.issuance_upb < best.issuance_upb ? row : best);
  const change = percentChange(latest.issuance_upb, prior.issuance_upb);
  const mix = latestMix(payload);
  const leader = mix[0];
  return [
    {
      title: `${monthLabel(latest.month)} moved ${change >= 0 ? "above" : "below"} the prior month`,
      detail: `${money(latest.issuance_upb)} of issuance, ${Math.abs(change).toFixed(1)}% ${change >= 0 ? "higher" : "lower"} than ${monthLabel(prior.month)}.`,
      action: "Compare security count and product mix before treating the change as an activity shift.",
    },
    {
      title: `${monthLabel(peak.month)} is the observed high`,
      detail: `${money(peak.issuance_upb)} versus ${money(trough.issuance_upb)} in the observed low, ${monthLabel(trough.month)}.`,
      action: "Check source comparability and surrounding months before investigating an operational cause.",
    },
    {
      title: `${leader.product_group} leads the latest mix`,
      detail: `${(leader.issuance_share * 100).toFixed(1)}% of ${monthLabel(latest.month)} issuance UPB.`,
      action: payload.metadata.mix.unmapped_observation_count
        ? "Review the explicit Other / Unmapped population before drawing product-level conclusions."
        : "Use the term-family mix to localize the latest change.",
    },
  ];
}
