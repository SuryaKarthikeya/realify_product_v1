// Dummy data for "The Realify Brief" banner (Workspace).
// Each tab provides three headline stats + a short narrative description.

const makeStats = (opportunity, skus, risk) => [
  { key: 'opportunity', label: 'OPPORTUNITY PROJECTED', value: opportunity, icon: 'fa-arrow-trend-up', tone: 'emerald' },
  { key: 'skus', label: 'NO. OF AFFECTED SKUS', value: skus, icon: 'fa-cubes', tone: 'blue' },
  { key: 'risk', label: 'BUSINESS AT RISK', value: risk, icon: 'fa-triangle-exclamation', tone: 'rose' },
];

export const REALIFY_BRIEF = {
  sales: {
    stats: makeStats('$89.5K', '14', '$52K'),
    description: [
      'Autofy clocked $18.4K in revenue this month, up 12% MoM, driven largely by mounting accessories, but margin slipped 2.1pp as ad spend outpaced returns.',
      'Three SKUs are flagged at risk, with AF-CABLE-USB losing Buy Box ground to a competitor who undercut price by $28.',
    ],
  },

  margin: {
    stats: makeStats('$412,000', '9', '$68,500'),
    description: [
      'Blended margin is down 2.1pp MoM as fees and ad spend rose faster than net revenue across your top categories.',
      'Nine SKUs are bleeding margin; the largest single drag is fulfilment fee creep on standard-tier items.',
    ],
  },

  inventory: {
    stats: makeStats('$326,000', '11', '$74,200'),
    description: [
      'Cover has thinned across fast-movers, with 11 SKUs projected to stock out inside 14 days on current velocity.',
      'A timely transfer to FBA protects organic rank and avoids the stockout penalty on your highest-velocity listing.',
    ],
  },

  marketing: {
    stats: makeStats('$268,000', '7', '$41,300'),
    description: [
      'TACoS drifted above target on seven campaigns as broad-match keywords absorbed budget with weak conversion.',
      'Reallocating spend to top-converting exact matches recovers efficiency without sacrificing share of voice.',
    ],
  },

  customers: {
    stats: makeStats('$351,000', '10', '$38,900'),
    description: [
      'Demand patterns are shifting toward bundled accessories, lifting basket size but concentrating revenue on fewer SKUs.',
      'Ten product families show changing buying behaviour worth watching before it moves category share.',
    ],
  },

  products: {
    stats: makeStats('$477,000', '12', '$45,600'),
    description: [
      'A cluster of emerging winners is gaining velocity ahead of the wider category, opening a near-term assortment gap.',
      'Twelve SKUs are trending up fast enough to warrant re-stocking and listing investment this cycle.',
    ],
  },
};
