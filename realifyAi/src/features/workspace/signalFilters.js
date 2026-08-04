/**
 * Shared matching rules for the Workspace filters.
 *
 * Channel, category and status are multi-select, so each is stored as an array
 * of selected values. An **empty array means "no filter"** — nothing selected
 * excludes nothing, matching how the SKU popover already behaves. Selections
 * within one filter are OR'd; separate filters are AND'd by the caller.
 *
 * These live in one module because the Workspace page and the Insights panel
 * both filter the same signals — duplicating the predicates is how they drift.
 */
import { categorySlug } from '@/constants/filterOptions';

/** True when `selected` is empty, i.e. the filter is off. */
export const isFilterOff = (selected) => !selected || selected.length === 0;

/** Channel match against a signal's `sourceOwn`. */
export const matchesChannel = (signal, selected) => {
  if (isFilterOff(selected)) return true;
  const channel = (signal.sourceOwn || signal.channel || signal.marketplace || '').toLowerCase();
  return selected.some((value) => channel === value.toLowerCase());
};

/**
 * Category match.
 *
 * The option values are slugs ('home-garden') while the data carries display
 * names ('Home & Garden'), so the label is slugified before comparing. The old
 * substring test could not bridge that — `'home & garden'.includes('home-garden')`
 * is false, so Home & Garden and Pet Supplies matched nothing at all.
 */
export const matchesCategory = (signal, selected) => {
  if (isFilterOff(selected)) return true;
  const slug = categorySlug(signal.category || signal.tagCategory || '');
  return selected.some((value) => slug === categorySlug(value));
};

/** Status match against the executed-signal list. */
export const matchesStatus = (signal, selected, executedSignalIds = []) => {
  if (isFilterOff(selected)) return true;
  const isExecuted = executedSignalIds.includes(signal.id);
  return selected.some((value) =>
    value === 'executed' ? isExecuted : value === 'not_executed' ? !isExecuted : true
  );
};

/**
 * Button label for a multi-select filter: the bare label while nothing is
 * chosen, the single choice when there is one, and a count beyond that.
 */
export const multiSelectLabel = (label, selected, options) => {
  if (isFilterOff(selected)) return label;
  if (selected.length === 1) {
    return options.find((o) => o.value === selected[0])?.label || label;
  }
  return `${label} (${selected.length})`;
};
