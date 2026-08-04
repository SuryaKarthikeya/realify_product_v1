/**
 * Options and defaults for the Actions table's SKU filter popover.
 *
 * Kept out of the component file so both the popover and the page that applies
 * the filter can import them without tripping fast-refresh.
 */

/**
 * Impact bands, matched against a signal's exposure.
 * `test` keeps the boundary logic next to the label it belongs to.
 */
/*
 * Thresholds are set against the actual exposure spread ($18K–$340K) so each
 * band selects a meaningful slice. A single band that matched every row would
 * look like a filter but do nothing.
 */
export const IMPACT_BANDS = [
  { key: 'high', label: '> $150K', test: (v) => v > 150000 },
  { key: 'mid', label: 'Between $50K to $150K', test: (v) => v >= 50000 && v <= 150000 },
  { key: 'low', label: '< $50K', test: (v) => v < 50000 },
];

/**
 * "Filter by action" options per domain — the action we're telling the seller to
 * take, not the symptom. Each option lists the signal `type` values it covers so
 * every row stays reachable through some option.
 */
export const ACTION_OPTIONS_BY_DOMAIN = {
  sales: [
    { key: 'reprice', label: 'Reprice', types: ['BUY BOX DROP'] },
    { key: 'diversify', label: 'Diversify', types: ['VIRAL SURGE', 'BUNDLE OPP'] },
    { key: 'conflict', label: 'Conflict', types: ['SEARCH RANK DROP', 'CONVERSION DROP'] },
    { key: 'opportunity', label: 'Opportunity', types: ['SEASONAL TAIL'] },
  ],
  margin: [
    { key: 'audit', label: 'Raise Audit', types: ['PROFIT LEAKAGE'] },
    { key: 'negate', label: 'Negate Keywords', types: ['UNPROFITABLE AD SPEND'] },
    { key: 'reprice', label: 'Apply Price Change', types: ['PRICING OPPORTUNITY'] },
    { key: 'negotiate', label: 'Negotiate Cost', types: ['COGS VARIANCE'] },
  ],
  inventory: [
    { key: 'restock', label: 'Restock', types: ['STOCKOUT IMMINENT'] },
    { key: 'clearance', label: 'Run Clearance', types: ['OVERSTOCK RISK'] },
    { key: 'po', label: 'Create PO', types: ['REORDER TRIGGER'] },
  ],
  cash: [
    { key: 'discount', label: 'Apply Discount', types: ['WORKING CAPITAL'] },
    { key: 'terms', label: 'Request Terms', types: ['PAYOUT GAP'] },
    { key: 'logistics', label: 'Switch Logistics', types: ['BURN RATE ALERT'] },
  ],
  ads: [
    { key: 'pause', label: 'Pause Campaign', types: ['ROAS DROP'] },
    { key: 'bids', label: 'Optimize Bids', types: ['TACOS SPIKE'] },
    { key: 'scale', label: 'Scale Budget', types: ['UNTAPPED KEYWORD'] },
    { key: 'creative', label: 'Refresh Creative', types: ['CREATIVE FATIGUE'] },
    { key: 'budget', label: 'Rebalance Budget', types: ['BUDGET PACING'] },
  ],
};

/** Nothing selected = nothing excluded, so every filter starts wide open. */
export const EMPTY_SKU_FILTER = {
  sort: null,          // null | 'asc' | 'desc'
  search: '',
  impact: [],          // IMPACT_BANDS keys
  actions: [],         // ACTION_OPTIONS_BY_DOMAIN keys
  showActive: true,
  showInactive: true,
};
