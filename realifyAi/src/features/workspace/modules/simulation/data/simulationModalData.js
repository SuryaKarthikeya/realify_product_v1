// src/features/intel/shared/data/simulationModalData.js
// Dummy data + math for the "Simulate" modal (Realify Signal · AI Simulation).
//
// Every displayed number is derived from a small set of base inputs per insight
// (gap value, capture %, margin %, ramp days). This keeps the dummy data compact
// and lets the modal recompute live when the user edits assumptions / picks a
// preset and clicks "Re-simulate".

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

import { PRODUCT_CATEGORIES } from '@/constants/filterOptions';

export const formatCurrency = (symbol, value) => {
  const rounded = Math.round(value);
  if (symbol === '$') return `$${rounded.toLocaleString('en-IN')}`;
  return `${symbol}${rounded.toLocaleString('en-US')}`;
};

const CATEGORY_LABELS = {
  ...Object.fromEntries(PRODUCT_CATEGORIES.map((c) => [c.value, c.label])),
  'industry-news': 'Industry News',
};

const categoryLabel = (key) => CATEGORY_LABELS[key] || 'your catalog';

// ---------------------------------------------------------------------------
// Per-insight base inputs (dummy). Everything else is computed from these.
// ---------------------------------------------------------------------------

const DEFAULT_INPUT = {
  signalLabel: 'Realify Signal · AI Simulation',
  title: 'A niche cleared your opportunity threshold: score 84.',
  badge: 'L1 · projection · directional',
  currency: '$',
  gapValue: 187500,
  capturePct: 10,
  marginPct: 20,
  rampDays: 90,
  intervention:
    'Enter/extend assortment to capture ~10% of a ~{gap}/mo gap at ~20% margin. Directional: the gap and entry costs are estimates.',
  projectionMetric: 'Contribution / mo',
  whatCouldGoWrong: [
    {
      title: 'Entry costs not modeled',
      description: "launch ads, inventory, and content spend aren't in this figure.",
    },
    {
      title: 'Capture slower/smaller than assumed',
      description: 'a new listing ramps slowly and may take less than 10% of the gap.',
    },
  ],
  monitoring: {
    metric: 'New-SKU velocity',
    detail: 'expected vs assumption',
    tripwire: 'below assumed share by day 60; re-scope or exit',
    days: [7, 15, 30, 60],
  },
  formulaExpression: 'gap value × capture share × est. margin, ramped over the launch',
  formulaGapLabel: 'Gap value / mo',
};

const BASE_BY_ID = {
  'insight-sales-1': {
    title: 'A concentration risk cleared your watch line in {category}: score 82.',
    currency: '$',
    gapValue: 2020000,
    intervention:
      'Diversify demand so ~10% of a ~{gap}/mo concentration eases at ~20% margin. Directional: the exposure and offsets are estimates.',
    projectionMetric: 'Contribution / mo',
    whatCouldGoWrong: [
      { title: 'Concentration persists', description: 'standing up alternative SKUs is a multi-month effort; exposure lingers.' },
      { title: 'Velocity may cool', description: 'the 22.5/day run-rate can normalise faster than modeled.' },
    ],
    monitoring: { metric: 'Revenue share', detail: 'expected vs assumption', tripwire: 'share climbs above 23.3% by day 60; re-scope', days: [7, 15, 30, 60] },
  },
  'insight-buybox-1': {
    title: 'A Buy Box shift cleared your alert threshold in {category}: score 86.',
    currency: '$',
    gapValue: 74000,
    intervention:
      'Reprice to recover ~10% of a ~{gap}/mo Buy Box gap at ~20% margin. Directional: the gap and win-rate lift are estimates.',
    projectionMetric: 'Recovered contribution / mo',
    whatCouldGoWrong: [
      { title: 'Price war risk', description: 'the competitor may re-match, eroding the recovered margin.' },
      { title: 'Buy Box eligibility', description: 'health metrics can block the win even at the matched price.' },
    ],
    monitoring: { metric: 'Buy Box share', detail: 'expected vs assumption', tripwire: 'below 90% share by day 60; re-scope or exit', days: [7, 15, 30, 60] },
  },
  'insight-demand-1': {
    title: 'A cover shortfall cleared your stock line in {category}: score 88.',
    currency: '$',
    gapValue: 162500,
    intervention:
      'Transfer stock to protect ~10% of a ~{gap}/mo demand window at ~20% margin. Directional: the spike and lead time are estimates.',
    projectionMetric: 'Protected contribution / mo',
    whatCouldGoWrong: [
      { title: 'Spike may fade', description: 'the 3.2x demand lift is promo-driven and can revert.' },
      { title: 'Transfer lead time', description: 'inbound delays can leave a stockout gap before units land.' },
    ],
    monitoring: { metric: 'Days of cover', detail: 'expected vs assumption', tripwire: 'cover under 8 days by day 60; expedite or exit', days: [7, 15, 30, 60] },
  },
  'insight-opp-1': {
    title: 'An ad-efficiency gap cleared your target in {category}: score 79.',
    currency: '$',
    gapValue: 60000,
    intervention:
      'Reallocate budget to capture ~10% of a ~{gap}/mo efficiency gap at ~20% margin. Directional: the ACoS lift is an estimate.',
    projectionMetric: 'Saved contribution / mo',
    whatCouldGoWrong: [
      { title: 'Exact-match ceiling', description: 'shifted budget may exhaust available exact-match volume.' },
      { title: 'Rank exposure', description: 'pausing broad terms can soften organic visibility short-term.' },
    ],
    monitoring: { metric: 'TACoS', detail: 'expected vs assumption', tripwire: 'above 18% by day 60; re-scope or exit', days: [7, 15, 30, 60] },
  },
  'insight-opp-2': {
    title: 'A pricing headroom niche cleared your opportunity threshold in {category}: score 88.',
    currency: '$',
    gapValue: 92500,
    intervention:
      'Raise price to capture ~10% of a ~{gap}/mo headroom at ~20% margin. Directional: the elasticity window is an estimate.',
    projectionMetric: 'Contribution / mo',
    whatCouldGoWrong: [
      { title: 'Competitor returns', description: 'the FBA stockout is temporary; the window may close early.' },
      { title: 'Conversion risk', description: 'the +$4.00 lift may soften conversion more than modeled.' },
    ],
    monitoring: { metric: 'Win rate', detail: 'expected vs assumption', tripwire: 'below 85% by day 60; revert price', days: [7, 15, 30, 60] },
  },
  'insight-opp-3': {
    title: 'A cross-sell niche cleared your opportunity threshold in {category}: score 84.',
    currency: '$',
    gapValue: 71000,
    intervention:
      'Launch a virtual bundle to capture ~10% of a ~{gap}/mo basket gap at ~20% margin. Directional: co-buy rate is an estimate.',
    projectionMetric: 'Contribution / mo',
    whatCouldGoWrong: [
      { title: 'Co-buy may not hold', description: 'the 28% attach rate can drop once bundled.' },
      { title: 'Cannibalisation', description: 'bundle sales may pull from standalone filter demand.' },
    ],
    monitoring: { metric: 'Attach rate', detail: 'expected vs assumption', tripwire: 'below assumed share by day 60; re-scope or exit', days: [7, 15, 30, 60] },
  },
  'insight-news-1': {
    title: 'A macro fee change cleared your risk threshold in {category}: score 90.',
    currency: '$',
    gapValue: 42000,
    intervention:
      'Re-price to offset ~10% of a ~{gap}/mo fee increase at ~20% margin. Directional: the +4.2% fee estimate may revise.',
    projectionMetric: 'Offset contribution / mo',
    whatCouldGoWrong: [
      { title: 'Fee schedule may revise', description: 'the +4.2% estimate is pre-effective and can change.' },
      { title: 'Price sensitivity', description: 'passing fees through can soften conversion on affected tiers.' },
    ],
    monitoring: { metric: 'Net margin', detail: 'expected vs assumption', tripwire: 'below floor by day 60; re-scope or exit', days: [7, 15, 30, 60] },
  },
};

// ---------------------------------------------------------------------------
// Resolve base inputs for a given insight
// ---------------------------------------------------------------------------

export const getSimulationInputs = (insight) => {
  const override = (insight && BASE_BY_ID[insight.id]) || {};
  const category = categoryLabel(insight?.category);
  const merged = { ...DEFAULT_INPUT, ...override };
  return {
    ...merged,
    category,
    title: merged.title.replace('{category}', category),
    intervention: merged.intervention, // {gap} resolved after compute
    productName: insight?.headline || '',
    skuCode: insight?.skuCode || insight?.sku || '',
  };
};

// ---------------------------------------------------------------------------
// Core math — everything the modal renders is computed here
// ---------------------------------------------------------------------------

export const computeSimulation = (inputs) => {
  const { currency, gapValue, capturePct, marginPct, rampDays } = inputs;

  const capture = Number(capturePct) / 100;
  const margin = Number(marginPct) / 100;
  const steadyState = gapValue * capture * margin;

  // Ramp fraction at each checkpoint (linear ramp to steady state over rampDays).
  const ramp = (day) => Math.min(day / Number(rampDays || 90), 1);
  const at = (day) => steadyState * ramp(day);

  const day30 = at(30);
  const day60 = at(60);
  const day90 = at(90);
  const maxVal = Math.max(day90, 1);

  const fmt = (v) => formatCurrency(currency, v);

  // Formula panel rows shared shape.
  const buildFormula = (day) => {
    const fraction = ramp(day);
    const result = steadyState * fraction;
    return {
      expression: inputs.formulaExpression,
      rows: [
        { label: inputs.formulaGapLabel, value: fmt(gapValue) },
        { label: 'Capture', value: `${Number(capturePct).toFixed(1)}%` },
        { label: 'Est. margin', value: `${Number(marginPct).toFixed(1)}%` },
        { label: `Ramp fraction (day ${day})`, value: fraction >= 1 ? '1×' : `${fraction.toFixed(2)}×` },
        { label: 'Result', value: fmt(result), highlight: true },
        { label: 'Timeframe', value: fraction >= 1 ? 'ramped to steady state' : `partial ramp · day ${day}` },
        { label: 'Provenance', value: 'projection over your L1 figures', badge: 'L1' },
      ],
      footnote:
        fraction >= 1
          ? '100% of the steady-state effect has landed by day 90.'
          : `${Math.round(fraction * 100)}% of the steady-state effect has landed by day ${day}.`,
    };
  };

  return {
    contribution: {
      value: fmt(steadyState),
      range: {
        conservative: fmt(steadyState * 0.5),
        expected: fmt(steadyState),
        optimistic: fmt(steadyState * 1.5),
      },
      doNothingD90: fmt(0),
      doThisD90: fmt(steadyState),
    },
    intervention: inputs.intervention.replace('{gap}', fmt(gapValue)),
    projection: {
      metric: inputs.projectionMetric,
      now: fmt(0),
      doNothing: fmt(0),
      cells: [
        { key: 'day30', label: 'DAY 30', value: fmt(day30), pct: Math.round((day30 / maxVal) * 100) },
        { key: 'day60', label: 'DAY 60', value: fmt(day60), pct: Math.round((day60 / maxVal) * 100) },
        { key: 'day90', label: 'DAY 90', value: fmt(day90), pct: Math.round((day90 / maxVal) * 100) },
      ],
    },
    formulas: {
      contribution: buildFormula(90),
      day30: buildFormula(30),
      day60: buildFormula(60),
      day90: buildFormula(90),
    },
  };
};

export const ASSUMPTION_PRESETS = {
  conservative: { capturePct: 5, marginPct: 15, rampDays: 120 },
  expected: { capturePct: 10, marginPct: 20, rampDays: 90 },
  optimistic: { capturePct: 15, marginPct: 25, rampDays: 60 },
};
