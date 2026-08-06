/**
 * The specialist roster shown on the Agents page.
 *
 * Each agent is one card. `group` drives the filter tabs, `status` drives the
 * badge and the Active/Standby counters — the header tiles are counted from this
 * list rather than hardcoded, so they cannot disagree with what is on screen.
 *
 * `rampDay` / `rampTotal` describe the shadow period a newly hired specialist
 * serves before it is allowed to act on its own.
 */
export const AGENT_GROUPS = ['All', 'Growth', 'Operations', 'Intelligence', 'Finance', 'System'];

export const AGENTS_ROSTER = [
  {
    id: 'category-manager',
    initials: 'CM',
    name: 'Category Manager',
    meta: 'Orchestrator • All Categories',
    group: 'System',
    status: 'active',
    description: 'Maps your category tree to Playbook scopes (L0 → L3)',
    phase: 'Shadow',
    rampDay: 9,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'category-sme',
    initials: 'SME',
    name: 'Category SME',
    meta: 'Advisory • Per L1 node',
    group: 'Intelligence',
    status: 'active',
    description: 'Loads the category archetype (one of seven behaviours)',
    phase: 'Shadow',
    rampDay: 9,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'pricing-repricing',
    initials: 'PR',
    name: 'Pricing & Repricing',
    meta: 'Margin • Sales',
    group: 'Growth',
    status: 'active',
    description: 'Learns elasticity per SKU from 24-month history in Shadow',
    phase: 'Shadow',
    /* Ramp complete — this one has cleared its gates and sits on the Graduate
       rung, so "Assign to workspace" is available on its panel. */
    rampDay: 14,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'bidding-ads',
    initials: 'BD',
    name: 'Bidding & Ads',
    meta: 'Ads',
    group: 'Growth',
    status: 'active',
    description: 'Audits campaign structure; maps spend to pricing roles',
    phase: 'Shadow',
    rampDay: 9,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'buy-box-defence',
    initials: 'BX',
    name: 'Buy Box Defence',
    meta: 'Sales • Per marketplace',
    group: 'Growth',
    status: 'active',
    description: 'Watches win rate and competitor undercuts on every listing',
    phase: 'Shadow',
    rampDay: 11,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'listing-content',
    initials: 'LX',
    name: 'Listing & Content',
    meta: 'Sales • Conversion',
    group: 'Growth',
    status: 'active',
    description: 'Scores title, bullets and imagery against converting peers',
    phase: 'Shadow',
    rampDay: 7,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'demand-forecast',
    initials: 'FA',
    name: 'Demand Forecast',
    meta: 'Plan of Record • All SKUs',
    group: 'Intelligence',
    status: 'active',
    description: 'Runs the forecast consensus every other agent reads from',
    phase: 'Shadow',
    /* Ramp complete — see Pricing & Repricing above. */
    rampDay: 14,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'replenishment',
    initials: 'RP',
    name: 'Replenishment',
    meta: 'Inventory • Working capital',
    group: 'Operations',
    status: 'active',
    description: 'Sets reorder points and quantities; owns expedite calls',
    phase: 'Shadow',
    rampDay: 9,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'supplier-manager',
    initials: 'SM',
    name: 'Supplier Manager',
    meta: 'Operations • Landed cost',
    group: 'Operations',
    status: 'active',
    description: 'Tracks supplier terms, MOQ drift and landed-cost truth',
    phase: 'Shadow',
    rampDay: 6,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'fee-recovery',
    initials: 'FE',
    name: 'Fee Recovery',
    meta: 'Margin • Reimbursements',
    group: 'Finance',
    status: 'active',
    description: 'Audits dimensional and referral fees, drafts the case body',
    phase: 'Shadow',
    rampDay: 10,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'cash-conversion',
    initials: 'CC',
    name: 'Cash Conversion',
    meta: 'Cash • CM3 truth',
    group: 'Finance',
    status: 'active',
    description: 'Watches payout pacing and working capital tied up in stock',
    phase: 'Shadow',
    rampDay: 9,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'payout-reconciliation',
    initials: 'PY',
    name: 'Payout Reconciliation',
    meta: 'Cash • Per marketplace',
    group: 'Finance',
    status: 'active',
    description: 'Reconciles settlements against expected deposits line by line',
    phase: 'Shadow',
    rampDay: 8,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'keyword-research',
    initials: 'KW',
    name: 'Keyword Research',
    meta: 'Ads • Search terms',
    group: 'Intelligence',
    status: 'standby',
    description: 'Mines search terms, match types and negation ladders',
    phase: 'Standby',
    rampDay: 0,
    rampTotal: 14,
    startsAt: 'Observe',
  },
  {
    id: 'guardrail-monitor',
    initials: 'GM',
    name: 'Guardrail Monitor',
    meta: 'System • Policy',
    group: 'System',
    status: 'standby',
    description: 'Holds any action that breaches a rule you set in Guardrails',
    phase: 'Standby',
    rampDay: 0,
    rampTotal: 14,
    startsAt: 'Observe',
  },
];

/**
 * Has this specialist finished its shadow period?
 *
 * `rampDay` / `rampTotal` are the steps shown on the card ("Day 9 of 14"), so
 * this is the same question the user is answering by reading it.
 */
export const isRampComplete = (agent) =>
  Number(agent?.rampTotal) > 0 && Number(agent?.rampDay) >= Number(agent?.rampTotal);

/**
 * The badge a roster card or profile shows.
 *
 * A specialist is Active only once its ramp is done — everyone starts in Shadow
 * and serves `rampTotal` days before it is allowed to act on its own, so a card
 * reading "Day 9 of 14" and "Active" in the same breath contradicts itself.
 *
 * `standby` keeps its own label rather than folding into Inactive: those are
 * shelved specialists rather than ones mid-ramp, and the header tile counts
 * them separately.
 */
export const agentStatusLabel = (agent) => {
  if (agent?.status === 'standby') return 'Standby';
  return isRampComplete(agent) ? 'Active' : 'Inactive';
};

/**
 * Header tiles, counted rather than hardcoded so they always match what is on
 * screen.
 *
 * "Active" counts *graduated* specialists, not roster entries: everyone starts
 * in Shadow, so a first-time visitor correctly reads 0 Active and gains one per
 * graduation.
 */
export const agentSummary = (graduatedIds = [], roster = AGENTS_ROSTER) => [
  {
    key: 'total',
    value: roster.length,
    label: 'Total specialists',
    icon: 'fa-cubes',
    tone: 'indigo',
  },
  {
    key: 'active',
    value: graduatedIds.length,
    label: 'Active',
    icon: 'fa-circle-check',
    tone: 'emerald',
  },
  {
    key: 'standby',
    value: roster.filter((a) => a.status === 'standby').length,
    label: 'Standby',
    icon: 'fa-bookmark',
    tone: 'indigo',
  },
];
