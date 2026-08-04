import { formatSignedMoney } from '@/utils/formatters';

/**
 * Action-type driven configuration for the Action Center.
 *
 * Everything keyed off `action.signalType` (the action-type field carried over
 * from the signal) so rows never hardcode their own label or colour.
 * Adding a new action type = one entry here, no component changes.
 */

/* ── action type → CTA label ── */
export const CTA_BY_ACTION_TYPE = {
  /* Revenue */
  'BUY BOX DROP':         { label: 'Reprice',            icon: 'fa-tags' },
  'VIRAL SURGE':          { label: 'Restock',            icon: 'fa-truck-fast' },
  'SEARCH RANK DROP':     { label: 'Optimize Listing',   icon: 'fa-magnifying-glass-chart' },
  'BUNDLE OPP':           { label: 'Create Bundle',      icon: 'fa-layer-group' },
  'SEASONAL TAIL':        { label: 'Reallocate Budget',  icon: 'fa-arrows-turn-right' },
  'CONVERSION DROP':      { label: 'Update Creative',    icon: 'fa-image' },

  /* Margin */
  'PROFIT LEAKAGE':       { label: 'Raise Audit',        icon: 'fa-file-invoice' },
  'UNPROFITABLE AD SPEND':{ label: 'Negate Keywords',    icon: 'fa-ban' },
  'PRICING OPPORTUNITY':  { label: 'Apply Price Change', icon: 'fa-tag' },
  'COGS VARIANCE':        { label: 'Negotiate Cost',     icon: 'fa-handshake' },

  /* Cash */
  'WORKING CAPITAL':      { label: 'Apply Discount',     icon: 'fa-percent' },
  'PAYOUT GAP':           { label: 'Request Terms',      icon: 'fa-calendar-days' },
  'BURN RATE ALERT':      { label: 'Switch Logistics',   icon: 'fa-ship' },

  /* Inventory */
  'STOCKOUT IMMINENT':    { label: 'Restock',            icon: 'fa-truck-fast' },
  'OVERSTOCK RISK':       { label: 'Run Clearance',      icon: 'fa-percent' },
  'REORDER TRIGGER':      { label: 'Create PO',          icon: 'fa-file-circle-plus' },

  /* Ads */
  'ROAS DROP':            { label: 'Pause Campaign',     icon: 'fa-circle-pause' },
  'TACOS SPIKE':          { label: 'Optimize Bids',      icon: 'fa-sliders' },
  'UNTAPPED KEYWORD':     { label: 'Scale Budget',       icon: 'fa-arrow-up-right-dots' },
  'CREATIVE FATIGUE':     { label: 'Refresh Creative',   icon: 'fa-wand-magic-sparkles' },
  'BUDGET PACING':        { label: 'Rebalance Budget',   icon: 'fa-scale-balanced' },
};

/* Anything unmapped falls back to a review step rather than a wrong action. */
export const DEFAULT_CTA = { label: 'Review', icon: 'fa-eye' };

export const getActionCta = (action) =>
  CTA_BY_ACTION_TYPE[action?.signalType] || DEFAULT_CTA;

/**
 * ── action type → impact direction ──
 * 'gain' = upside you can capture (renders green / positive).
 * 'loss' = value currently bleeding (renders red / negative).
 * Types absent from this list default to 'loss'.
 */
export const GAIN_ACTION_TYPES = new Set([
  'VIRAL SURGE',
  'BUNDLE OPP',
  'PRICING OPPORTUNITY',
  'UNTAPPED KEYWORD',
  'BUDGET PACING', // unspent budget at good ROAS is upside, not a leak
  'REORDER TRIGGER',
  'WORKING CAPITAL', // liquidating overstock frees up cash
]);

export const getImpactSign = (action) => (GAIN_ACTION_TYPES.has(action?.signalType) ? 1 : -1);

/* ── module → icon, shared by the table and the filter bar ── */
export const CATEGORY_ICONS = {
  Revenue: 'fa-dollar-sign',
  Margin: 'fa-chart-line',
  Cash: 'fa-money-bill-wave',
  Inventory: 'fa-boxes-stacked',
  Ads: 'fa-bullhorn',
};

/** Sign-aware compact dollars — K / M only. Mirrors the app's other $ readouts. */
export const formatImpactValue = (value) => formatSignedMoney(value);

export const formatImpactPct = (pct) => `${(pct || 0) < 0 ? '' : '+'}${(pct || 0).toFixed(1)}%`;
