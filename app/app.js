import { buildInvestigationPayload, deriveFindings, latestMix, money, monthLabel, percentChange, semanticFindings, validatePayload, validateSemanticPayload } from "./analytics.js";

const statusPanel = document.querySelector("#app-status");
const dashboard = document.querySelector("#dashboard-content");
const retryButton = document.querySelector("#retry");
let semanticState = null;
let caseCredentials = null;

const evidenceLabels = {
  issuance_change: "Latest issuance movement",
  issuance_peak: "Observed issuance high",
  issuance_mix: "Latest issuance composition",
  outstanding_upb: "Outstanding UPB movement",
  modification_rate: "Modification rate movement",
  seller_concentration: "Seller concentration",
  servicer_concentration: "Servicer concentration",
  state_concentration: "State concentration",
};

function setStatus(kind, title, detail) {
  statusPanel.dataset.kind = kind;
  statusPanel.querySelector("strong").textContent = title;
  statusPanel.querySelector("span").textContent = detail;
  statusPanel.hidden = false;
  retryButton.hidden = kind !== "error";
}

function appendFinding(container, finding) {
  const article = document.createElement("article");
  const title = document.createElement("strong");
  const detail = document.createElement("p");
  const action = document.createElement("small");
  title.textContent = finding.title;
  detail.textContent = finding.detail;
  action.textContent = `Investigate: ${finding.action}`;
  article.append(title, detail, action);
  container.append(article);
}

function percent(value, digits = 2) {
  return `${(value * 100).toFixed(digits)}%`;
}

function deltaNote(now, then, format = (value) => `${value.toFixed(2)}%`) {
  const delta = percentChange(now, then);
  if (delta === null) return "No valid prior-period comparison";
  return `${delta >= 0 ? "+" : ""}${format(delta)} vs prior month`;
}

function renderSeriesChart(rows, metric, target, label, format) {
  const values = rows.map((row) => row[metric]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min || 1) * 0.18;
  const width = 720;
  const x = (index) => 42 + index * 650 / (rows.length - 1);
  const y = (value) => 22 + (max + padding - value) * 196 / (max - min + padding * 2);
  const labelEvery = Math.ceil(rows.length / 7);
  const chart = document.querySelector(target);
  chart.setAttribute("aria-label", `${label} by month from ${monthLabel(rows[0].month)} through ${monthLabel(rows.at(-1).month)}.`);
  chart.innerHTML = `<svg viewBox="0 0 ${width} 260" aria-hidden="true" focusable="false"><polyline class="chart-line" points="${rows.map((row, index) => `${x(index)},${y(row[metric])}`).join(" ")}"/>${rows.map((row, index) => `<circle class="chart-point" cx="${x(index)}" cy="${y(row[metric])}" r="4"><title>${monthLabel(row.month)}: ${format(row[metric])}</title></circle>${index % labelEvery === 0 || index === rows.length - 1 ? `<text class="chart-label" text-anchor="middle" x="${x(index)}" y="248">${monthLabel(row.month, "short")}</text>` : ""}`).join("")}</svg>`;
}

function renderChart(payload, metric) {
  const settings = {
    issuance_upb: ["Issuance UPB", money],
    security_count: ["Issued securities", (value) => value.toLocaleString("en-US")],
  };
  const [name, format] = settings[metric];
  const rows = payload.months;
  const values = rows.map((row) => row[metric]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min || 1) * 0.18;
  const width = 720;
  const x = (index) => 42 + index * 650 / (rows.length - 1);
  const y = (value) => 22 + (max + padding - value) * 196 / (max - min + padding * 2);
  const labelEvery = Math.ceil(rows.length / 7);
  const chart = document.querySelector("#chart");
  chart.setAttribute("aria-label", `${name} by month from ${monthLabel(rows[0].month)} through ${monthLabel(rows.at(-1).month)}.`);
  chart.innerHTML = `<svg viewBox="0 0 ${width} 260" aria-hidden="true" focusable="false"><polyline class="chart-line" points="${rows.map((row, index) => `${x(index)},${y(row[metric])}`).join(" ")}"/>${rows.map((row, index) => `<circle class="chart-point" cx="${x(index)}" cy="${y(row[metric])}" r="4"><title>${monthLabel(row.month)}: ${format(row[metric])}</title></circle>${index % labelEvery === 0 || index === rows.length - 1 ? `<text class="chart-label" text-anchor="middle" x="${x(index)}" y="248">${monthLabel(row.month, "short")}</text>` : ""}`).join("")}</svg>`;
  document.querySelector("#chart-title").textContent = name;
  document.querySelector("#chart-description").textContent = `${monthLabel(rows[0].month)} through ${monthLabel(rows.at(-1).month)}. Observed range: ${format(min)} to ${format(max)}.`;
}

function renderSemantic(semantic, unavailableDetail = "") {
  const unavailable = document.querySelector("#semantic-unavailable");
  const content = document.querySelector("#semantic-content");
  if (!semantic) {
    semanticState = null;
    unavailable.hidden = false;
    content.hidden = true;
    document.querySelector("#semantic-stamp").textContent = "Portfolio connection unavailable";
    document.querySelector("#semantic-unavailable-title").textContent = unavailableDetail ? "Portfolio payload was refused" : "Portfolio measures are not connected";
    document.querySelector("#semantic-unavailable-detail").textContent = unavailableDetail || "Run the governed product build and preview commands to load the external M5 release. Issuance remains available above.";
    document.querySelector("#transition-evidence").hidden = true;
    configureEvidenceSignals();
    return;
  }
  semanticState = semantic;
  const rows = semantic.series;
  const latest = rows.at(-1);
  const prior = rows.at(-2);
  unavailable.hidden = true;
  content.hidden = false;
  document.querySelector("#semantic-stamp").innerHTML = `<strong>Full-population engine connected</strong><span>${semantic.metadata.supported_contracts} of ${semantic.metadata.catalog_contracts} contracts released</span>`;
  document.querySelector("#release-period").textContent = `Dec 2024-${monthLabel(latest.month)}`;
  document.querySelector("#portfolio-period").textContent = monthLabel(latest.month);
  document.querySelector("#correction-view").textContent = semantic.correction_view === "latest" ? "Latest known" : "As reported";
  document.querySelector("#metric-version").textContent = semantic.metadata.metric_version;
  document.querySelector("#portfolio-coverage").textContent = `${monthLabel(rows[0].month)}-${monthLabel(latest.month)} / ${rows.length} periods`;
  document.querySelector("#portfolio-refreshed").textContent = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(semantic.generated_at));
  document.querySelector("#portfolio-quality").textContent = "Passed";
  document.querySelector("#portfolio-quality-detail").textContent = semantic.quality.detail;
  document.querySelector("#comparability-status").textContent = "Unavailable";
  document.querySelector("#comparability-detail").textContent = semantic.comparability.detail;
  document.querySelector("#portfolio-loans").textContent = latest.loan_count.toLocaleString("en-US");
  document.querySelector("#portfolio-loans-note").textContent = deltaNote(latest.loan_count, prior.loan_count);
  document.querySelector("#portfolio-upb").textContent = money(latest.loan_upb);
  document.querySelector("#portfolio-upb-note").textContent = deltaNote(latest.loan_upb, prior.loan_upb);
  document.querySelector("#average-loan").textContent = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(latest.average_loan_balance);
  document.querySelector("#average-loan-note").textContent = deltaNote(latest.average_loan_balance, prior.average_loan_balance);
  document.querySelector("#modification-rate").textContent = percent(latest.modification_rate, 3);
  document.querySelector("#modification-rate-note").textContent = `${((latest.modification_rate - prior.modification_rate) * 10000).toFixed(2)} bps vs prior month`;
  document.querySelector("#delinquency-30").textContent = percent(latest.delinquency_30_rate, 3);
  document.querySelector("#delinquency-60").textContent = percent(latest.delinquency_60_rate, 3);
  document.querySelector("#delinquency-90").textContent = percent(latest.delinquency_90_rate, 3);
  renderSeriesChart(rows, "loan_upb", "#portfolio-chart", "Outstanding UPB", money);
  document.querySelector("#portfolio-chart-summary").textContent = `${money(latest.loan_upb)} in ${monthLabel(latest.month)}; ${deltaNote(latest.loan_upb, prior.loan_upb).toLowerCase()}. No certified comparability determination is available.`;

  const findings = document.querySelector("#portfolio-findings");
  findings.replaceChildren();
  semanticFindings(semantic).forEach((finding) => appendFinding(findings, finding));

  const table = document.querySelector("#concentration-body");
  table.replaceChildren();
  for (const row of semantic.concentration) {
    const tr = document.createElement("tr");
    const cue = row.top_10_share >= .5 ? "Prioritize top-ten composition review" : "Monitor with monthly comparison";
    const labels = ["Dimension", "Top-ten UPB share", "Top-ten UPB", "HHI", "Review cue"];
    for (const [index, value] of [row.entity[0].toUpperCase() + row.entity.slice(1), percent(row.top_10_share, 1), money(row.top_10_upb), row.hhi.toFixed(4), cue].entries()) {
      const td = document.createElement("td");
      td.textContent = value;
      td.dataset.label = labels[index];
      tr.append(td);
    }
    table.append(tr);
  }
  document.querySelector("#release-id").textContent = semantic.release_id;
  document.querySelector("#release-proof").textContent = `${semantic.metadata.released_components.toLocaleString("en-US")} released components / ${semantic.metadata.loan_rows.toLocaleString("en-US")} loan-period rows / snapshot ${semantic.metadata.snapshot_sha256.slice(0, 12)}...`;
  renderTransitionEvidence(semantic);
  configureEvidenceSignals();
}

function renderTransitionEvidence(semantic) {
  const transition = semantic.evidence.transitions;
  const section = document.querySelector("#transition-evidence");
  const body = document.querySelector("#transition-body");
  body.replaceChildren();
  for (const row of transition.rows) {
    const denominator = Number(row.denominator || 0);
    const numerator = Number(row.numerator);
    const values = [row.member, numerator.toLocaleString("en-US"), denominator.toLocaleString("en-US"), denominator ? percent(numerator / denominator, 3) : "Unavailable", row.correction_view === "latest" ? "Latest known" : "As reported"];
    const labels = ["Transition", "Loans", "Eligible origin", "Share", "Correction view"];
    const tr = document.createElement("tr");
    for (const [index, value] of values.entries()) {
      const td = document.createElement("td");
      td.textContent = value;
      td.dataset.label = labels[index];
      tr.append(td);
    }
    body.append(tr);
  }
  document.querySelector("#transition-summary").textContent = `${monthLabel(transition.period)} identity-matched loan cohorts. Attrition remains explicit and transition shares use the disclosed eligible origin population.`;
  document.querySelector("#transition-provenance").textContent = `Source partitions: ${transition.provenance.map((row) => `${row.source_file} (${row.report_period}, ${row.partition_sha256.slice(0, 12)}...)`).join("; ")}`;
  section.hidden = false;
}

function configureEvidenceSignals() {
  const select = document.querySelector("#case-signal");
  select.replaceChildren();
  for (const [id, label] of Object.entries(evidenceLabels)) {
    if (!semanticState?.evidence?.metrics?.[id]) continue;
    const option = document.createElement("option");
    option.value = id;
    option.textContent = label;
    select.append(option);
  }
  select.disabled = !select.options.length;
  renderEvidencePreview();
}

function renderEvidencePreview() {
  const select = document.querySelector("#case-signal");
  const preview = document.querySelector("#case-evidence-preview");
  const evidence = semanticState?.evidence?.metrics?.[select.value];
  if (!evidence) {
    preview.textContent = "No released evidence signal is available.";
    return;
  }
  const sources = evidence.provenance.map((row) => `${row.source_file} / ${row.partition_sha256.slice(0, 12)}...`).join("; ");
  preview.textContent = `${evidence.contract_id} / ${evidence.component} / ${evidence.report_period} / ${evidence.correction_view} / ${sources}`;
}

async function caseApi(path, options = {}) {
  if (!caseCredentials) throw new Error("Connect the investigation API first.");
  const headers = { Authorization: `Bearer ${caseCredentials.token}`, ...(options.headers ?? {}) };
  if (options.method && options.method !== "GET") headers["X-Actor"] = caseCredentials.actor;
  const response = await fetch(path, { ...options, headers, cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Investigation API returned HTTP ${response.status}.`);
  return payload;
}

function renderCases(items) {
  const container = document.querySelector("#case-list");
  container.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "case-empty";
    empty.textContent = "No investigations yet. Open one from a released evidence signal above.";
    container.append(empty);
    return;
  }
  for (const item of items) {
    const article = document.createElement("article");
    article.className = "case-record";
    const heading = document.createElement("div");
    heading.className = "case-record-heading";
    const title = document.createElement("h3");
    title.textContent = item.title;
    const status = document.createElement("span");
    status.textContent = item.status.replace("_", " ");
    status.dataset.status = item.status;
    heading.append(title, status);
    const summary = document.createElement("p");
    summary.textContent = item.summary;
    const context = document.createElement("p");
    context.className = "case-context";
    context.textContent = `${item.id} · ${item.owner} · ${item.priority} priority · ${item.report_period} · ${item.correction_view} · ${item.metric_version}`;
    const evidence = document.createElement("p");
    evidence.className = "case-evidence";
    evidence.textContent = `Evidence: ${item.evidence.map((row) => `${row.contract_id}/${row.component}`).join(", ")} · release ${item.release_id}`;
    article.append(heading, summary, context, evidence);
    if (item.resolution) {
      const resolution = document.createElement("p");
      resolution.className = "case-resolution";
      resolution.textContent = `Resolution: ${item.resolution}`;
      article.append(resolution);
    } else {
      const form = document.createElement("form");
      form.className = "case-resolve";
      const label = document.createElement("label");
      label.htmlFor = `resolution-${item.id}`;
      label.textContent = "Resolution";
      const textarea = document.createElement("textarea");
      textarea.id = `resolution-${item.id}`;
      textarea.rows = 2;
      textarea.required = true;
      const button = document.createElement("button");
      button.type = "submit";
      button.textContent = "Resolve investigation";
      form.append(label, textarea, button);
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        button.disabled = true;
        try {
          await caseApi(`/v1/investigations/${encodeURIComponent(item.id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: "resolved", resolution: textarea.value }),
          });
          await loadCases();
        } catch (error) {
          document.querySelector("#case-create-status").textContent = error.message;
        } finally {
          button.disabled = false;
        }
      });
      article.append(form);
    }
    container.append(article);
  }
}

async function loadCases() {
  const payload = await caseApi("/v1/investigations");
  renderCases(payload.items);
}

function configureInvestigations() {
  const accessForm = document.querySelector("#case-access");
  const createForm = document.querySelector("#case-create");
  document.querySelector("#case-signal").addEventListener("change", renderEvidencePreview);
  if (!["localhost", "127.0.0.1", "::1"].includes(window.location.hostname)) {
    accessForm.querySelectorAll("input, button").forEach((control) => { control.disabled = true; });
    document.querySelector("#case-access-status").textContent = "Public release is read-only. Run the authenticated API locally to create or resolve investigations.";
  }
  accessForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const actor = document.querySelector("#case-actor").value.trim();
    const tokenInput = document.querySelector("#case-token");
    caseCredentials = { actor, token: tokenInput.value };
    tokenInput.value = "";
    try {
      await loadCases();
      document.querySelector("#case-workspace").hidden = false;
      document.querySelector("#case-owner").value ||= actor;
      document.querySelector("#case-access-status").textContent = "Connected. Credentials remain in memory for this page only.";
    } catch (error) {
      caseCredentials = null;
      document.querySelector("#case-workspace").hidden = true;
      document.querySelector("#case-access-status").textContent = error.message;
    }
  });
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const signal = document.querySelector("#case-signal");
    const button = createForm.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const payload = buildInvestigationPayload(semanticState, signal.value, {
        title: `Review ${signal.options[signal.selectedIndex].textContent.toLowerCase()}`,
        owner: document.querySelector("#case-owner").value,
        priority: document.querySelector("#case-priority").value,
        summary: document.querySelector("#case-summary").value,
      });
      const created = await caseApi("/v1/investigations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      document.querySelector("#case-create-status").textContent = `${created.id} created with immutable release evidence.`;
      document.querySelector("#case-summary").value = "";
      await loadCases();
    } catch (error) {
      document.querySelector("#case-create-status").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

function configureViews() {
  const buttons = [...document.querySelectorAll("[data-view-target]")];
  const views = [...document.querySelectorAll(".product-view")];
  const activate = (button, moveFocus = false) => {
    for (const candidate of buttons) {
      const selected = candidate === button;
      candidate.setAttribute("aria-selected", String(selected));
      candidate.tabIndex = selected ? 0 : -1;
    }
    for (const view of views) view.hidden = view.id !== button.dataset.viewTarget;
    if (moveFocus) button.focus();
  };
  for (const button of buttons) {
    button.addEventListener("click", () => activate(button));
    button.addEventListener("keydown", (event) => {
      const current = buttons.indexOf(button);
      const next = event.key === "ArrowRight" ? (current + 1) % buttons.length
        : event.key === "ArrowLeft" ? (current - 1 + buttons.length) % buttons.length
          : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
      if (next === null) return;
      event.preventDefault();
      activate(buttons[next], true);
    });
  }
}

function renderMix(payload) {
  const container = document.querySelector("#mix-list");
  container.replaceChildren();
  for (const row of latestMix(payload)) {
    const item = document.createElement("li");
    const heading = document.createElement("div");
    const label = document.createElement("strong");
    const value = document.createElement("span");
    const track = document.createElement("div");
    const bar = document.createElement("span");
    label.textContent = row.product_group;
    value.textContent = `${money(row.issuance_upb)} · ${(row.issuance_share * 100).toFixed(1)}%`;
    bar.style.inlineSize = `${Math.max(row.issuance_share * 100, 1)}%`;
    track.className = "mix-track";
    track.setAttribute("aria-hidden", "true");
    heading.append(label, value);
    track.append(bar);
    item.append(heading, track);
    container.append(item);
  }
}

function render(payload) {
  const rows = payload.months;
  const latest = rows.at(-1);
  const prior = rows.at(-2);
  const peak = rows.reduce((best, row) => row.issuance_upb > best.issuance_upb ? row : best);
  const total = rows.reduce((sum, row) => sum + row.issuance_upb, 0);
  const change = percentChange(latest.issuance_upb, prior.issuance_upb);
  const quality = payload.metadata.quality;
  document.querySelector("#coverage-note").textContent = `${quality.published_count.toLocaleString("en-US")} published observations across ${payload.metadata.source_file_count} files.`;
  document.querySelector("#generated-note").textContent = `Built ${new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(payload.metadata.generated_at))}`;
  document.querySelector("#quality-summary").textContent = `${quality.input_count.toLocaleString("en-US")} source rows reconciled`;
  document.querySelector("#quality-detail").textContent = `${quality.accepted_count.toLocaleString("en-US")} accepted · ${quality.excluded_count.toLocaleString("en-US")} documented exclusions · ${quality.rejected_count} rejected · ${quality.duplicate_count} duplicates`;
  document.querySelector("#latest-count").textContent = latest.security_count.toLocaleString("en-US");
  document.querySelector("#latest-count-note").textContent = `${monthLabel(latest.month)} · ${percentChange(latest.security_count, prior.security_count).toFixed(1)}% vs prior`;
  document.querySelector("#latest-upb").textContent = money(latest.issuance_upb);
  document.querySelector("#latest-upb-note").textContent = `${change >= 0 ? "+" : ""}${change.toFixed(1)}% vs prior month`;
  document.querySelector("#period-total").textContent = money(total);
  document.querySelector("#period-total-note").textContent = `${rows.length} observed months`;
  document.querySelector("#peak-upb").textContent = money(peak.issuance_upb);
  document.querySelector("#peak-upb-note").textContent = monthLabel(peak.month);

  const findings = document.querySelector("#findings");
  findings.replaceChildren();
  deriveFindings(payload).forEach((finding) => appendFinding(findings, finding));
  renderChart(payload, "issuance_upb");
  renderMix(payload);

  const table = document.querySelector("#table-body");
  table.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    const labels = ["Month", "Issued securities", "Issuance UPB", "Corrections"];
    for (const [index, value] of [monthLabel(row.month), row.security_count.toLocaleString("en-US"), money(row.issuance_upb), row.correction_count.toLocaleString("en-US")].entries()) {
      const td = document.createElement("td");
      td.textContent = value;
      td.dataset.label = labels[index];
      tr.append(td);
    }
    table.append(tr);
  }
  document.querySelector("#mix-source").href = payload.metadata.mix.taxonomy_source;
  document.querySelector("#mix-coverage").textContent = `${(payload.metadata.mix.mapped_issuance_share * 100).toFixed(1)}% of issuance UPB mapped to an official UMBS term family; all remaining prefixes stay explicit.`;
  document.querySelector("#metric").onchange = (event) => renderChart(payload, event.target.value);
  try {
    renderSemantic(validateSemanticPayload(payload.semantic));
  } catch (error) {
    renderSemantic(null, `${error.message} Issuance remains available; rebuild the governed product payload before retrying portfolio analysis.`);
  }
  statusPanel.hidden = true;
  dashboard.hidden = false;
}

async function loadDashboard() {
  dashboard.hidden = true;
  setStatus("loading", "Loading governed disclosure data", "Checking the verified release and quality gate.");
  retryButton.disabled = true;
  try {
    const response = await fetch("data/dashboard.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`The release request returned HTTP ${response.status}.`);
    const payload = validatePayload(await response.json());
    render(payload);
  } catch (error) {
    setStatus("error", "Issuance data could not be loaded", `${error.message} Confirm the local server and released payload, then retry.`);
  } finally {
    retryButton.disabled = false;
  }
}

retryButton.addEventListener("click", loadDashboard);
configureViews();
configureInvestigations();
loadDashboard();
