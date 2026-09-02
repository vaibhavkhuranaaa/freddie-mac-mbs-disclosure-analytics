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

export function validateSemanticPayload(semantic) {
  if (!semantic) return null;
  if (semantic.schema_version !== 1 || !Array.isArray(semantic.series) || !Array.isArray(semantic.concentration)) {
    throw new Error("The portfolio payload is missing required semantic sections.");
  }
  if (semantic.series.length < 2) throw new Error("At least two portfolio periods are required.");
  let previous = "";
  for (const row of semantic.series) {
    if (!monthPattern.test(row.month) || row.month <= previous) throw new Error("Portfolio observations are not ordered correctly.");
    for (const key of ["loan_count", "loan_upb", "average_loan_balance", "delinquency_30_rate", "delinquency_60_rate", "delinquency_90_rate", "modification_rate", "correction_count"]) {
      if (!Number.isFinite(row[key]) || row[key] < 0) throw new Error(`Portfolio observation ${row.month} has an invalid ${key}.`);
    }
    previous = row.month;
  }
  if (semantic.coverage?.period_start !== semantic.series[0].month || semantic.coverage?.period_end !== semantic.series.at(-1).month) {
    throw new Error("The portfolio coverage metadata does not reconcile.");
  }
  if (!semantic.release_id || !semantic.metadata?.snapshot_sha256 || semantic.correction_view !== "latest") {
    throw new Error("The portfolio release provenance is incomplete.");
  }
  if (semantic.quality?.status !== "pass" || !semantic.quality.detail) {
    throw new Error("The portfolio quality status is incomplete.");
  }
  if (semantic.comparability?.status !== "unavailable" || !semantic.comparability.detail) {
    throw new Error("The portfolio comparability status is incomplete.");
  }
  if (!semantic.generated_at || Number.isNaN(Date.parse(semantic.generated_at))) {
    throw new Error("The portfolio refresh timestamp is invalid.");
  }
  const evidenceMetrics = semantic.evidence?.metrics;
  const requiredEvidence = ["issuance_change", "issuance_peak", "issuance_mix", "outstanding_upb", "modification_rate", "seller_concentration", "servicer_concentration", "state_concentration"];
  if (!evidenceMetrics || requiredEvidence.some((key) => !evidenceMetrics[key]?.provenance?.length)) {
    throw new Error("The portfolio evidence pointers are incomplete.");
  }
  if (!semantic.evidence?.transitions?.rows?.length || !semantic.evidence.transitions.provenance?.length) {
    throw new Error("The portfolio transition evidence is incomplete.");
  }
  return semantic;
}

export function semanticFindings(semantic) {
  const latest = semantic.series.at(-1);
  const prior = semantic.series.at(-2);
  const upbChange = percentChange(latest.loan_upb, prior.loan_upb);
  const modificationChange = (latest.modification_rate - prior.modification_rate) * 10000;
  const concentrationLeader = [...semantic.concentration].sort((a, b) => b.top_10_share - a.top_10_share)[0];
  const concentrationName = concentrationLeader.entity[0].toUpperCase() + concentrationLeader.entity.slice(1);
  return [
    {
      title: `Outstanding UPB ${upbChange >= 0 ? "increased" : "decreased"} from the prior month`,
      detail: `${money(latest.loan_upb)}, a ${Math.abs(upbChange).toFixed(2)}% ${upbChange >= 0 ? "increase" : "decrease"} from ${monthLabel(prior.month)}.`,
      action: "Compare loan count and average balance before assigning a balance investigation.",
    },
    {
      title: `Modification rate moved ${Math.abs(modificationChange).toFixed(2)} basis points`,
      detail: `${(latest.modification_rate * 100).toFixed(3)}% in ${monthLabel(latest.month)}. Direction alone is not a quality judgment.`,
      action: "Review the disclosed modification population and correction count for the same period.",
    },
    {
      title: `${concentrationName} has the highest top-ten share`,
      detail: `${(concentrationLeader.top_10_share * 100).toFixed(1)}% of current UPB, with HHI ${concentrationLeader.hhi.toFixed(4)}.`,
      action: `Open ${concentrationLeader.entity} evidence before treating concentration as material.`,
    },
  ];
}

export function buildInvestigationPayload(semantic, evidenceId, fields) {
  const evidence = semantic?.evidence?.metrics?.[evidenceId];
  if (!evidence) throw new Error(`Evidence signal is unavailable: ${evidenceId}.`);
  for (const key of ["title", "owner", "priority", "summary"]) {
    if (!String(fields[key] ?? "").trim()) throw new Error(`${key} is required.`);
  }
  return {
    title: fields.title.trim(),
    owner: fields.owner.trim(),
    priority: fields.priority,
    status: "open",
    summary: fields.summary.trim(),
    release_id: semantic.release_id,
    report_period: evidence.report_period,
    correction_view: evidence.correction_view,
    metric_version: semantic.metadata.metric_version,
    filter_context: { view: "portfolio", evidence_id: evidenceId },
    evidence: [
      {
        contract_id: evidence.contract_id,
        component: evidence.component,
        period: evidence.report_period,
        correction_view: evidence.correction_view,
        provenance: evidence.provenance,
      },
    ],
  };
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
