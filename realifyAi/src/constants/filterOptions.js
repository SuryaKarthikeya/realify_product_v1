/**
 * Filter vocabulary shared by every filter surface in the app — the Workspace
 * filter panel, the Dashboard View filter bar, and the global header popover.
 */
export const V2_DATE_OPTS = [['last-7-days', 'Last 7 Days'], ['last-30-days', 'Last 30 Days'], ['last-90-days', 'Last 90 Days'], ['ytd', 'Year to Date']];

/**
 * ── The product taxonomy, single source of truth ──
 *
 * Every catalogue category the platform recognises, used identically by all five
 * KPI domains (Revenue, Margin, Inventory, Ads, Cash). Nothing outside this list
 * should appear on a signal, in a filter, or in a breakdown chart — the previous
 * ad-hoc labels ('Finance', 'Operations', 'Pet Suppliers') are what let the
 * filter lists and the data drift apart.
 *
 * `value` is the slug filters store; `label` is what the data and UI display.
 */
export const PRODUCT_CATEGORIES = [
  { value: 'electronics', label: 'Electronics', icon: 'fa-tv' },
  { value: 'furniture', label: 'Furniture', icon: 'fa-couch' },
  { value: 'apparel', label: 'Apparel', icon: 'fa-shirt' },
  { value: 'home-garden', label: 'Home & Garden', icon: 'fa-house' },
  { value: 'pet-supplies', label: 'Pet Supplies', icon: 'fa-paw' },
];

/**
 * Display label → filter slug.
 *
 * Collapsing every run of non-alphanumerics to a single dash is what makes
 * 'Home & Garden' resolve to 'home-garden'; comparing the two directly is why
 * that filter silently matched nothing before.
 */
export const categorySlug = (label = '') =>
  label.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export const V2_CAT_OPTS = [['all', 'All Categories'], ...PRODUCT_CATEGORIES.map((c) => [c.value, c.label])];
export const V2_CAT_GRID = [...PRODUCT_CATEGORIES.map((c) => [c.value, c.label]), ['all', 'All Categories']];
export const CAL_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
export const CAL_WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
