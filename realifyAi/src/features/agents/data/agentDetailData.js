import { AGENTS_ROSTER } from '@/features/agents/data/agentsData';

/**
 * Content for the agent detail panel and the "Live Now" strip.
 *
 * `agentDetail(agent)` merges a per-agent override over a derived default, so
 * every one of the 14 specialists opens a populated panel rather than only the
 * ones that were written out by hand.
 */

/** The trust dial. Every hire starts on the first rung; the rest are earned. */
export const TRUST_RUNGS = [
  { key: 'learning', label: 'Learning', sub: '(Observe)' },
  { key: 'baseline', label: 'Baseline', sub: '(Trained)' },
  { key: 'shadow', label: 'Shadow', sub: '(Review Mode)' },
  { key: 'scope', label: 'Scope', sub: '(Limited Write)' },
  { key: 'graduate', label: 'Graduate', sub: '(Autonomous)' },
];

/** The rung a specialist has to reach before it can be handed real work. */
const GRADUATE_INDEX = TRUST_RUNGS.findIndex((r) => r.key === 'graduate');

/** Gates that must clear before the dial advances. */
export const GRADUATION_GATES = [
  { icon: 'fa-user-check', label: '5 more human reviews' },
  { icon: 'fa-circle-half-stroke', label: '≥ 90% agreement on proposals' },
  { icon: 'fa-check', label: 'Manager approval' },
];

/**
 * What a graduated specialist is doing once it is live.
 *
 * Only graduated agents appear in the Live Now strip, so this is display copy
 * for that state — not what decides whether the strip renders.
 * `trend` is a sparkline series — plain numbers, drawn as an inline SVG.
 */
const LIVE_TASKS = {
  'pricing-repricing': {
    label: 'Pricing & Margin',
    verb: 'Optimizing pricing for',
    subject: '12 SKUs',
    updated: '18s ago',
    tone: 'indigo',
    trend: [7, 5, 9, 6, 11, 8, 13, 10, 15, 12, 17],
  },
  'bidding-ads': {
    label: 'Campaign Manager',
    verb: 'Simulating ACOS for',
    subject: '8 campaigns',
    updated: '33s ago',
    tone: 'emerald',
    trend: [6, 9, 7, 12, 9, 14, 11, 15, 13, 17, 15],
  },
  'replenishment': {
    label: 'Inventory Agent',
    verb: 'Forecasting demand for',
    subject: '320 products',
    updated: '45s ago',
    tone: 'amber',
    trend: [11, 9, 12, 8, 10, 7, 11, 9, 12, 10, 13],
  },
  'demand-forecast': {
    label: 'Research Agent',
    verb: 'Scanning market for',
    subject: '3 opportunities',
    updated: '1m ago',
    tone: 'violet',
    trend: [8, 12, 9, 14, 10, 13, 11, 16, 12, 15, 13],
  },
};

/** Sparkline palette, cycled for agents with no hand-written live copy. */
const LIVE_TONES = ['indigo', 'emerald', 'amber', 'violet'];

/** Plausible series so a generated card still draws a real sparkline. */
const defaultTrend = (seed) =>
  Array.from({ length: 11 }, (_, i) => 10 + ((seed * 7 + i * 5) % 9) + (i % 2 ? 2 : 0));

/**
 * The specialists the user has graduated, most recent first.
 *
 * Newest first so the one just assigned lands at the head of the strip instead
 * of at the end of a row the user has to scroll to find.
 *
 * This is what the Live Now strip renders — nothing else. A first-time visitor
 * has graduated nobody, so the strip is empty and the page shows the five-step
 * hire rail in its place. Agents without hand-written live copy get a derived
 * card, so any of the 14 can graduate and still appear correctly.
 */
export const liveAgents = (graduatedIds = [], roster = AGENTS_ROSTER) =>
  [...graduatedIds]
    .reverse()
    .map((id) => roster.find((a) => a.id === id))
    .filter(Boolean)
    .map((a, idx) => ({
      ...a,
      live: LIVE_TASKS[a.id] || {
        label: a.name,
        verb: 'Working across',
        subject: a.meta.split(' • ')[0],
        updated: 'just now',
        tone: LIVE_TONES[idx % LIVE_TONES.length],
        trend: defaultTrend(idx + 1),
      },
    }));

/** Per-agent panel copy. Anything omitted falls back to the derived default. */
const DETAIL_OVERRIDES = {
  'category-manager': {
    hiredOn: '21 Jul',
    weekly: { proposed: 31, accepted: 27, approval: '87%' },
    responsibilities: [
      "Owns the queue's priorities across all lenses",
      'Runs the category like a GMM',
      'Coordinates work across specialist agents',
      'Ensures playbooks stay accurate and current',
    ],
    workingOn: [
      { label: 'Mapping category tree to Playbook scopes (L0 → L3)', state: 'done', status: 'In progress' },
      { label: 'Drafting workspace Playbook v1 with SME archetypes', state: 'active', status: 'In progress' },
      { label: 'Sequencing which agents graduate first', state: 'waiting', status: 'Waiting' },
    ],
    afterGraduation: [
      'Automatically prioritizes actions queue across all lenses',
      'Chairs the monthly clock — Playbook revisions as Suggest-only',
      'Escalates cross-desk conflicts to the Arbiter with context',
      'Drives outcomes and performance reviews',
    ],
  },
  'pricing-repricing': {
    hiredOn: '18 Jul',
    weekly: { proposed: 44, accepted: 38, approval: '86%' },
    responsibilities: [
      'Holds the CM3 floor on every repricing decision',
      'Learns elasticity per SKU from 24 months of history',
      'Defends the Buy Box without trading away margin',
      'Respects MAP and promo windows as hard gates',
    ],
    workingOn: [
      { label: 'Fitting elasticity curves across 12 live SKUs', state: 'done', status: 'In progress' },
      { label: 'Proposing floor changes for review', state: 'active', status: 'In progress' },
      { label: 'Awaiting competitor scrape refresh', state: 'waiting', status: 'Waiting' },
    ],
    afterGraduation: [
      'Reprices inside the approved band without an ask',
      'Opens a case when a floor breach is unavoidable',
      'Coordinates promo timing with the Campaign Manager',
      'Reports realised margin against every projection',
    ],
  },
  'bidding-ads': {
    hiredOn: '19 Jul',
    weekly: { proposed: 52, accepted: 41, approval: '79%' },
    responsibilities: [
      'Maps ad spend to the pricing role of each SKU',
      'Keeps TACoS under the category threshold',
      'Mines search terms and maintains negation ladders',
      'Flags creative fatigue before ROAS decays',
    ],
    workingOn: [
      { label: 'Auditing campaign structure across 8 campaigns', state: 'done', status: 'In progress' },
      { label: 'Simulating ACOS under three bid ladders', state: 'active', status: 'In progress' },
      { label: 'Waiting on placement report refresh', state: 'waiting', status: 'Waiting' },
    ],
    afterGraduation: [
      'Adjusts bids inside the approved ladder autonomously',
      'Pauses fatigued creative and proposes replacements',
      'Rebalances budget across channels on evidence',
      'Defends TACoS targets in the monthly review',
    ],
  },
};

/**
 * Panel content for one agent.
 *
 * The default is derived from the roster entry so an agent with no override
 * still reads as a real specialist — its own description becomes the first
 * responsibility rather than the panel showing an empty section.
 */
export const agentDetail = (agent) => {
  if (!agent) return null;
  const o = DETAIL_OVERRIDES[agent.id] || {};

  const trustIndex = agent.status === 'standby'
    ? 0
    : agent.rampDay >= agent.rampTotal
      ? GRADUATE_INDEX
      : 2;

  return {
    hiredOn: o.hiredOn || '21 Jul',
    phase: agent.phase,
    rampDay: agent.rampDay,
    rampTotal: agent.rampTotal,
    weekly: o.weekly || { proposed: 18, accepted: 15, approval: '83%' },
    responsibilities: o.responsibilities || [
      agent.description,
      `Operates within the ${agent.meta} grain`,
      'Surfaces every decision with its supporting evidence',
      'Escalates anything outside its Playbook',
    ],
    workingOn: o.workingOn || [
      { label: `Calibrating against 24 months of history`, state: 'done', status: 'In progress' },
      { label: agent.description, state: 'active', status: 'In progress' },
      { label: 'Awaiting the next scheduled data pull', state: 'waiting', status: 'Waiting' },
    ],
    afterGraduation: o.afterGraduation || [
      'Acts inside the Playbook without an approval step',
      'Opens a case whenever a hard gate would be breached',
      'Coordinates with adjacent specialists automatically',
      'Reports realised outcomes against every projection',
    ],
    /* The dial position follows the ramp: a standby hire has not started, a
       completed ramp has cleared its gates and sits on Graduate, and anything
       mid-shadow sits on the Shadow rung. */
    trustIndex,
    /* Reaching Graduate is what unlocks "Assign to workspace" — until then the
       specialist is still proposing for review and has nothing to hand over. */
    canGraduate: trustIndex >= GRADUATE_INDEX,
  };
};

/* ── Live-agent panel ── */

export const LIVE_PANEL_TABS = ['Overview', 'Goals', 'Metrics', 'Activity'];

/**
 * Panel content for a specialist that has graduated and is running.
 *
 * A live agent is reported on differently from one still in Shadow: the ramp and
 * graduation gates no longer matter, so this shows its goal, focus areas, key
 * metrics and what it has actually done. Anything omitted derives from the
 * roster entry, so any of the 14 can graduate and still open a full panel.
 */
const LIVE_PANEL_OVERRIDES = {
  'pricing-repricing': {
    goal: 'Right price per role; CM3 defended',
    focusAreas: ['Price Optimization', 'Margin Expansion', 'Role Pricing', 'CM3 Defense'],
    impact: 'High',
    frequency: 'Daily',
    confidence: 88,
    recentActions: [
      { label: 'Adjusted price on 12 SKUs', when: '18s ago', icon: 'fa-check' },
      { label: 'Detected margin leakage in 3 categories', when: '1d ago', icon: 'fa-check' },
      { label: 'Recommended price increase for 8 SKUs', when: '2d ago', icon: 'fa-chart-simple' },
    ],
  },
  'bidding-ads': {
    goal: 'Spend that pays for itself; TACoS held',
    focusAreas: ['Bid Ladders', 'Search Term Mining', 'Creative Rotation', 'TACoS Guard'],
    impact: 'High',
    frequency: 'Hourly',
    confidence: 82,
    recentActions: [
      { label: 'Negated 14 non-converting search terms', when: '33s ago', icon: 'fa-check' },
      { label: 'Rotated 3 fatiguing creatives', when: '6h ago', icon: 'fa-check' },
      { label: 'Proposed budget shift into exact match', when: '1d ago', icon: 'fa-chart-simple' },
    ],
  },
  'replenishment': {
    goal: 'Cover held without tying up cash',
    focusAreas: ['Reorder Points', 'Expedite Calls', 'Cover Bands', 'Working Capital'],
    impact: 'Medium',
    frequency: 'Daily',
    confidence: 79,
    recentActions: [
      { label: 'Raised reorder point on 9 SKUs', when: '45s ago', icon: 'fa-check' },
      { label: 'Flagged 2 SKUs at stockout risk', when: '4h ago', icon: 'fa-check' },
      { label: 'Recommended PO for 500 units', when: '2d ago', icon: 'fa-chart-simple' },
    ],
  },
  'demand-forecast': {
    goal: 'One forecast every desk plans against',
    focusAreas: ['Plan of Record', 'Seasonality', 'Consensus', 'Signal Quality'],
    impact: 'High',
    frequency: 'Weekly',
    confidence: 91,
    recentActions: [
      { label: 'Published this week’s Plan of Record', when: '1m ago', icon: 'fa-check' },
      { label: 'Revised 3 seasonality curves', when: '2d ago', icon: 'fa-check' },
      { label: 'Flagged a demand break on 3 SKUs', when: '3d ago', icon: 'fa-chart-simple' },
    ],
  },
};

/** Sparkline series for the Impact tile, and bars for Frequency. */
export const IMPACT_TREND = [6, 8, 7, 11, 9, 13, 11, 15, 14, 17];
export const FREQUENCY_BARS = [5, 8, 11, 7, 13];

export const liveAgentPanel = (agent) => {
  if (!agent) return null;
  const o = LIVE_PANEL_OVERRIDES[agent.id] || {};
  const grain = agent.meta.split(' • ')[0];

  return {
    goal: o.goal || `${grain} held inside the Playbook`,
    /* Derived focus areas stay grounded in the roster entry rather than being
       invented, so an unlisted agent still reads truthfully. */
    focusAreas: o.focusAreas || [grain, agent.group, 'Evidence First', 'Guardrails'],
    impact: o.impact || 'Medium',
    frequency: o.frequency || 'Daily',
    confidence: o.confidence ?? 80,
    recentActions: o.recentActions || [
      { label: agent.description, when: 'just now', icon: 'fa-check' },
      { label: `Held every hard gate across ${grain}`, when: '1d ago', icon: 'fa-check' },
      { label: 'Drafted a proposal for review', when: '2d ago', icon: 'fa-chart-simple' },
    ],
  };
};
