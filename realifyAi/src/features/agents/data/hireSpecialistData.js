/**
 * Content for the "Hire a specialist" flow.
 *
 * The five-step rail is data-driven: `HIRE_STEPS` holds the copy and the view
 * takes a `currentStep` index, so the later procedure can advance the rail
 * without the component knowing anything about the sequence. Steps before the
 * index render as complete, the index itself as active, the rest as pending.
 */
export const HIRE_STEPS = [
  {
    key: 'connect',
    label: 'Connect',
    description: 'Channels and data wired in Integrations — SP-API, Ads, Shopify, cost reads.',
  },
  {
    key: 'baseline',
    label: 'Baseline',
    description: 'RCDP ingests 24 months; engines calibrate floors, covers, targets.',
  },
  {
    key: 'shadow',
    label: 'Shadow',
    description: '14 days. Every agent proposes; nothing writes. You grade the tape.',
  },
  {
    key: 'scope',
    label: 'Scope',
    description: 'Playbook per grain, tighten-only. Trust contract: every hire starts at Observe.',
  },
  {
    key: 'graduate',
    label: 'Graduate',
    description: 'Promotion on evidence — the dial advances one stop per earned review.',
  },
];

/** Where the flow currently sits. Bump this as the procedure is built out. */
export const CURRENT_HIRE_STEP = 2;

/**
 * Scope tree for the selected specialist. `depth` drives the indent and the last
 * node is the bound leaf — highlighted because scope is tighten-only below it.
 */
export const SCOPE_TREE = [
  { label: 'Home & Kitchen', depth: 0, icon: 'fa-house' },
  { label: 'Cookware', depth: 1, icon: 'fa-box-archive' },
  { label: 'Fry Pans', depth: 2, icon: 'fa-box-archive' },
  { label: 'Nonstick Fry Pan 10"', depth: 3, isLeaf: true },
];

/** Resolved playbook values. `origin` says whether the value was inherited. */
export const PLAYBOOK_RULES = [
  { key: 'category-role', label: 'Category role', origin: 'Inherited · Subcategory', value: 'Traffic / KVI' },
  { key: 'cm3-floor', label: 'CM3 floor', origin: 'Overridden · Item', value: '$6.10 / unit' },
  { key: 'map', label: 'MAP', origin: 'Inherited · Category', value: '$24.99' },
  { key: 'cover-band', label: 'Cover band', origin: 'Inherited · Subcategory', value: '14 days' },
  { key: 'depth-ceiling', label: 'Depth ceiling', origin: 'Inherited · Category', value: '18%' },
];

/**
 * The trust ladder. Every hire starts at the first rung; the rest are earned,
 * which is why only `Observe` renders as reached.
 */
export const TRUST_LADDER = [
  { key: 'observe', label: 'Observe', badge: 'STARTS HERE', description: 'Simulates & narrates — nothing surfaces as an ask' },
  { key: 'suggest', label: 'Suggest', description: 'Proposes; every action needs approval' },
  { key: 'assist', label: 'Assist', description: 'Acts inside tight bands; review after' },
  { key: 'act', label: 'Act', description: 'Autonomous inside the Playbook; A3 still yours' },
];

/* ── per-agent preview content ── */

/**
 * Scope and playbook differ by specialist: a pricing agent is bound to an item
 * and gated on CM3/MAP, while an ads agent is bound to a campaign and gated on
 * TACoS. Overrides live here; anything unlisted derives a default from the
 * roster entry so every specialist previews with its own values.
 */
const HIRE_OVERRIDES = {
  'pricing-repricing': {
    tagline: 'runs like a GMM',
    scope: SCOPE_TREE,
    playbook: PLAYBOOK_RULES,
  },
  'bidding-ads': {
    tagline: 'runs like a media buyer',
    scope: [
      { label: 'Electronics', depth: 0, icon: 'fa-tv' },
      { label: 'Cameras', depth: 1, icon: 'fa-box-archive' },
      { label: 'Sponsored Products', depth: 2, icon: 'fa-box-archive' },
      { label: 'Smart Camera SP Broad', depth: 3, isLeaf: true },
    ],
    playbook: [
      { key: 'campaign-role', label: 'Campaign role', origin: 'Inherited · Subcategory', value: 'Prospecting' },
      { key: 'tacos-ceiling', label: 'TACoS ceiling', origin: 'Overridden · Campaign', value: '12.0%' },
      { key: 'roas-floor', label: 'ROAS floor', origin: 'Inherited · Category', value: '3.5x' },
      { key: 'bid-step', label: 'Bid step', origin: 'Inherited · Subcategory', value: '± 15%' },
      { key: 'daily-cap', label: 'Daily cap', origin: 'Inherited · Campaign', value: '$2,500' },
    ],
  },
  'replenishment': {
    tagline: 'runs like a planner',
    scope: [
      { label: 'Home & Garden', depth: 0, icon: 'fa-house' },
      { label: 'Cleaning', depth: 1, icon: 'fa-box-archive' },
      { label: 'Vacuum Filters', depth: 2, icon: 'fa-box-archive' },
      { label: 'Car Vacuum Filter', depth: 3, isLeaf: true },
    ],
    playbook: [
      { key: 'cover-target', label: 'Cover target', origin: 'Inherited · Subcategory', value: '21 days' },
      { key: 'reorder-point', label: 'Reorder point', origin: 'Overridden · Item', value: '12 days' },
      { key: 'lead-time', label: 'Supplier lead time', origin: 'Inherited · Supplier', value: '15 days' },
      { key: 'moq', label: 'MOQ', origin: 'Inherited · Supplier', value: '500 units' },
      { key: 'expedite-cap', label: 'Expedite cap', origin: 'Inherited · Category', value: '$8,000' },
    ],
  },
};

/**
 * Preview content for the specialist being hired.
 *
 * Falls back to a scope derived from the agent's own `meta` grain, so an agent
 * with no override still previews against something true about itself rather
 * than another specialist's fry pans.
 */
export const hireProfile = (agent) => {
  const o = (agent && HIRE_OVERRIDES[agent.id]) || {};
  const grain = agent?.meta?.split(' • ')[0] || 'All categories';

  return {
    tagline: o.tagline || (agent ? `runs the ${grain.toLowerCase()} desk` : 'runs like a GMM'),
    scope: o.scope || [
      { label: grain, depth: 0, icon: 'fa-house' },
      { label: agent?.group || 'Growth', depth: 1, icon: 'fa-box-archive' },
      { label: agent?.name || 'Specialist', depth: 2, isLeaf: true },
    ],
    playbook: o.playbook || PLAYBOOK_RULES,
  };
};
