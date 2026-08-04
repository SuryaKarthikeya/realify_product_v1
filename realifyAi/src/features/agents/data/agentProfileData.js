import { formatSignedMoney } from '@/utils/formatters';

/**
 * Content for the full agent profile page.
 *
 * `agentProfile(agent)` merges a per-agent override over a derived default, so
 * every specialist opens a populated profile rather than only the ones written
 * out by hand.
 */

export const PROFILE_TABS = ['Overview', 'Rhythm', 'Triggers', 'Safeguards', 'To-dos', 'Log'];

/** Status pill tones used by the activity feed. */
export const ACTIVITY_TONES = {
  gain: { chip: 'text-emerald-600 dark:text-emerald-400', icon: 'fa-arrow-trend-up', bg: 'bg-emerald-50 dark:bg-emerald-950/40', fg: 'text-emerald-600 dark:text-emerald-400' },
  attention: { chip: 'text-amber-600 dark:text-amber-400', icon: 'fa-circle-exclamation', bg: 'bg-amber-50 dark:bg-amber-950/40', fg: 'text-amber-600 dark:text-amber-400' },
  secured: { chip: 'text-emerald-600 dark:text-emerald-400', icon: 'fa-check', bg: 'bg-emerald-50 dark:bg-emerald-950/40', fg: 'text-emerald-600 dark:text-emerald-400' },
  review: { chip: 'text-violet-600 dark:text-violet-400', icon: 'fa-star', bg: 'bg-violet-50 dark:bg-violet-950/40', fg: 'text-violet-600 dark:text-violet-400' },
  info: { chip: 'text-gray-500 dark:text-slate-400', icon: 'fa-circle-pause', bg: 'bg-gray-100 dark:bg-slate-800', fg: 'text-gray-400 dark:text-slate-500' },
};

/** The four-stage cadence every specialist runs on. */
export const EXECUTION_RHYTHM = [
  { key: 'annual', label: 'Annual Blueprint', state: 'DONE', description: 'Sets strategic pricing direction' },
  { key: 'seasonal', label: 'Seasonal Tune', state: 'ONGOING', description: 'Adjusts for season & demand shifts' },
  { key: 'monthly', label: 'Monthly Refresh', state: 'ONGOING', description: 'Updates baselines & thresholds' },
  { key: 'daily', label: 'Daily Run', state: 'LIVE', description: 'Executes real-time decisions' },
];

export const RHYTHM_STATE_TONES = {
  DONE: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400',
  ONGOING: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  LIVE: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400',
};

/** Peers this specialist coordinates with. */
export const CONNECTED_AGENTS = [
  { key: 'campaign', label: 'Campaign Optimizer', icon: 'fa-chart-simple', bg: 'bg-emerald-500' },
  { key: 'stock', label: 'Stock Manager', icon: 'fa-box', bg: 'bg-orange-500' },
  { key: 'demand', label: 'Demand Forecaster', icon: 'fa-bell', bg: 'bg-indigo-500' },
  { key: 'category', label: 'Category Advisor', icon: 'fa-user', bg: 'bg-violet-500' },
  { key: 'finance', label: 'Finance Controller', icon: 'fa-dollar-sign', bg: 'bg-slate-800' },
];

export const CONNECTED_OVERFLOW = 5;

/* ── per-agent content ── */

const PROFILE_OVERRIDES = {
  'pricing-repricing': {
    tagline: 'Runs like a GM',
    since: 'Mar 2026',
    decisionsLogged: 1240,
    summary:
      'Continuously scanning 12,430+ SKUs to uncover pricing opportunities, identify competitive gaps, and protect profit margins. Delivering real-time insights that help optimise pricing strategies and maximise business profitability.',
    mission: 'Deliver the right price for every customer while safeguarding CM3.',
    stats: [
      { key: 'adjustments', value: '38', label: 'Adjustments made today', icon: 'fa-arrow-trend-up', tone: 'indigo' },
      { key: 'risks', value: '4', label: 'Risks flagged today', icon: 'fa-triangle-exclamation', tone: 'amber' },
      { key: 'suggestions', value: '2', label: 'Suggestions awaiting action', icon: 'fa-lightbulb', tone: 'violet' },
      { key: 'value', value: formatSignedMoney(14200), label: 'Incremental value unlocked today', icon: 'fa-sack-dollar', tone: 'emerald' },
    ],
    activity: [
      { time: '09:24 AM', title: 'Raised prices on 12 SKUs to improve margin', sub: 'Countered competitor price pressure', tone: 'gain', value: formatSignedMoney(4800) },
      { time: '09:12 AM', title: 'Detected competitor price gaps on 4 SKUs', sub: 'Avg gap > 5% vs similar items', tone: 'attention', badge: 'Attention' },
      { time: '08:58 AM', title: 'Secured margin on 4 fast-moving SKUs', sub: 'Staying within pricing guardrails', tone: 'secured', value: formatSignedMoney(2100) },
      { time: '08:32 AM', title: 'Proposed price uplift for 8 SKUs', sub: 'High conversion potential identified', tone: 'review', badge: 'Review' },
      { time: '08:07 AM', title: 'Paused repricing on 3 SKUs', sub: 'Low stock availability', tone: 'info', badge: 'Info' },
    ],
    settings: [
      { key: 'mode', icon: 'fa-circle-check', label: 'Decision mode', value: 'Margin Focus · Growth Support' },
      { key: 'safety', icon: 'fa-shield-halved', label: 'Safety net', value: 'On', dot: 'emerald' },
      { key: 'guardrails', icon: 'fa-clipboard', label: 'Pricing guardrails', value: '± 5% from benchmark' },
      { key: 'promo', icon: 'fa-circle-minus', label: 'Promo spend limit', value: '68% left' },
      { key: 'next', icon: 'fa-clock', label: 'Next run', value: 'Today, 6:00 AM' },
      { key: 'state', icon: 'fa-gear', label: 'System state', value: 'OPTIMAL', chip: 'emerald' },
    ],
  },
  'bidding-ads': {
    tagline: 'Runs like a media buyer',
    since: 'Apr 2026',
    decisionsLogged: 890,
    summary:
      'Auditing campaign structure across every active channel, mapping ad spend to the pricing role of each SKU, and holding TACoS under its category threshold. Surfacing bid and budget moves before ROAS decays.',
    mission: 'Buy demand that pays for itself, and stop the spend that does not.',
    stats: [
      { key: 'adjustments', value: '52', label: 'Bid changes proposed today', icon: 'fa-arrow-trend-up', tone: 'indigo' },
      { key: 'risks', value: '6', label: 'Fatiguing creatives flagged', icon: 'fa-triangle-exclamation', tone: 'amber' },
      { key: 'suggestions', value: '3', label: 'Suggestions awaiting action', icon: 'fa-lightbulb', tone: 'violet' },
      { key: 'value', value: formatSignedMoney(9600), label: 'Wasted spend recovered today', icon: 'fa-sack-dollar', tone: 'emerald' },
    ],
    activity: [
      { time: '09:31 AM', title: 'Negated 14 non-converting search terms', sub: 'Zero orders across 30 days', tone: 'gain', value: formatSignedMoney(3200) },
      { time: '09:05 AM', title: 'TACoS crossed 18.4% on 2 campaigns', sub: 'Above the 12% category floor', tone: 'attention', badge: 'Attention' },
      { time: '08:44 AM', title: 'Held ROAS above 4.2x on branded terms', sub: 'Bid ladder unchanged', tone: 'secured', value: formatSignedMoney(1800) },
      { time: '08:20 AM', title: 'Proposed budget shift into exact match', sub: '8.4x ROAS on an un-capped campaign', tone: 'review', badge: 'Review' },
      { time: '07:58 AM', title: 'Paused 3 creatives at frequency 7.8', sub: 'Click-through down 38%', tone: 'info', badge: 'Info' },
    ],
    settings: [
      { key: 'mode', icon: 'fa-circle-check', label: 'Decision mode', value: 'Efficiency Focus · Rank Guard' },
      { key: 'safety', icon: 'fa-shield-halved', label: 'Safety net', value: 'On', dot: 'emerald' },
      { key: 'guardrails', icon: 'fa-clipboard', label: 'Bid guardrails', value: '± 15% per ladder step' },
      { key: 'promo', icon: 'fa-circle-minus', label: 'Daily budget limit', value: '41% left' },
      { key: 'next', icon: 'fa-clock', label: 'Next run', value: 'Today, 6:00 AM' },
      { key: 'state', icon: 'fa-gear', label: 'System state', value: 'OPTIMAL', chip: 'emerald' },
    ],
  },
};

/**
 * Profile content for one agent.
 *
 * The default is derived from the roster entry so an unspecified specialist
 * still reads as a real agent — its own description becomes the summary rather
 * than the page showing empty sections.
 */
export const agentProfile = (agent) => {
  if (!agent) return null;
  const o = PROFILE_OVERRIDES[agent.id] || {};

  return {
    tagline: o.tagline || agent.hireTagline || `Runs the ${agent.meta.split(' • ')[0]} desk`,
    since: o.since || 'Mar 2026',
    decisionsLogged: o.decisionsLogged ?? 240,
    summary:
      o.summary ||
      `${agent.description}. Operating across ${agent.meta}, surfacing every decision with the evidence behind it and escalating anything outside its Playbook.`,
    mission: o.mission || `${agent.description}, without ever writing outside the Playbook.`,
    stats: o.stats || [
      { key: 'adjustments', value: '18', label: 'Proposals made today', icon: 'fa-arrow-trend-up', tone: 'indigo' },
      { key: 'risks', value: '2', label: 'Risks flagged today', icon: 'fa-triangle-exclamation', tone: 'amber' },
      { key: 'suggestions', value: '1', label: 'Suggestions awaiting action', icon: 'fa-lightbulb', tone: 'violet' },
      { key: 'value', value: formatSignedMoney(5400), label: 'Incremental value unlocked today', icon: 'fa-sack-dollar', tone: 'emerald' },
    ],
    activity: o.activity || [
      { time: '09:20 AM', title: agent.description, sub: `Within ${agent.meta}`, tone: 'gain', value: formatSignedMoney(2400) },
      { time: '09:02 AM', title: 'Flagged a threshold crossing for review', sub: 'Awaiting your grade on the tape', tone: 'attention', badge: 'Attention' },
      { time: '08:41 AM', title: 'Held every hard gate this run', sub: 'No breach proposed', tone: 'secured', value: formatSignedMoney(900) },
      { time: '08:15 AM', title: 'Drafted a proposal for the next loop', sub: 'Evidence attached', tone: 'review', badge: 'Review' },
      { time: '07:52 AM', title: 'Skipped a run on stale data', sub: 'Waiting on the next pull', tone: 'info', badge: 'Info' },
    ],
    settings: o.settings || [
      { key: 'mode', icon: 'fa-circle-check', label: 'Decision mode', value: 'Balanced · Evidence First' },
      { key: 'safety', icon: 'fa-shield-halved', label: 'Safety net', value: 'On', dot: 'emerald' },
      { key: 'guardrails', icon: 'fa-clipboard', label: 'Guardrails', value: 'Playbook defaults' },
      { key: 'promo', icon: 'fa-circle-minus', label: 'Budget limit', value: 'Not set' },
      { key: 'next', icon: 'fa-clock', label: 'Next run', value: 'Today, 6:00 AM' },
      { key: 'state', icon: 'fa-gear', label: 'System state', value: 'OPTIMAL', chip: 'emerald' },
    ],
  };
};

/* ── Triggers tab: the 5-signal engine ── */

/** Domain chip tones used by the signal cards. */
export const SIGNAL_DOMAIN_TONES = {
  Sales: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400',
  Margin: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400',
  Inventory: 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400',
  Ads: 'bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400',
  Cash: 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400',
};

/**
 * Hard gates. Enforced server-side and independent of the trust dial, so they
 * hold at every autonomy level — including Act.
 */
export const HARD_GATES = [
  'Cover-block (Tier-1)',
  'CM3 floor per SKU',
  'MAP',
  '15% max move',
  '1 change / SKU / day',
  'Blast radius 20 SKUs',
];

/**
 * The five signals a specialist watches, each read as:
 *   source → trigger → role-steered response → auto / human line
 *
 * `auto` is what the agent may do unattended; `handoff` is the boundary where it
 * must come back to a person. A signal without a handoff line would imply the
 * agent never escalates, which no specialist is allowed to do.
 */
const TRIGGERS_BY_AGENT = {
  'pricing-repricing': [
    {
      key: 'competitive',
      title: 'Competitive movement',
      domain: 'Sales',
      icon: 'fa-arrow-trend-up',
      source: 'competitor tracking (Keepa)',
      trigger: 'rival moves a comparison KPI',
      response: 'track, react, recalibrate pricing to stay ahead',
      auto: 'in-band follow',
      handoff: 'below floor or MAP',
    },
    {
      key: 'margin',
      title: 'Margin resilience',
      domain: 'Margin',
      icon: 'fa-percent',
      source: 'CM3 & TACoS',
      trigger: 'CM3 drifts below target / TACoS above target',
      response: 'adjust price, bundle, or mix to restore margin',
      auto: 'in-band adjust',
      handoff: 'structural or category breach',
    },
    {
      key: 'velocity',
      title: 'Inventory velocity',
      domain: 'Inventory',
      icon: 'fa-box',
      source: 'STR vs plan curve',
      trigger: 'STR off the planned lifecycle curve',
      response: 'balance sell-through with healthy coverage',
      auto: 'step within budget',
      handoff: 'clearance or overshoot',
    },
    {
      key: 'promo',
      title: 'Promotional window',
      domain: 'Ads',
      icon: 'fa-bullhorn',
      source: 'event calendar, deal asks',
      trigger: 'window opens / rival promotes a KPI',
      response: 'align promotions, price depth, and ad support',
      auto: 'pre-planned in ceilings',
      handoff: 'doorbuster / below-floor / breach',
    },
    {
      key: 'in-stock',
      title: 'In-stock position — HARD GATE',
      domain: 'Inventory',
      icon: 'fa-shield-halved',
      source: 'WOC, OOS risk, Buy Box',
      trigger: 'WOC < cover-block / overstock / KVI OOS',
      response: 'gate price changes based on stock risk',
      auto: 'cover-block raise / hold',
      handoff: 'KVI OOS risk / overstock clearance',
    },
  ],
  'bidding-ads': [
    {
      key: 'pacing',
      title: 'Budget pacing',
      domain: 'Ads',
      icon: 'fa-gauge-high',
      source: 'spend vs monthly plan',
      trigger: 'pacing drifts ±15% off plan',
      response: 'rebalance budget across campaigns and match types',
      auto: 'in-plan reallocation',
      handoff: 'total budget increase',
    },
    {
      key: 'efficiency',
      title: 'Ad efficiency',
      domain: 'Margin',
      icon: 'fa-percent',
      source: 'TACoS & ROAS',
      trigger: 'TACoS above ceiling / ROAS below floor',
      response: 'lower bids on non-branded, protect branded position',
      auto: 'bid step within ladder',
      handoff: 'campaign pause or restructure',
    },
    {
      key: 'search-terms',
      title: 'Search term drift',
      domain: 'Sales',
      icon: 'fa-magnifying-glass',
      source: 'search term report',
      trigger: 'non-converting terms clear the spend threshold',
      response: 'negate waste, promote converters to exact match',
      auto: 'negation of zero-order terms',
      handoff: 'negating a branded term',
    },
    {
      key: 'creative',
      title: 'Creative fatigue',
      domain: 'Ads',
      icon: 'fa-images',
      source: 'frequency & CTR curve',
      trigger: 'frequency > 7 with CTR decaying',
      response: 'rotate the creative set before ROAS decays',
      auto: 'rotate within approved set',
      handoff: 'new creative production',
    },
    {
      key: 'stock-gate',
      title: 'Stock coverage — HARD GATE',
      domain: 'Inventory',
      icon: 'fa-shield-halved',
      source: 'WOC, OOS risk',
      trigger: 'WOC < cover-block on an advertised SKU',
      response: 'stop spending into a SKU that cannot ship',
      auto: 'pause on OOS risk',
      handoff: 'resuming spend after restock',
    },
  ],
};

/**
 * Signals for one agent.
 *
 * The derived default keeps the shape — source, trigger, response and both
 * autonomy lines — so an agent with no hand-written engine still reads as a real
 * one rather than showing an empty tab.
 */
export const agentTriggers = (agent) => {
  if (!agent) return [];
  if (TRIGGERS_BY_AGENT[agent.id]) return TRIGGERS_BY_AGENT[agent.id];

  const grain = agent.meta.split(' • ')[0];
  return [
    {
      key: 'threshold',
      title: 'Threshold crossing',
      domain: 'Sales',
      icon: 'fa-arrow-trend-up',
      source: `${grain} telemetry`,
      trigger: 'a watched metric crosses its band',
      response: agent.description,
      auto: 'in-band correction',
      handoff: 'outside the Playbook band',
    },
    {
      key: 'margin',
      title: 'Margin resilience',
      domain: 'Margin',
      icon: 'fa-percent',
      source: 'CM3 & contribution',
      trigger: 'contribution drifts below target',
      response: 'restore margin without breaching a hard gate',
      auto: 'in-band adjust',
      handoff: 'structural or category breach',
    },
    {
      key: 'velocity',
      title: 'Coverage & velocity',
      domain: 'Inventory',
      icon: 'fa-box',
      source: 'cover vs plan curve',
      trigger: 'cover falls off the planned curve',
      response: 'balance sell-through against healthy coverage',
      auto: 'step within budget',
      handoff: 'clearance or overshoot',
    },
    {
      key: 'calendar',
      title: 'Calendar events',
      domain: 'Ads',
      icon: 'fa-bullhorn',
      source: 'event calendar',
      trigger: 'a planned window opens',
      response: 'align activity with the window',
      auto: 'pre-planned in ceilings',
      handoff: 'anything unplanned',
    },
    {
      key: 'gate',
      title: 'Policy gate — HARD GATE',
      domain: 'Inventory',
      icon: 'fa-shield-halved',
      source: 'guardrail evaluation',
      trigger: 'an action would breach a hard gate',
      response: 'hold the action and open a case',
      auto: 'hold',
      handoff: 'every breach, at every trust level',
    },
  ];
};
