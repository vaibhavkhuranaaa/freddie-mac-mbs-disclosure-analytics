# User-facing design rules

## Audience and outcome

- Design first for disclosure operations and business leaders who do not write SQL.
- Each page answers one business question and ends with a clear review decision or investigation path.
- Lead with `What changed`, `Why it matters`, and `What to review next`; keep formulas available but secondary.

## Information hierarchy

- Page order follows trust, change, driver, comparability, and action.
- Show release period, refresh time, data coverage, quality status, comparability status, and active filters persistently.
- Group release period, coverage, correction view, metric version, refresh time, quality, and comparability into a compact trust-context ledger before affected measures; keep the labels stable across views and data providers.
- Put failed quality/comparability states above and visually stronger than affected metrics.
- When comparison context is not released, label comparability `Unavailable` and name the missing period or contract. Raw adjacent-period arithmetic may remain as explicitly descriptive context, but do not turn it into a certified comparison, imply equivalence, or substitute another period.
- Limit a page to one primary message and no more than seven decision-bearing visuals.
- Provide an evidence/drill-through path from every executive exception.

## Visual selection

- Use KPI cards with period delta and sparkline for current state; never use a card without comparison context.
- Use lines/small multiples for time, waterfalls for balance or change bridges, 100% stacked bars for composition, heatmaps/matrices for cohorts and transitions, and scatterplots for relationships.
- Use a map only when geography is the question and pair it with a sortable table.
- Avoid 3D charts, decorative gauges, unlabeled pies, rainbow palettes, unexplained dual axes, and chart decoration that carries no decision value.
- Keep units, denominators, filter context, missing values, `Other`, corrections, and non-comparable periods visible.

## Language and interpretation

- Use plain business names and define specialist terms in report-page tooltips or the methods page.
- Describe observed association, composition, or operational signal; do not imply causation, investment merit, or borrower judgment.
- Treat direction as contextual unless the metric has an approved good/bad interpretation.
- Generated takeaways must cite period, metric version, and quality/comparability status.

## Interaction

- Global slicers: reporting/comparison period, product/term, vintage, purpose, occupancy, property type, geography, seller, servicer, score band/model, LTV band, delinquency band, and correction view.
- Use provider-neutral view tabs named for the user's business question or evidence domain, never for a backend, release artifact, or implementation technology. Implement them as keyboard-operable tabs with one clearly selected state and preserved context when switching views.
- Provide reset filters, current filter summary, drill-through, back navigation, metric definition, and export classification.
- Do not rely on hover, hidden gestures, or cross-highlighting as the only way to understand a result.
- Preserve user context when moving from an exception to evidence.

## Accessibility and polish

- Use the selected platform's professional readable type; maintain clear typographic hierarchy and restrained spacing.
- Meet WCAG 2.2 AA contrast, keyboard order, visible focus, screen-reader labels, high-contrast mode, and 200% zoom requirements.
- Never encode meaning by color alone; pair status colors with text and icons.
- Every chart conclusion needs a text summary or accessible data table.
- Loading, empty, partial, stale, non-comparable, error, and refusal states must name the cause and next action.
- Treat semantic refusal as a governed product result, distinct from loading, empty, connectivity, and generic error states. Name the unavailable metric or contract, explain the release or policy boundary, preserve unaffected views, and offer only a valid recovery path; never fabricate a proxy.
- Keep evidence as a semantic table at wide widths. At compact widths, reflow each row into a bordered record with every value paired to its visible column label; retain the accessible header structure and avoid horizontal page scrolling.
- Validate at desktop and compact widths; no clipped labels, hidden controls, or horizontal page scrolling.

## Governance

- No report-local calculation may bypass the certified semantic model.
- Before publication, source values and row-level analytical data stay outside Git and appear only in authorized pages and exports.
- Publication targets complete row-level source and derived data after the explicit integrity, provenance, rights, and release gates pass.
- Screenshots and validation artifacts use the approved release boundary, never a more permissive data source by convenience.
- Apply these rules and `docs/BI_PRODUCT_SPEC.md` to every Power BI, static web, and portfolio-facing change.
