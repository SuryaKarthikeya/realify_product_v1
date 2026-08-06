/**
 * Background for the filter pills — Category / Channel / Status / SKU / date.
 *
 * Two surfaces, because the same three controls are used in two different
 * places and only one of them is a table:
 *
 *   'table'  the filter bar inside a table card (Workspace's Actions table).
 *            #F8FAFC reads as a control sitting on the card rather than as
 *            another white panel floating on a white one.
 *   'plain'  anywhere the pills are not filtering a table — the Workspace KPI
 *            header, for one — where they stay white. Default, so a new caller
 *            has to opt in to the table surface deliberately.
 *
 * Dark mode is the same on both: the tint only does work against a white card.
 *
 * Written as whole class strings, never composed from fragments — Tailwind
 * scans source text, so a class it cannot see spelled out is never generated.
 */
export const FILTER_PILL_SURFACE = {
  plain: 'bg-white dark:bg-slate-800',
  table: 'bg-[#F8FAFC] dark:bg-slate-800',
};

/** Resolves a `surface` prop to its classes, falling back to the plain pill. */
export const pillSurface = (surface) => FILTER_PILL_SURFACE[surface] || FILTER_PILL_SURFACE.plain;
