const payload = await fetch("data/dashboard.json").then((response) => response.ok ? response.json() : Promise.reject(new Error("Dashboard data is unavailable.")));
const byMonth = payload.months;
const monthLabel = (month) => new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${month}-01T00:00:00Z`));
const money = (value) => `$${(value / 1e9).toLocaleString("en-US", { maximumFractionDigits: 1 })}B`;
const percentChange = (now, then) => `${now >= then ? "+" : ""}${((now / then - 1) * 100).toFixed(1)}% vs. prior month`;
const latest = byMonth.at(-1);
const prior = byMonth.at(-2);
const peak = byMonth.reduce((highest, month) => month.issuance_upb > highest.issuance_upb ? month : highest);
const low = byMonth.reduce((lowest, month) => month.issuance_upb < lowest.issuance_upb ? month : lowest);
const totalIssuance = byMonth.reduce((sum, month) => sum + month.issuance_upb, 0);

document.querySelector("#coverage-note").textContent = `${payload.metadata.observation_count.toLocaleString("en-US")} security observations across ${byMonth.length} monthly files.`;
document.querySelector("#issuance-value").textContent = latest.security_count.toLocaleString("en-US");
document.querySelector("#issuance-change").textContent = percentChange(latest.security_count, prior.security_count);
document.querySelector("#upb-value").textContent = money(latest.issuance_upb);
document.querySelector("#upb-change").textContent = percentChange(latest.issuance_upb, prior.issuance_upb);
document.querySelector("#total-value").textContent = money(totalIssuance);
document.querySelector("#total-change").textContent = `${byMonth.length} months of issuance`;
document.querySelector("#peak-value").textContent = money(peak.issuance_upb);
document.querySelector("#peak-change").textContent = `${monthLabel(peak.month)} · ${peak.security_count.toLocaleString("en-US")} securities`;

const april2026 = byMonth.find((month) => month.month === "2026-04");
const march2026 = byMonth.find((month) => month.month === "2026-03");
const observedLift = april2026 && march2026 ? ((april2026.issuance_upb / march2026.issuance_upb - 1) * 100).toFixed(1) : null;
const spread = ((peak.issuance_upb / low.issuance_upb - 1) * 100).toFixed(0);
document.querySelector("#findings").innerHTML = [
  `<article><strong>An elevated start to 2025</strong><p>${monthLabel(peak.month)} was the highest observed issuance month at ${money(peak.issuance_upb)}, spanning ${peak.security_count.toLocaleString("en-US")} securities.</p></article>`,
  `<article><strong>A clear 2026 spring pickup</strong><p>${monthLabel(april2026?.month || latest.month)} issuance reached ${money(april2026?.issuance_upb || latest.issuance_upb)}${observedLift ? `, up ${observedLift}% from March` : ""}.</p></article>`,
  `<article><strong>A wide monthly range</strong><p>Issuance moved from ${money(low.issuance_upb)} in ${monthLabel(low.month)} to ${money(peak.issuance_upb)} at the high, a ${spread}% spread across observed months.</p></article>`
].join("");

function chart(metric) {
  const settings = {
    issuance_upb: ["Issuance UPB", money],
    security_count: ["Issued securities", (value) => value.toLocaleString("en-US")],
    average_factor: ["Average security factor", (value) => value.toFixed(4)]
  };
  const [name, format] = settings[metric];
  const values = byMonth.map((month) => month[metric]);
  const min = Math.min(...values), max = Math.max(...values), padding = (max - min || 1) * 0.18;
  const lowValue = min - padding, highValue = max + padding, width = 720, height = 260;
  const x = (index) => 36 + index * 666 / (byMonth.length - 1);
  const y = (value) => 20 + (highValue - value) * 200 / (highValue - lowValue);
  document.querySelector("#chart-title").textContent = name;
  document.querySelector("#chart-summary").textContent = `${monthLabel(byMonth[0].month)} to ${monthLabel(latest.month)}`;
  document.querySelector("#chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true"><polyline class="chart-line" points="${byMonth.map((month, index) => `${x(index)},${y(month[metric])}`).join(" ")}"/>${byMonth.map((month, index) => `<circle class="chart-point" cx="${x(index)}" cy="${y(month[metric])}" r="4"><title>${monthLabel(month.month)}: ${format(month[metric])}</title></circle><text class="chart-label" text-anchor="middle" x="${x(index)}" y="248">${monthLabel(month.month).split(" ")[0]}</text>`).join("")}</svg>`;
}

document.querySelector("#table-body").innerHTML = byMonth.map((month) => `<tr><td>${monthLabel(month.month)}</td><td>${month.security_count.toLocaleString("en-US")}</td><td>${money(month.issuance_upb)}</td><td>${month.average_factor.toFixed(4)}</td><td>${month.correction_count.toLocaleString("en-US")}</td></tr>`).join("");
chart("issuance_upb");
document.querySelector("#metric").addEventListener("change", (event) => chart(event.target.value));
