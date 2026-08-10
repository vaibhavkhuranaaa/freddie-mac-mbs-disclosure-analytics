import { deriveFindings, latestMix, money, monthLabel, percentChange, validatePayload } from "./analytics.js";

const statusPanel = document.querySelector("#app-status");
const dashboard = document.querySelector("#dashboard-content");
const retryButton = document.querySelector("#retry");

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
  const chart = document.querySelector("#chart");
  chart.setAttribute("aria-label", `${name} by month from ${monthLabel(rows[0].month)} through ${monthLabel(rows.at(-1).month)}.`);
  chart.innerHTML = `<svg viewBox="0 0 ${width} 260" aria-hidden="true" focusable="false"><polyline class="chart-line" points="${rows.map((row, index) => `${x(index)},${y(row[metric])}`).join(" ")}"/>${rows.map((row, index) => `<circle class="chart-point" cx="${x(index)}" cy="${y(row[metric])}" r="4"><title>${monthLabel(row.month)}: ${format(row[metric])}</title></circle><text class="chart-label" text-anchor="middle" x="${x(index)}" y="248">${monthLabel(row.month, "short")}</text>`).join("")}</svg>`;
  document.querySelector("#chart-title").textContent = name;
  document.querySelector("#chart-description").textContent = `${monthLabel(rows[0].month)} through ${monthLabel(rows.at(-1).month)}. Observed range: ${format(min)} to ${format(max)}.`;
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
    for (const value of [monthLabel(row.month), row.security_count.toLocaleString("en-US"), money(row.issuance_upb), row.correction_count.toLocaleString("en-US")]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    table.append(tr);
  }
  document.querySelector("#mix-source").href = payload.metadata.mix.taxonomy_source;
  document.querySelector("#mix-coverage").textContent = `${(payload.metadata.mix.mapped_issuance_share * 100).toFixed(1)}% of issuance UPB mapped to an official UMBS term family; all remaining prefixes stay explicit.`;
  document.querySelector("#metric").onchange = (event) => renderChart(payload, event.target.value);
  statusPanel.hidden = true;
  dashboard.hidden = false;
}

async function loadDashboard() {
  dashboard.hidden = true;
  setStatus("loading", "Loading governed issuance data", "Checking the released aggregate and quality gate.");
  retryButton.disabled = true;
  try {
    const response = await fetch("data/dashboard.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`The aggregate request returned HTTP ${response.status}.`);
    const payload = validatePayload(await response.json());
    render(payload);
  } catch (error) {
    setStatus("error", "Issuance data could not be loaded", `${error.message} Confirm the local server and released payload, then retry.`);
  } finally {
    retryButton.disabled = false;
  }
}

retryButton.addEventListener("click", loadDashboard);
loadDashboard();
