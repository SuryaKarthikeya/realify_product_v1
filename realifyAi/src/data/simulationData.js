import { formatCompactMoney } from '@/utils/formatters';

/**
 * ── Simulation content, one entry per Action ──
 *
 * The Simulation panel (Reason → Analyze → Decide → Confirm) is opened from a row
 * in the Actions table, so everything it shows has to belong to *that* action:
 * a stockout reads about days of cover and supplier lead times, a keyword negation
 * reads about match types and wasted spend.
 *
 * Each signal id maps to a compact spec below; the builders at the top expand it
 * into the shape the panel renders. Anything a spec leaves out falls back to a
 * value derived from the signal itself (channel, category, SKU, exposure), so a
 * new action still renders a coherent panel before its copy is written.
 */

/* ── cell / card builders ── */

/** Analyze-tab metric row. `tone`: 'bad' | 'good' | undefined (neutral). */
const m = (label, value, icon, tone) => ({
  label,
  value,
  icon,
  highlightColor:
    tone === 'bad' ? 'text-red-500' : tone === 'good' ? 'text-emerald-600' : undefined,
});

/** Simulation cards — green (upside), red (downside), plain (neutral fact). */
const good = (label, value) => ({ label, value, valueColor: 'text-emerald-600' });
const bad = (label, value) => ({ label, value, valueColor: 'text-red-500' });
const flat = (label, value) => ({ label, value, valueColor: 'text-gray-900 dark:text-white' });

/** Decide-tab impact tile. */
const tile = (label, value, icon, tone) => ({
  label,
  value,
  icon,
  color:
    tone === 'bad' ? 'text-red-600' : tone === 'good' ? 'text-emerald-600' : 'text-gray-900 dark:text-white',
});

/** Numbered "what happens after approval" step. */
const steps = (rows) => rows.map(([icon, text], i) => ({ step: i + 1, icon, text }));

/** Confirm-tab summary row. `tone`: 'good' | 'bad' | undefined. */
const row = (label, value, tone) => ({
  label,
  value,
  isBold: true,
  valueColor:
    tone === 'good' ? 'text-emerald-600' : tone === 'bad' ? 'text-red-600' : 'text-gray-900 dark:text-white',
});

/**
 * The four Analyze accordions. Descriptions sit after the cards for "now" (the
 * numbers are the point) and before them for the scenarios (the setup is).
 */
const buildSims = (s) => [
  {
    id: 'now',
    number: '①',
    title: s.nowTitle,
    cards: s.now.cards,
    description: s.now.desc,
    descriptionPlacement: 'after',
  },
  {
    id: 'delay',
    number: '②',
    title: s.delayTitle || 'If we delay the decision',
    tabs: s.delay.tabs,
    activeTab: s.delay.tabs[0],
    cards: s.delay.cards,
    description: s.delay.desc,
    descriptionPlacement: 'before',
  },
  {
    id: 'worst',
    number: '③',
    title: 'Worst case scenario',
    cards: s.worst.cards,
    description: s.worst.desc,
    descriptionPlacement: 'before',
  },
  {
    id: 'best',
    number: '④',
    title: 'Best case scenario',
    cards: s.best.cards,
    description: s.best.desc,
    descriptionPlacement: 'before',
  },
];

/* ── agent rosters ──
 * Which agents plausibly weigh in depends on the domain, so the trace on a cash
 * action names the cash agents rather than the inventory ones.
 */
const AGENTS = {
  sales: [
    ['PX', 'blue', 'Price positioning, Buy Box defence, promo windows.'],
    ['FA', 'blue', 'Runs the Plan of Record consensus; one forecast every agent reads.'],
    ['LX', 'orange', 'Listing quality, keyword coverage, content conversion.'],
    ['CH', 'emerald', 'Channel mix, marketplace-specific rules and fee structures.'],
  ],
  margin: [
    ['FE', 'blue', 'Fee recovery, dimensional and referral fee audits.'],
    ['CG', 'blue', 'Landed cost truth, COGS variance, supplier price drift.'],
    ['PX', 'orange', 'Price positioning, Buy Box defence, promo windows.'],
    ['CC', 'emerald', 'Fee recovery, payout pacing, CM3 truth, working capital.'],
  ],
  inventory: [
    ['RP', 'blue', 'Reorder points and quantities, working-capital-aware; owns expedites.'],
    ['FA', 'blue', 'Runs the Plan of Record consensus; one forecast every agent reads.'],
    ['SM', 'orange', 'Supplier lifecycle, landed-cost truth, terms, MOQ.'],
    ['CC', 'emerald', 'Fee recovery, payout pacing, CM3 truth, working capital.'],
  ],
  cash: [
    ['CC', 'blue', 'Fee recovery, payout pacing, CM3 truth, working capital.'],
    ['PY', 'blue', 'Marketplace payout schedules, reserve holds, settlement timing.'],
    ['SM', 'orange', 'Supplier lifecycle, landed-cost truth, terms, MOQ.'],
    ['RP', 'emerald', 'Reorder points and quantities, working-capital-aware; owns expedites.'],
  ],
  ads: [
    ['AD', 'blue', 'Campaign structure, budget pacing, ROAS and TACoS guardrails.'],
    ['KW', 'blue', 'Search term mining, match types, negation and bid ladders.'],
    ['CR', 'orange', 'Creative rotation, frequency caps, fatigue detection.'],
    ['FA', 'emerald', 'Runs the Plan of Record consensus; one forecast every agent reads.'],
  ],
};

/* ── per-action specs ── */

const SPECS = {
  /* ══════════ REVENUE ══════════ */

  'sig-rev-1': {
    title: ['Buy Box win rate has fallen to', '71%'],
    action: 'Reprice',
    reason: {
      confidence: ['High', 'Strong outlook', 88],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$240K', 'Potential impact', 72],
      checklist: [
        'A competitor undercut your listing by $420 eleven days ago and has held the Buy Box since.',
        'Buy Box share on B0DM28PRG7 has slid from 94% to 71%, costing roughly 9 orders a day.',
        'At $8,499 the listing still clears the $7,940 margin floor with $559 of headroom.',
        'The category promo window closes in 6 days, after which traffic drops about 40%.',
      ],
      cannotSettle:
        'Whether the competitor is running a temporary promo or a permanent price cut — their 90-day history shows both patterns.',
    },
    analyze: {
      metricsTitle: 'CURRENT PRICING POSITION',
      metrics: [
        m('Your price', '$9,299', 'fa-tag'),
        m('Lowest competitor price', '$8,879', 'fa-arrow-down', 'bad'),
        m('Buy Box win rate', '71%', 'fa-crown', 'bad'),
        m('Margin floor', '$7,940', 'fa-shield-halved'),
        m('Orders lost per day', '9 units', 'fa-cart-shopping', 'bad'),
        m('Promo window remaining', '6 days', 'fa-clock', 'bad'),
        m('Price elasticity (30d)', '1.8x', 'fa-chart-line'),
      ],
      simulationsTitle: 'PRICING SIMULATIONS',
      nowTitle: 'If we reprice to $8,499 now',
      now: {
        cards: [good('BUY BOX WIN RATE', '94%'), good('REVENUE RECOVERED', '+$240K')],
        desc:
          'Undercutting by $380 reclaims the Buy Box within 2 hours of the next repricer sweep, ahead of the promo window closing.',
      },
      delay: {
        tabs: ['3 days', '7 days', '14 days'],
        cards: [bad('ORDERS FORGONE', '27 units'), bad('RANK SLIPPAGE', '#4 → #7')],
        desc:
          'Every day at 71% share compounds: lost velocity feeds back into organic rank, which costs traffic even after the price is fixed.',
      },
      worst: {
        cards: [bad('MARGIN GIVEN UP', '-$46K')],
        desc:
          'The competitor matches your $8,499 within a day and both listings sit at the lower price with the same share split as before.',
      },
      best: {
        cards: [good('PROFIT CAPTURED', '+$290K')],
        desc:
          'The competitor is mid-promo, runs out of stock in nine days, and you hold the Buy Box at a restored price through the window.',
      },
    },
    decide: {
      icon: 'fa-tags',
      title: 'Reprice B0DM28PRG7 to $8,499',
      description: 'This undercuts the current Buy Box holder by $380 while holding $559 above the margin floor.',
      tiles: [
        tile('Revenue protected', '+$240K', 'fa-shield-halved', 'good'),
        tile('Margin per unit', '$559', 'fa-percent'),
        tile('Buy Box recovery', '94%', 'fa-crown', 'good'),
        tile('Time to effect', '~2 hrs', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-tag', 'The listing price on B0DM28PRG7 changes from $9,299 to $8,499.'],
        ['fa-robot', 'The repricer floor is pinned at $7,940 so automation cannot go below margin.'],
        ['fa-crown', 'Buy Box share is monitored every 30 minutes for the next 48 hours.'],
        ['fa-rotate-left', 'The price reverts automatically when the promo window closes in 6 days.'],
      ]),
      confidence: ['94%', 'High confidence', 'Based on 11 days of competitor price tracking and a stable 1.8x elasticity curve.'],
      confidenceFactors: ['Competitor price verified', 'Margin floor respected', 'Promo window still open'],
      disclaimer: 'The price point and revert date can still be adjusted before you confirm.',
      alternatives: [
        ['Match instead of undercut', 'Hold at $8,879 and split the Buy Box rotation', 'fa-equals'],
        ['Test a smaller cut first', 'Try $8,799 for 48 hours and measure share recovery', 'fa-flask'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Price change'),
        row('SKU', 'B0DM28PRG7'),
        row('Current price', '$9,299'),
        row('New price', '$8,499'),
        row('Margin floor', '$7,940'),
        row('Revert date', '6 days'),
        row('Buy Box impact', '71% → 94%', 'good'),
      ],
      cases: ['-$46K', '+$240K', '+$290K'],
      checklist: ['Competitor pricing verified', 'Margin floor reviewed', 'Simulations reviewed', 'Revert window set'],
    },
    success: ['Price updated', 'B0DM28PRG7 is now live at $8,499 on Amazon with a $7,940 repricer floor. Buy Box share is being tracked every 30 minutes.', 'RPR-2026-04417'],
  },

  'sig-rev-2': {
    title: ['Viral demand surge —', '4 days of cover left'],
    action: 'Restock',
    reason: {
      confidence: ['High', 'Strong outlook', 84],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$180K', 'Potential impact', 64],
      checklist: [
        'Units per day on SKU-CAM-01 jumped from 18 to 61 after a creator video landed on 22 July.',
        'FBA has 244 units left — about 4 days of cover at the new run rate.',
        'Inbound lead time to the nearest fulfilment node is 5 days, so there is a 1-day gap.',
        'Organic rank has climbed to #3 in Smart Home Cameras and holds while stock lasts.',
      ],
      cannotSettle:
        'How long the viral lift holds — comparable creator-driven spikes in this category have decayed anywhere between 9 and 40 days.',
    },
    analyze: {
      metricsTitle: 'CURRENT DEMAND POSITION',
      metrics: [
        m('Sales velocity (pre-surge)', '18 units/day', 'fa-chart-line'),
        m('Sales velocity (now)', '61 units/day', 'fa-fire', 'good'),
        m('FBA stock on hand', '244 units', 'fa-cube'),
        m('Days of cover', '4 days', 'fa-calendar', 'bad'),
        m('Inbound lead time', '5 days', 'fa-truck-fast', 'bad'),
        m('Organic rank', '#3', 'fa-ranking-star', 'good'),
        m('Stockout probability (7d)', '86%', 'fa-triangle-exclamation', 'bad'),
      ],
      simulationsTitle: 'DEMAND SIMULATIONS',
      nowTitle: 'If we restock 350 units now',
      now: {
        cards: [good('REVENUE CAPTURED', '+$180K'), good('COVER EXTENDED', '+6 days')],
        desc:
          'A 350-unit inbound arriving day 5 bridges the gap with a one-day dip, keeping the listing in stock through the momentum window.',
      },
      delay: {
        tabs: ['2 days', '4 days', '7 days'],
        cards: [bad('STOCKOUT RISK', 'Certain'), bad('RANK LOST', '#3 → #11')],
        desc:
          'Going out of stock during a surge is the expensive failure mode — rank resets and the recovered listing no longer inherits the traffic.',
      },
      worst: {
        cards: [bad('EXCESS UNITS', '180 units')],
        desc:
          'The viral lift decays within a week and 350 units land into normalised demand, leaving stock to carry at storage cost.',
      },
      best: {
        cards: [good('REVENUE CAPTURED', '+$260K')],
        desc: 'Demand holds past 30 days, the listing keeps #3 rank, and the full inbound sells through at full price.',
      },
    },
    decide: {
      icon: 'fa-truck-fast',
      title: 'Create a 350-unit FBA inbound for SKU-CAM-01',
      description: 'Sized to bridge the 5-day lead time and cover 6 days of demand at the current run rate.',
      tiles: [
        tile('Revenue captured', '+$180K', 'fa-arrow-trend-up', 'good'),
        tile('Cash required', '$105K', 'fa-wallet'),
        tile('Days of cover', '+6 days', 'fa-calendar', 'good'),
        tile('Rank protected', '#3', 'fa-ranking-star', 'good'),
      ],
      approvalSteps: steps([
        ['fa-boxes-stacked', 'A 350-unit FBA inbound shipment is created for SKU-CAM-01.'],
        ['fa-truck-fast', 'The shipment is routed to the nearest fulfilment node on a 5-day lane.'],
        ['fa-dollar-sign', 'The cash forecast is adjusted for the $105K outflow.'],
        ['fa-chart-line', 'The demand plan is re-baselined at 61 units/day with a 14-day review.'],
      ]),
      confidence: ['86%', 'High confidence', 'Based on 11 days of post-surge sell-through and a verified 5-day inbound lane.'],
      confidenceFactors: ['Velocity confirmed', 'Lane capacity available', 'Cash position sufficient'],
      disclaimer: 'Quantity and destination node can still be adjusted before you confirm.',
      alternatives: [
        ['Split the inbound', 'Send 200 now and 150 after a 7-day demand read', 'fa-arrows-split-up-and-left'],
        ['Expedite a smaller lot', 'Air-freight 120 units in 2 days at a higher landed cost', 'fa-plane'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'FBA inbound shipment'),
        row('SKU', 'SKU-CAM-01'),
        row('Quantity', '350 units'),
        row('Destination', 'Nearest FBA node'),
        row('Lead time', '5 days'),
        row('Total cost', '$105K'),
        row('Inventory impact', '+6 days cover', 'good'),
      ],
      cases: ['-$62K', '+$180K', '+$260K'],
      checklist: ['Demand velocity verified', 'Lane capacity confirmed', 'Simulations reviewed', 'Decay risk understood'],
    },
    success: ['Inbound created', '350 units of SKU-CAM-01 are booked to the nearest FBA node on a 5-day lane. Inventory and cash forecasts have been updated.', 'FBA-2026-08812'],
  },

  'sig-rev-3': {
    title: ['Search rank dropped to', '#9 on Walmart'],
    action: 'Optimize Listing',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 66],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$95,000', 'Potential impact', 48],
      checklist: [
        'SKU-CHR-42 fell from #2 to #9 on "ergonomic office chair" over 18 days.',
        'The product title is missing two of the three highest-volume search terms in the category.',
        'Organic sessions are down 44% while conversion rate on the listing held steady at 4.1%.',
        'Two competitors added sponsored coverage on the same terms during the same period.',
      ],
      cannotSettle:
        'How much of the drop is Walmart algorithm reweighting versus competitor sponsored pressure — the two moved in the same window.',
    },
    analyze: {
      metricsTitle: 'CURRENT LISTING POSITION',
      metrics: [
        m('Search rank', '#9', 'fa-ranking-star', 'bad'),
        m('Rank 18 days ago', '#2', 'fa-clock'),
        m('Organic sessions (7d)', '1,240', 'fa-eye', 'bad'),
        m('Conversion rate', '4.1%', 'fa-percent'),
        m('Title keyword coverage', '1 of 3', 'fa-key', 'bad'),
        m('Competitor sponsored bids', '2 new', 'fa-bullhorn', 'bad'),
        m('Revenue at risk (30d)', '$95,000', 'fa-triangle-exclamation', 'bad'),
      ],
      simulationsTitle: 'RANKING SIMULATIONS',
      nowTitle: 'If we optimise the listing now',
      now: {
        cards: [good('PROJECTED RANK', '#2 – #3'), good('REVENUE RECOVERED', '+$95K')],
        desc:
          'Rewriting the title around the two missing terms plus a $9K exact-match campaign typically reclaims top-3 within 12 to 16 days.',
      },
      delay: {
        tabs: ['1 week', '3 weeks', '6 weeks'],
        cards: [bad('SESSIONS LOST', '-58%'), bad('RANK DRIFT', '#9 → #14')],
        desc:
          'Rank decay is self-reinforcing on Walmart: lower rank means fewer sessions, which further weakens the relevance signal.',
      },
      worst: {
        cards: [bad('SPEND WITH NO LIFT', '-$9K')],
        desc: 'The drop was algorithmic reweighting, the rewritten title does not move relevance, and the campaign spend returns nothing.',
      },
      best: {
        cards: [good('REVENUE RECOVERED', '+$130K')],
        desc: 'The title change restores relevance, the competitors pull their sponsored bids, and the listing returns to #1.',
      },
    },
    decide: {
      icon: 'fa-magnifying-glass-chart',
      title: 'Rewrite the SKU-CHR-42 title and launch exact-match coverage',
      description: 'Adds the two missing high-volume terms and backs them with a $9K exact-match campaign for 21 days.',
      tiles: [
        tile('Revenue recovered', '+$95K', 'fa-arrow-trend-up', 'good'),
        tile('Campaign cost', '$9K', 'fa-wallet'),
        tile('Target rank', '#2', 'fa-ranking-star', 'good'),
        tile('Time to effect', '12–16 days', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-pen-to-square', 'The SKU-CHR-42 title is rewritten to cover both missing search terms.'],
        ['fa-bullhorn', 'A $9K exact-match campaign launches on the two terms for 21 days.'],
        ['fa-ranking-star', 'Daily rank tracking is enabled on all three category head terms.'],
        ['fa-flag-checkered', 'A 16-day checkpoint is scheduled to decide whether to keep the spend.'],
      ]),
      confidence: ['71%', 'Medium confidence', 'Title relevance is well understood; the competitor sponsored response is not predictable.'],
      confidenceFactors: ['Keyword gap confirmed', 'Conversion rate healthy', 'Competitor response unknown'],
      disclaimer: 'Campaign budget and the 16-day checkpoint can still be adjusted before you confirm.',
      alternatives: [
        ['Change the title only', 'Skip the paid coverage and measure organic recovery alone', 'fa-pen-to-square'],
        ['Run alternate scenarios', 'Compare budgets from $5K to $20K against projected rank', 'fa-chart-simple'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Listing optimisation'),
        row('SKU', 'SKU-CHR-42'),
        row('Channel', 'Walmart'),
        row('Terms added', '2'),
        row('Campaign budget', '$9,000'),
        row('Duration', '21 days'),
        row('Target rank', '#9 → #2', 'good'),
      ],
      cases: ['-$9K', '+$95K', '+$130K'],
      checklist: ['Keyword gap verified', 'Title copy approved', 'Simulations reviewed', 'Checkpoint scheduled'],
    },
    success: ['Listing updated', 'The SKU-CHR-42 title now covers both missing terms and a $9,000 exact-match campaign is live on Walmart for 21 days.', 'LST-2026-02290'],
  },

  'sig-rev-4': {
    title: ['Bundle opportunity worth', '+$850 AOV'],
    action: 'Create Bundle',
    reason: {
      confidence: ['High', 'Strong outlook', 82],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$65,000', 'Potential impact', 42],
      checklist: [
        'SKU-VND-08 is bought together with two accessory SKUs in 31% of orders already.',
        'Both accessories are in stock with more than 40 days of cover, so a bundle will not starve them.',
        'A Virtual Bundle carries no packaging or inbound cost — it is a listing-level change.',
        'Category benchmarks put bundle attach rate at 18% to 24% of eligible traffic.',
      ],
      cannotSettle:
        'Whether bundle sales will be incremental or simply cannibalise the standalone accessory listings — historical data is mixed.',
    },
    analyze: {
      metricsTitle: 'CURRENT BASKET POSITION',
      metrics: [
        m('Average order value', '$2,140', 'fa-cart-shopping'),
        m('Bought-together rate', '31%', 'fa-link', 'good'),
        m('Accessory 1 cover', '46 days', 'fa-cube'),
        m('Accessory 2 cover', '41 days', 'fa-cube'),
        m('Projected AOV lift', '+$850', 'fa-arrow-trend-up', 'good'),
        m('Setup cost', '$0', 'fa-wallet', 'good'),
        m('Time to live', '~24 hrs', 'fa-clock'),
      ],
      simulationsTitle: 'BASKET SIMULATIONS',
      nowTitle: 'If we launch the bundle now',
      now: {
        cards: [good('AOV LIFT', '+$850'), good('REVENUE ADDED', '+$65K')],
        desc:
          'A Virtual Bundle costs nothing to stand up and goes live in about a day, so the only real exposure is cannibalisation.',
      },
      delay: {
        tabs: ['2 weeks', '1 month', '2 months'],
        cards: [bad('REVENUE FORGONE', '-$65K'), flat('COST OF WAITING', 'None')],
        desc: 'Nothing degrades by waiting — this is pure opportunity cost while the accessories stay in stock.',
      },
      worst: {
        cards: [bad('NET REVENUE CHANGE', '-$12K')],
        desc: 'Bundle sales fully cannibalise standalone accessory orders and the discount inside the bundle nets out negative.',
      },
      best: {
        cards: [good('REVENUE ADDED', '+$110K')],
        desc: 'The bundle attaches at 24% of eligible traffic and lifts the standalone listings through added visibility.',
      },
    },
    decide: {
      icon: 'fa-layer-group',
      title: 'Create a Virtual Bundle around SKU-VND-08',
      description: 'Pairs the main SKU with its two most-attached accessories at a 6% bundle discount.',
      tiles: [
        tile('Revenue added', '+$65K', 'fa-arrow-trend-up', 'good'),
        tile('Setup cost', '$0', 'fa-wallet', 'good'),
        tile('AOV lift', '+$850', 'fa-cart-shopping', 'good'),
        tile('Time to live', '~24 hrs', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-layer-group', 'A Virtual Bundle is created for SKU-VND-08 plus both accessory SKUs.'],
        ['fa-percent', 'A 6% bundle discount is applied against the sum of standalone prices.'],
        ['fa-cube', 'Bundle availability is tied to the lowest-cover component so it cannot oversell.'],
        ['fa-chart-simple', 'Attach rate and standalone cannibalisation are tracked side by side for 30 days.'],
      ]),
      confidence: ['82%', 'High confidence', 'Based on a 31% observed bought-together rate across 90 days of order data.'],
      confidenceFactors: ['Attach behaviour proven', 'Components in stock', 'No setup cost'],
      disclaimer: 'Bundle discount and component mix can still be adjusted before you confirm.',
      alternatives: [
        ['Bundle one accessory only', 'Lower cannibalisation risk with a smaller AOV lift', 'fa-minus'],
        ['Run alternate scenarios', 'Compare 4%, 6% and 10% bundle discounts', 'fa-chart-simple'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Virtual Bundle'),
        row('Anchor SKU', 'SKU-VND-08'),
        row('Components', '3 SKUs'),
        row('Bundle discount', '6%'),
        row('Setup cost', '$0'),
        row('Expected AOV lift', '+$850', 'good'),
        row('Revenue impact', '+$65,000', 'good'),
      ],
      cases: ['-$12K', '+$65K', '+$110K'],
      checklist: ['Attach rate verified', 'Component cover reviewed', 'Simulations reviewed', 'Cannibalisation risk understood'],
    },
    success: ['Bundle created', 'A 3-SKU Virtual Bundle around SKU-VND-08 is live on Amazon at a 6% discount. Attach rate tracking starts today.', 'BDL-2026-01174'],
  },

  'sig-rev-5': {
    title: ['Seasonal tail — demand down', '34%'],
    action: 'Reallocate Budget',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 64],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$42,000', 'Potential impact', 36],
      checklist: [
        'SKU-PET-15 demand is down 34% against the prior 30 days as the seasonal peak passes.',
        'The reorder point is still set for peak velocity, so the next PO would over-order by about 260 units.',
        'Two high-margin treat SKUs are trending up 22% and are currently under-funded on ads.',
        'Shifting budget between Shopify campaigns takes effect the same day.',
      ],
      cannotSettle:
        'Whether the treat trend is a genuine category shift or a short promo-driven bump — only 19 days of data so far.',
    },
    analyze: {
      metricsTitle: 'CURRENT SEASONAL POSITION',
      metrics: [
        m('Demand vs prior 30d', '-34%', 'fa-arrow-trend-down', 'bad'),
        m('Current reorder point', '520 units', 'fa-cube', 'bad'),
        m('Right-sized reorder point', '260 units', 'fa-cube', 'good'),
        m('Treat SKUs trend', '+22%', 'fa-arrow-trend-up', 'good'),
        m('Ad budget on declining SKU', '$18,000/mo', 'fa-bullhorn'),
        m('Treat SKU margin', '41%', 'fa-percent', 'good'),
        m('Cash freed by re-sizing', '$42,000', 'fa-wallet', 'good'),
      ],
      simulationsTitle: 'SEASONAL SIMULATIONS',
      nowTitle: 'If we reallocate now',
      now: {
        cards: [good('CASH FREED', '+$42K'), good('MARGIN MIX', '+2.4 pts')],
        desc:
          'Re-sizing the reorder point avoids over-ordering into a declining season, and the freed ad budget lands on higher-margin SKUs.',
      },
      delay: {
        tabs: ['2 weeks', '1 month', '6 weeks'],
        cards: [bad('OVER-ORDER RISK', '260 units'), bad('MARGIN DRAG', '-1.8 pts')],
        desc: 'The next PO fires on the old reorder point, committing cash to stock that will sell through the slow season.',
      },
      worst: {
        cards: [bad('LOST UPSIDE', '-$28K')],
        desc: 'The seasonal dip reverses within three weeks and the reduced reorder point leaves the main SKU short on cover.',
      },
      best: {
        cards: [good('MARGIN CAPTURED', '+$78K')],
        desc: 'The treat trend holds, the reallocated ad budget compounds on 41% margin SKUs, and the seasonal SKU tapers cleanly.',
      },
    },
    decide: {
      icon: 'fa-arrows-turn-right',
      title: 'Re-size the reorder point and shift ad budget to treats',
      description: 'Drops the SKU-PET-15 reorder point to 260 units and moves $18,000/mo of ad budget onto two trending treat SKUs.',
      tiles: [
        tile('Cash freed', '+$42K', 'fa-wallet', 'good'),
        tile('Margin mix', '+2.4 pts', 'fa-chart-pie', 'good'),
        tile('Budget shifted', '$18K/mo', 'fa-bullhorn'),
        tile('Time to effect', 'Same day', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-cube', 'The SKU-PET-15 reorder point drops from 520 to 260 units.'],
        ['fa-bullhorn', '$18,000/mo of Shopify ad budget moves to the two trending treat SKUs.'],
        ['fa-dollar-sign', 'The cash forecast is updated for the $42,000 released from stock.'],
        ['fa-flag-checkered', 'A 19-day review confirms whether the treat trend is holding.'],
      ]),
      confidence: ['68%', 'Medium confidence', 'The seasonal decline is well established; the treat trend has only 19 days of history.'],
      confidenceFactors: ['Seasonal pattern confirmed', 'Treat trend early', 'Same-day reversibility'],
      disclaimer: 'Reorder point and budget split can still be adjusted before you confirm.',
      alternatives: [
        ['Shift half the budget', 'Move $9,000/mo and keep the rest until the trend confirms', 'fa-scale-balanced'],
        ['Re-size stock only', 'Adjust the reorder point and leave ad budgets untouched', 'fa-cube'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Budget reallocation'),
        row('SKU', 'SKU-PET-15'),
        row('Channel', 'Shopify'),
        row('Reorder point', '520 → 260 units'),
        row('Budget shifted', '$18,000/mo'),
        row('Receiving SKUs', '2 treat SKUs'),
        row('Cash impact', '+$42,000', 'good'),
      ],
      cases: ['-$28K', '+$42K', '+$78K'],
      checklist: ['Seasonal decline verified', 'Treat trend reviewed', 'Simulations reviewed', 'Review date set'],
    },
    success: ['Budget reallocated', 'The SKU-PET-15 reorder point is now 260 units and $18,000/mo has moved to two trending treat SKUs on Shopify.', 'BGT-2026-06531'],
  },

  'sig-rev-6': {
    title: ['Conversion rate dropped to', '1.9%'],
    action: 'Update Creative',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 62],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$18,000', 'Potential impact', 24],
      checklist: [
        'Conversion on SKU-HUB-07 fell from 3.4% to 1.9% while sessions stayed flat.',
        'Twelve of the last twenty support tickets ask which ports the hub actually supports.',
        'The image gallery has no specification or lifestyle shot — only five plain product angles.',
        'Category median conversion for powered USB hubs is 3.1%.',
      ],
      cannotSettle:
        'Whether the confusion is the gallery or the title copy — both mention ports without specifying the standard.',
    },
    analyze: {
      metricsTitle: 'CURRENT LISTING CONVERSION',
      metrics: [
        m('Conversion rate', '1.9%', 'fa-percent', 'bad'),
        m('Conversion 30 days ago', '3.4%', 'fa-clock'),
        m('Category median', '3.1%', 'fa-chart-bar'),
        m('Sessions (7d)', '2,180', 'fa-eye'),
        m('Spec-related tickets', '12 of 20', 'fa-headset', 'bad'),
        m('Gallery images', '5 plain', 'fa-image', 'bad'),
        m('Revenue at risk (30d)', '$18,000', 'fa-triangle-exclamation', 'bad'),
      ],
      simulationsTitle: 'CONVERSION SIMULATIONS',
      nowTitle: 'If we update the gallery now',
      now: {
        cards: [good('PROJECTED CONVERSION', '3.2%'), good('REVENUE RECOVERED', '+$18K')],
        desc:
          'Two lifestyle infographics that spell out the port standard usually close a spec-confusion gap within a week of indexing.',
      },
      delay: {
        tabs: ['2 weeks', '1 month', '2 months'],
        cards: [bad('REVENUE FORGONE', '-$18K'), bad('RETURN RATE', '4.8% → 6.1%')],
        desc: 'Spec confusion does not just cost conversion — it drives returns, which compound into listing health.',
      },
      worst: {
        cards: [bad('NO MEASURABLE LIFT', '$0')],
        desc: 'The drop was competitive pricing pressure rather than spec confusion, and the new gallery changes nothing.',
      },
      best: {
        cards: [good('REVENUE RECOVERED', '+$34K')],
        desc: 'Conversion returns above the category median at 3.6% and the return rate falls as buyers self-select correctly.',
      },
    },
    decide: {
      icon: 'fa-image',
      title: 'Replace the SKU-HUB-07 gallery with spec infographics',
      description: 'Adds two lifestyle infographics that state the port standard explicitly and reorders the gallery.',
      tiles: [
        tile('Revenue recovered', '+$18K', 'fa-arrow-trend-up', 'good'),
        tile('Production cost', '$4K', 'fa-wallet'),
        tile('Target conversion', '3.2%', 'fa-percent', 'good'),
        tile('Time to effect', '~7 days', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-image', 'Two lifestyle infographics are added to the SKU-HUB-07 gallery.'],
        ['fa-arrows-up-down-left-right', 'The gallery is reordered so the spec shot sits in position two.'],
        ['fa-percent', 'Conversion and return rate are tracked daily for 14 days.'],
        ['fa-headset', 'Support ticket tagging confirms whether spec questions drop off.'],
      ]),
      confidence: ['64%', 'Medium confidence', 'The ticket evidence is strong but the pricing environment shifted in the same window.'],
      confidenceFactors: ['Ticket evidence clear', 'Sessions stable', 'Pricing pressure unquantified'],
      disclaimer: 'Image selection and gallery order can still be adjusted before you confirm.',
      alternatives: [
        ['Update the title too', 'Add the port standard to the title alongside the gallery', 'fa-pen-to-square'],
        ['A/B test the gallery', 'Run both galleries for 14 days before committing', 'fa-flask'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Creative update'),
        row('SKU', 'SKU-HUB-07'),
        row('Channel', 'Shopify'),
        row('Images added', '2 infographics'),
        row('Production cost', '$4,000'),
        row('Target conversion', '1.9% → 3.2%', 'good'),
        row('Revenue impact', '+$18,000', 'good'),
      ],
      cases: ['-$4K', '+$18K', '+$34K'],
      checklist: ['Ticket evidence reviewed', 'Creative approved', 'Simulations reviewed', 'Tracking enabled'],
    },
    success: ['Creative updated', 'Two spec infographics are live on the SKU-HUB-07 gallery. Conversion and return rate tracking runs for 14 days.', 'CRV-2026-03348'],
  },

  /* ══════════ MARGIN ══════════ */

  'sig-mar-1': {
    title: ['Fee overcharge of', '$210K detected'],
    action: 'Raise Audit',
    reason: {
      confidence: ['High', 'Strong outlook', 90],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$210K', 'Potential impact', 68],
      checklist: [
        'SKU-EAR-10 is being billed in the Large Standard tier while its measured pack is Small Standard.',
        'The variance has run for 7 months across 4,180 billable units.',
        'Your own warehouse measurement is 21.4 × 16.2 × 4.1 cm, inside the Small Standard envelope.',
        'Amazon\'s reimbursement window covers 18 months, so the full period is still claimable.',
      ],
      cannotSettle:
        'Whether Amazon will accept your warehouse measurement or insist on their own re-measure, which adds 2 to 3 weeks.',
    },
    analyze: {
      metricsTitle: 'CURRENT FEE POSITION',
      metrics: [
        m('Billed size tier', 'Large Standard', 'fa-box', 'bad'),
        m('Measured size tier', 'Small Standard', 'fa-ruler-combined', 'good'),
        m('Fee per unit billed', '$78', 'fa-receipt', 'bad'),
        m('Fee per unit correct', '$28', 'fa-receipt', 'good'),
        m('Units affected', '4,180', 'fa-cube'),
        m('Months in variance', '7 months', 'fa-clock', 'bad'),
        m('Claimable amount', '$210K', 'fa-dollar-sign', 'good'),
      ],
      simulationsTitle: 'FEE RECOVERY SIMULATIONS',
      nowTitle: 'If we file the audit now',
      now: {
        cards: [good('FEE RECLAIMED', '+$210K'), good('ONGOING SAVING', '$50/unit')],
        desc:
          'Filing with your own measurement evidence recovers the back-dated variance and corrects the tier for every future unit.',
      },
      delay: {
        tabs: ['1 month', '3 months', '6 months'],
        cards: [bad('OVERCHARGE ACCRUING', '$30K/mo'), bad('CLAIM WINDOW LEFT', '11 months')],
        desc: 'Each month adds roughly $30,000 of new overcharge and burns one month of the 18-month reimbursement window.',
      },
      worst: {
        cards: [bad('CLAIM REJECTED', '$0')],
        desc: 'Amazon re-measures with packaging included, lands back in Large Standard, and the claim is denied.',
      },
      best: {
        cards: [good('FEE RECLAIMED', '+$240K')],
        desc: 'The claim is accepted in full, the tier is corrected within a week, and two sibling SKUs qualify for the same audit.',
      },
    },
    decide: {
      icon: 'fa-file-invoice',
      title: 'Submit a dimensional audit request for SKU-EAR-10',
      description: 'Files the measured pack dimensions against 7 months of Large Standard billing across 4,180 units.',
      tiles: [
        tile('Fee reclaimed', '+$210K', 'fa-hand-holding-dollar', 'good'),
        tile('Ongoing saving', '$50/unit', 'fa-percent', 'good'),
        tile('Filing cost', '$0', 'fa-wallet', 'good'),
        tile('Resolution time', '3–5 weeks', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-file-invoice', 'A dimensional audit case is opened with Amazon Seller Support.'],
        ['fa-ruler-combined', 'Warehouse measurements and pack photos are attached as evidence.'],
        ['fa-receipt', '7 months of fee statements are attached for the 4,180 affected units.'],
        ['fa-dollar-sign', 'The reimbursement is tracked against the $210K expected credit.'],
      ]),
      confidence: ['91%', 'High confidence', 'Measurements are documented and the fee statements show an unambiguous tier mismatch.'],
      confidenceFactors: ['Measurements documented', 'Statements retained', 'Within claim window'],
      disclaimer: 'You can attach additional SKUs to the same case before you confirm.',
      alternatives: [
        ['File for all sibling SKUs', 'Include the two SKUs with the same pack profile', 'fa-layer-group'],
        ['Request a re-measure first', 'Have Amazon measure before filing the back claim', 'fa-ruler'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Dimensional fee audit'),
        row('SKU', 'SKU-EAR-10'),
        row('Channel', 'Amazon'),
        row('Units affected', '4,180'),
        row('Period', '7 months'),
        row('Claim amount', '$210K', 'good'),
        row('Ongoing saving', '$50/unit', 'good'),
      ],
      cases: ['$0', '+$210K', '+$240K'],
      checklist: ['Measurements documented', 'Fee statements attached', 'Simulations reviewed', 'Claim window confirmed'],
    },
    success: ['Audit filed', 'A dimensional audit case for SKU-EAR-10 covering 4,180 units over 7 months is with Amazon. Expected credit $210K.', 'AUD-2026-07725'],
  },

  'sig-mar-2': {
    title: ['Keyword bleeding', '$145K a month'],
    action: 'Negate Keywords',
    reason: {
      confidence: ['High', 'Strong outlook', 92],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$145K', 'Potential impact', 58],
      checklist: [
        'Broad match "heavy jackets" has spent $162K over 60 days and returned $17,000 in sales.',
        'It converts at 0.3% against a 2.8% campaign average — the traffic is looking for a different product.',
        'The term drives 38% of campaign spend and 2% of campaign revenue.',
        'Negating it is reversible at any time and takes effect within an hour.',
      ],
      cannotSettle:
        'Whether the term contributes any halo to organic rank on adjacent phrases — attribution cannot isolate that cleanly.',
    },
    analyze: {
      metricsTitle: 'CURRENT KEYWORD POSITION',
      metrics: [
        m('Spend (60d)', '$162K', 'fa-bullhorn', 'bad'),
        m('Sales attributed', '$17,000', 'fa-cart-shopping', 'bad'),
        m('Conversion rate', '0.3%', 'fa-percent', 'bad'),
        m('Campaign average CVR', '2.8%', 'fa-chart-bar'),
        m('Share of campaign spend', '38%', 'fa-chart-pie', 'bad'),
        m('Share of campaign revenue', '2%', 'fa-chart-pie', 'bad'),
        m('Monthly profit drain', '$145K', 'fa-triangle-exclamation', 'bad'),
      ],
      simulationsTitle: 'SPEND SIMULATIONS',
      nowTitle: 'If we negate the keyword now',
      now: {
        cards: [good('PROFIT SAVED', '+$145K'), good('CAMPAIGN ACOS', '41% → 24%')],
        desc:
          'Removing the term stops the bleed within the hour and lifts campaign-level ACoS without touching any converting traffic.',
      },
      delay: {
        tabs: ['1 week', '2 weeks', '1 month'],
        cards: [bad('SPEND WASTED', '$34K/wk'), bad('CM2 DRAG', '-2.1 pts')],
        desc: 'The term spends about $34,000 a week regardless of season — every week of delay is a straight profit transfer.',
      },
      worst: {
        cards: [bad('ORGANIC HALO LOST', '-$22K')],
        desc: 'The broad term was feeding organic relevance on adjacent phrases and rank softens after it is negated.',
      },
      best: {
        cards: [good('PROFIT SAVED', '+$172K')],
        desc: 'The freed budget redeploys onto exact-match terms already converting at 3.4% and the saving compounds.',
      },
    },
    decide: {
      icon: 'fa-ban',
      title: 'Negate "heavy jackets" as an exact negative',
      description: 'Adds the term as an exact negative on the SKU-JKT-99 campaign, keeping phrase variants live.',
      tiles: [
        tile('Profit saved', '+$145K', 'fa-shield-halved', 'good'),
        tile('Campaign ACoS', '41% → 24%', 'fa-percent', 'good'),
        tile('Implementation cost', '$0', 'fa-wallet', 'good'),
        tile('Time to effect', '~1 hr', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-ban', '"heavy jackets" is added as an exact negative on the campaign.'],
        ['fa-magnifying-glass', 'Phrase and broad variants stay live so partial matches keep serving.'],
        ['fa-chart-line', 'Campaign ACoS and organic rank are tracked side by side for 21 days.'],
        ['fa-rotate-left', 'The negation can be lifted in one click if organic rank softens.'],
      ]),
      confidence: ['92%', 'High confidence', 'Based on 60 days of search-term report data with a clear 0.3% conversion signal.'],
      confidenceFactors: ['Spend data unambiguous', 'Fully reversible', 'Halo effect unquantified'],
      disclaimer: 'Match type and the 21-day review window can still be adjusted before you confirm.',
      alternatives: [
        ['Lower the bid instead', 'Cut the bid by 70% rather than negating outright', 'fa-sliders'],
        ['Negate at ad-group level', 'Scope the negative more narrowly to one ad group', 'fa-crosshairs'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Keyword negation'),
        row('SKU', 'SKU-JKT-99'),
        row('Channel', 'Amazon'),
        row('Term', '"heavy jackets"'),
        row('Match type', 'Exact negative'),
        row('Monthly saving', '$145K', 'good'),
        row('ACoS impact', '41% → 24%', 'good'),
      ],
      cases: ['-$22K', '+$145K', '+$172K'],
      checklist: ['Search-term data reviewed', 'Halo risk understood', 'Simulations reviewed', 'Rollback available'],
    },
    success: ['Keyword negated', '"heavy jackets" is now an exact negative on the SKU-JKT-99 campaign. ACoS and organic rank tracking runs for 21 days.', 'NEG-2026-05583'],
  },

  'sig-mar-3': {
    title: ['Competitor stockout opens', '$88K of headroom'],
    action: 'Apply Price Change',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 70],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$88K', 'Potential impact', 44],
      checklist: [
        'The two cheapest competitors on SKU-DSH-04 have both been out of stock for 6 days.',
        'Your listing is now the lowest-priced in-stock option by $610.',
        'Sell-through has held at 24 units/day through the stockout with no price change.',
        'Category elasticity suggests a +$400 move costs under 6% of volume.',
      ],
      cannotSettle:
        'How long the competitor stockout lasts — their historical replenishment cycle ranges from 8 to 26 days.',
    },
    analyze: {
      metricsTitle: 'CURRENT PRICING POSITION',
      metrics: [
        m('Your price', '$3,290', 'fa-tag'),
        m('Next in-stock competitor', '$3,900', 'fa-arrow-up', 'good'),
        m('Competitors out of stock', '2', 'fa-box-open', 'good'),
        m('Stockout duration so far', '6 days', 'fa-clock'),
        m('Sell-through', '24 units/day', 'fa-cart-shopping'),
        m('Price elasticity', '1.1x', 'fa-chart-line'),
        m('Profit headroom', '$88K', 'fa-dollar-sign', 'good'),
      ],
      simulationsTitle: 'MARGIN SIMULATIONS',
      nowTitle: 'If we raise price by $400 now',
      now: {
        cards: [good('EXTRA PROFIT', '+$88K'), good('MARGIN', '+4.2 pts')],
        desc:
          'At $3,690 you remain $210 below the next in-stock competitor, so the price advantage survives the increase.',
      },
      delay: {
        tabs: ['3 days', '1 week', '2 weeks'],
        cards: [bad('MARGIN FORGONE', '$12K/day'), flat('WINDOW REMAINING', 'Unknown')],
        desc: 'The window closes the moment either competitor restocks, and there is no signal to say when that happens.',
      },
      worst: {
        cards: [bad('VOLUME LOST', '-14%')],
        desc: 'Both competitors restock within two days at their old prices and the raised price costs more volume than modelled.',
      },
      best: {
        cards: [good('EXTRA PROFIT', '+$140K')],
        desc: 'The stockout runs the full 26 days, volume holds flat at the higher price, and margin compounds across the window.',
      },
    },
    decide: {
      icon: 'fa-tag',
      title: 'Raise SKU-DSH-04 from $3,290 to $3,690',
      description: 'Captures competitor-stockout headroom while staying $210 under the next in-stock listing.',
      tiles: [
        tile('Extra profit', '+$88K', 'fa-arrow-trend-up', 'good'),
        tile('Margin gain', '+4.2 pts', 'fa-percent', 'good'),
        tile('Volume risk', '-6%', 'fa-cart-shopping', 'bad'),
        tile('Time to effect', '~1 hr', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-tag', 'The SKU-DSH-04 price moves from $3,290 to $3,690 on Shopify.'],
        ['fa-eye', 'Competitor stock status is polled every 4 hours.'],
        ['fa-rotate-left', 'The price reverts automatically when either competitor comes back in stock.'],
        ['fa-chart-line', 'Volume is tracked daily against the -6% modelled tolerance.'],
      ]),
      confidence: ['74%', 'Medium confidence', 'The stockout and price gap are verified; restock timing is the open variable.'],
      confidenceFactors: ['Stockout verified', 'Price gap confirmed', 'Restock timing unknown'],
      disclaimer: 'The price point and auto-revert trigger can still be adjusted before you confirm.',
      alternatives: [
        ['Raise by $200 instead', 'Capture half the headroom with lower volume risk', 'fa-scale-balanced'],
        ['Run alternate scenarios', 'Compare +$200 +$400 and +$600 against volume', 'fa-chart-simple'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Price increase'),
        row('SKU', 'SKU-DSH-04'),
        row('Channel', 'Shopify'),
        row('Current price', '$3,290'),
        row('New price', '$3,690'),
        row('Auto-revert', 'On competitor restock'),
        row('Profit impact', '+$88,000', 'good'),
      ],
      cases: ['-$24K', '+$88K', '+$140K'],
      checklist: ['Competitor stockout verified', 'Elasticity reviewed', 'Simulations reviewed', 'Auto-revert set'],
    },
    success: ['Price updated', 'SKU-DSH-04 is live at $3,690 on Shopify with auto-revert armed on competitor restock.', 'PRC-2026-02907'],
  },

  'sig-mar-4': {
    title: ['Supplier cost up', '$150 per unit'],
    action: 'Negotiate Cost',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 68],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$35,000', 'Potential impact', 30],
      checklist: [
        'Landed cost on SKU-BLD-02 rose from $1,240 to $1,390 on the last two POs.',
        'The retail price has not moved, so CM2 has compressed by 3.1 points.',
        'Your annual volume with this supplier is up 34%, which is real negotiating leverage.',
        'Two alternate suppliers quote within $40 of the old cost but need a 6-week qualification.',
      ],
      cannotSettle:
        'Whether the increase is a genuine input-cost pass-through or opportunistic — the supplier has not shared a cost breakdown.',
    },
    analyze: {
      metricsTitle: 'CURRENT COST POSITION',
      metrics: [
        m('Previous landed cost', '$1,240', 'fa-clock'),
        m('Current landed cost', '$1,390', 'fa-arrow-up', 'bad'),
        m('Retail price', '$2,450', 'fa-tag'),
        m('CM2 compression', '-3.1 pts', 'fa-percent', 'bad'),
        m('Volume growth (YoY)', '+34%', 'fa-chart-line', 'good'),
        m('Alternate supplier quote', '$1,280', 'fa-handshake', 'good'),
        m('Qualification time', '6 weeks', 'fa-hourglass-half', 'bad'),
      ],
      simulationsTitle: 'COST SIMULATIONS',
      nowTitle: 'If we open the negotiation now',
      now: {
        cards: [good('COST RECOVERED', '$110/unit'), good('CM2 RESTORED', '+2.3 pts')],
        desc:
          'Presenting 34% volume growth alongside the alternate quote typically recovers most of a pass-through increase.',
      },
      delay: {
        tabs: ['1 PO cycle', '2 cycles', '3 cycles'],
        cards: [bad('MARGIN LOST', '$35K/cycle'), bad('CM2 DRIFT', '-3.1 pts')],
        desc: 'Each PO cycle at the new cost locks in the compression and weakens the argument that the increase is disputed.',
      },
      worst: {
        cards: [bad('COST HELD', '$1,390')],
        desc: 'The supplier holds firm, qualification of the alternates slips past 6 weeks, and a +$150 retail increase is the only lever left.',
      },
      best: {
        cards: [good('COST RECOVERED', '$150/unit')],
        desc: 'The supplier reverses the increase in full against committed annual volume and adds 15-day terms.',
      },
    },
    decide: {
      icon: 'fa-handshake',
      title: 'Open a volume renegotiation on SKU-BLD-02',
      description: 'Puts 34% volume growth and a $1,280 alternate quote against the $150 increase before the next PO.',
      tiles: [
        tile('Cost recovered', '$110/unit', 'fa-hand-holding-dollar', 'good'),
        tile('CM2 restored', '+2.3 pts', 'fa-percent', 'good'),
        tile('Negotiation cost', '$0', 'fa-wallet', 'good'),
        tile('Time to resolve', '2–3 weeks', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-handshake', 'A volume renegotiation is opened with the current supplier on SKU-BLD-02.'],
        ['fa-chart-line', '34% annual volume growth and the $1,280 alternate quote are shared as leverage.'],
        ['fa-file-contract', 'The next PO is held for up to 3 weeks pending the outcome.'],
        ['fa-tag', 'A fallback +$150 retail price change is prepared but not applied.'],
      ]),
      confidence: ['69%', 'Medium confidence', 'Volume leverage is real, but the supplier has not disclosed a cost breakdown to argue against.'],
      confidenceFactors: ['Volume leverage strong', 'Alternate quotes in hand', 'Cost basis undisclosed'],
      disclaimer: 'The PO hold period and fallback price change can still be adjusted before you confirm.',
      alternatives: [
        ['Pass the cost to retail', 'Apply +$150 at retail and keep the supplier terms as-is', 'fa-tag'],
        ['Qualify alternates now', 'Start the 6-week qualification in parallel with talks', 'fa-arrows-split-up-and-left'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Supplier renegotiation'),
        row('SKU', 'SKU-BLD-02'),
        row('Channel', 'Walmart'),
        row('Cost increase disputed', '$150/unit'),
        row('Target recovery', '$110/unit', 'good'),
        row('PO hold', 'Up to 3 weeks'),
        row('CM2 impact', '+2.3 pts', 'good'),
      ],
      cases: ['$0', '+$35K', '+$48K'],
      checklist: ['Cost variance verified', 'Alternate quotes obtained', 'Simulations reviewed', 'Fallback prepared'],
    },
    success: ['Negotiation opened', 'A volume renegotiation on SKU-BLD-02 is open with the supplier and the next PO is held for 3 weeks.', 'NEG-2026-04102'],
  },

  /* ══════════ CASH ══════════ */

  'sig-csh-1': {
    title: ['$340K of cash tied up in', '400 excess units'],
    action: 'Apply Discount',
    reason: {
      confidence: ['High', 'Strong outlook', 80],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$340K', 'Potential impact', 78],
      checklist: [
        'SKU-OVS-12 has 620 units on hand against 220 units of forecast demand over 90 days.',
        'The 400 excess units represent $340K of working capital sitting still.',
        'A 15% outlet promo has historically cleared this category at 4.2x normal velocity.',
        'The cash forecast shows a $280K deficit in week 6 that this would cover.',
      ],
      cannotSettle:
        'Whether a 15% discount trains repeat buyers to wait for promos — the Shopify cohort data is inconclusive on this SKU.',
    },
    analyze: {
      metricsTitle: 'CURRENT CASH POSITION',
      metrics: [
        m('Units on hand', '620 units', 'fa-cube'),
        m('90-day forecast demand', '220 units', 'fa-chart-bar'),
        m('Excess units', '400 units', 'fa-box-open', 'bad'),
        m('Capital tied up', '$340K', 'fa-wallet', 'bad'),
        m('Week 6 cash deficit', '-$280K', 'fa-triangle-exclamation', 'bad'),
        m('Promo velocity multiple', '4.2x', 'fa-fire', 'good'),
        m('Holding cost per month', '$28,000', 'fa-warehouse', 'bad'),
      ],
      simulationsTitle: 'CASH SIMULATIONS',
      nowTitle: 'If we apply the discount now',
      now: {
        cards: [good('CASH UNLOCKED', '+$340K'), good('RUNWAY EXTENDED', '+11 days')],
        desc:
          'Accelerated sell-through brings forward enough cash to clear the week-6 deficit with room to spare.',
      },
      delay: {
        tabs: ['3 days', '7 days', '12 days'],
        cards: [bad('CASH SHORTAGE RISK', 'Rising'), bad('BUFFER BREACH', 'Day 9')],
        desc: 'The week-6 deficit does not move, so every day of delay compresses the window the promo has to work in.',
      },
      worst: {
        cards: [bad('PEAK DEFICIT', '-$190K')],
        desc: 'The discount underperforms at 2x velocity and only part of the excess clears before the deficit lands.',
      },
      best: {
        cards: [good('CASH UNLOCKED', '+$410K')],
        desc: 'The promo clears all 400 units inside 3 weeks and pulls forward demand on two adjacent SKUs.',
      },
    },
    decide: {
      icon: 'fa-percent',
      title: 'Run a 15% outlet promo on 400 units of SKU-OVS-12',
      description: 'Clears the excess position and pulls $340K of working capital forward ahead of the week-6 deficit.',
      tiles: [
        tile('Cash unlocked', '+$340K', 'fa-wallet', 'good'),
        tile('Margin given up', '-$51K', 'fa-percent', 'bad'),
        tile('Runway extended', '+11 days', 'fa-calendar', 'good'),
        tile('Holding cost saved', '$28K/mo', 'fa-warehouse', 'good'),
      ],
      approvalSteps: steps([
        ['fa-percent', 'A 15% outlet discount goes live on 400 units of SKU-OVS-12.'],
        ['fa-clock', 'The promo runs for 21 days or until the 400-unit cap is reached.'],
        ['fa-dollar-sign', 'The cash forecast is updated for the $340K inflow.'],
        ['fa-cube', 'The reorder point is suspended until the excess position clears.'],
      ]),
      confidence: ['84%', 'High confidence', 'Based on 4 comparable outlet promos in this category averaging 4.2x velocity.'],
      confidenceFactors: ['Excess position verified', 'Promo history comparable', 'Repeat-buyer effect unclear'],
      disclaimer: 'Discount depth and unit cap can still be adjusted before you confirm.',
      alternatives: [
        ['Try 10% first', 'Lower margin sacrifice with slower cash conversion', 'fa-scale-balanced'],
        ['Bundle the excess', 'Move units as an add-on rather than a discount', 'fa-layer-group'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Outlet promotion'),
        row('SKU', 'SKU-OVS-12'),
        row('Channel', 'Shopify'),
        row('Discount', '15%'),
        row('Unit cap', '400 units'),
        row('Duration', '21 days'),
        row('Cash impact', '+$340K', 'good'),
      ],
      cases: ['-$51K', '+$340K', '+$410K'],
      checklist: ['Excess position verified', 'Cash forecast reviewed', 'Simulations reviewed', 'Margin sacrifice accepted'],
    },
    success: ['Discount applied', 'A 15% discount on 400 units of SKU-OVS-12 is live on Shopify for 21 days. Cash and inventory forecasts have been updated automatically.', 'DSC-2026-03192'],
  },

  'sig-csh-2': {
    title: ['Payout gap of', '14 days'],
    action: 'Request Terms',
    reason: {
      confidence: ['High', 'Strong outlook', 86],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$185K', 'Potential impact', 62],
      checklist: [
        'Amazon settlement for the current cycle lands on day 21; supplier payment for PO-01 is due on day 7.',
        'That leaves a 14-day gap and a $185K shortfall against the operating buffer.',
        'This supplier has granted a terms extension twice before without a fee.',
        'Amazon early payout is available at a 1.4% fee, which costs $26,000 on this cycle.',
      ],
      cannotSettle:
        'Whether Amazon will hold a reserve against the current cycle, which would widen the gap beyond 14 days.',
    },
    analyze: {
      metricsTitle: 'CURRENT PAYOUT POSITION',
      metrics: [
        m('Supplier payment due', 'Day 7', 'fa-calendar', 'bad'),
        m('Amazon settlement date', 'Day 21', 'fa-calendar-check'),
        m('Gap', '14 days', 'fa-hourglass-half', 'bad'),
        m('Shortfall', '$185K', 'fa-triangle-exclamation', 'bad'),
        m('Operating buffer', '$120K', 'fa-wallet'),
        m('Early payout fee', '1.4% ($26,000)', 'fa-receipt', 'bad'),
        m('Prior terms extensions', '2 granted', 'fa-handshake', 'good'),
      ],
      simulationsTitle: 'LIQUIDITY SIMULATIONS',
      nowTitle: 'If we request supplier terms now',
      now: {
        cards: [good('GAP CLOSED', '14 → 0 days'), good('FEE AVOIDED', '$26K')],
        desc:
          'A 14-day extension aligns the supplier payment with the settlement date at no cost, and there is precedent for it.',
      },
      delay: {
        tabs: ['2 days', '4 days', '6 days'],
        cards: [bad('BUFFER BREACH', 'Day 7'), bad('FORCED FEE', '$26K')],
        desc: 'Suppliers need notice for a terms change; past day 4 the only remaining lever is the paid early payout.',
      },
      worst: {
        cards: [bad('COST INCURRED', '-$26K')],
        desc: 'The supplier declines the extension and the early payout fee has to be paid to cover the gap.',
      },
      best: {
        cards: [good('CASH PRESERVED', '+$185K')],
        desc: 'The supplier grants 14 days and converts the arrangement into standing Net 21 terms for future POs.',
      },
    },
    decide: {
      icon: 'fa-calendar-days',
      title: 'Request a 14-day terms extension on PO-01',
      description: 'Moves the supplier payment from day 7 to day 21 so it lands after the Amazon settlement.',
      tiles: [
        tile('Cash preserved', '+$185K', 'fa-wallet', 'good'),
        tile('Fee avoided', '$26K', 'fa-hand-holding-dollar', 'good'),
        tile('Gap closed', '14 days', 'fa-calendar', 'good'),
        tile('Time to resolve', '2–4 days', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-calendar-days', 'A 14-day terms extension request goes to the supplier for PO-01.'],
        ['fa-file-contract', 'The payment date moves from day 7 to day 21 on acceptance.'],
        ['fa-dollar-sign', 'The cash forecast is rebuilt against the new payment date.'],
        ['fa-shield-halved', 'The early payout option stays armed as a fallback until day 4.'],
      ]),
      confidence: ['86%', 'High confidence', 'Two prior extensions were granted by this supplier without a fee or terms change.'],
      confidenceFactors: ['Precedent exists', 'Settlement date confirmed', 'Reserve risk unquantified'],
      disclaimer: 'The extension length and fallback trigger date can still be adjusted before you confirm.',
      alternatives: [
        ['Take the early payout', 'Pay the 1.4% fee and settle the supplier on time', 'fa-bolt'],
        ['Split the payment', 'Pay 40% on day 7 and the balance on day 21', 'fa-arrows-split-up-and-left'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Supplier terms extension'),
        row('Reference', 'FINANCE-PO-01'),
        row('Channel', 'Amazon'),
        row('Current due date', 'Day 7'),
        row('Requested due date', 'Day 21'),
        row('Fee avoided', '$26,000', 'good'),
        row('Cash impact', '+$185K', 'good'),
      ],
      cases: ['-$26K', '+$185K', '+$210K'],
      checklist: ['Settlement date confirmed', 'Supplier precedent checked', 'Simulations reviewed', 'Fallback armed'],
    },
    success: ['Terms requested', 'A 14-day extension on FINANCE-PO-01 is with the supplier. The early payout fallback stays armed until day 4.', 'TRM-2026-09044'],
  },

  'sig-csh-3': {
    title: ['Daily burn running', '$4,200 over plan'],
    action: 'Switch Logistics',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 72],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$92,000', 'Potential impact', 34],
      checklist: [
        'Inbound freight has run on air for 11 weeks, $4,200/day above the ocean baseline.',
        'Ocean adds 18 days of transit but costs 64% less per kilo on this lane.',
        'Current days of cover across the affected SKUs is 47 — enough to absorb the longer transit.',
        'Switching saves $92,000 over the next quarter with no service-level change at the customer.',
      ],
      cannotSettle:
        'Whether Q3 demand holds at the forecast level — if it runs hot, 47 days of cover stops being enough for an 18-day-longer lane.',
    },
    analyze: {
      metricsTitle: 'CURRENT LOGISTICS POSITION',
      metrics: [
        m('Current mode', 'Air', 'fa-plane', 'bad'),
        m('Daily cost over plan', '$4,200', 'fa-arrow-up', 'bad'),
        m('Weeks on air freight', '11 weeks', 'fa-clock'),
        m('Ocean cost delta', '-64%/kg', 'fa-ship', 'good'),
        m('Added transit time', '+18 days', 'fa-hourglass-half', 'bad'),
        m('Days of cover available', '47 days', 'fa-cube', 'good'),
        m('Quarterly saving', '$92,000', 'fa-wallet', 'good'),
      ],
      simulationsTitle: 'BURN RATE SIMULATIONS',
      nowTitle: 'If we switch to ocean now',
      now: {
        cards: [good('BURN REDUCED', '$4,200/day'), good('QUARTERLY SAVING', '+$92K')],
        desc:
          '47 days of cover absorbs the 18-day transit increase, so the saving lands without a service-level change.',
      },
      delay: {
        tabs: ['2 weeks', '1 month', '2 months'],
        cards: [bad('BURN CONTINUES', '$29K/wk'), bad('SAVING FORGONE', '-$92K')],
        desc: 'Air freight keeps billing at the higher rate, and each week of delay is a straight $29,000 of avoidable spend.',
      },
      worst: {
        cards: [bad('STOCKOUT EXPOSURE', '3 SKUs')],
        desc: 'Q3 demand runs 20% above forecast, the longer lane cannot respond, and three SKUs go short before the next arrival.',
      },
      best: {
        cards: [good('ANNUAL SAVING', '+$370K')],
        desc: 'The lane change holds all year, cover stays comfortable, and the saving compounds across four quarters.',
      },
    },
    decide: {
      icon: 'fa-ship',
      title: 'Move inbound freight from air to ocean',
      description: 'Switches the affected lane to ocean, trading 18 days of transit for a $4,200/day reduction in burn.',
      tiles: [
        tile('Quarterly saving', '+$92K', 'fa-wallet', 'good'),
        tile('Burn reduced', '$4,200/day', 'fa-arrow-trend-down', 'good'),
        tile('Added transit', '+18 days', 'fa-hourglass-half', 'bad'),
        tile('Cover buffer', '47 days', 'fa-cube', 'good'),
      ],
      approvalSteps: steps([
        ['fa-ship', 'The inbound lane switches from air to ocean for the affected SKUs.'],
        ['fa-cube', 'Reorder points are lifted to absorb the 18 additional transit days.'],
        ['fa-dollar-sign', 'The cash forecast is updated for the $4,200/day reduction.'],
        ['fa-plane', 'Air freight stays available as an expedite lane for genuine shortages.'],
      ]),
      confidence: ['76%', 'Medium confidence', 'Lane economics are firm; the risk sits entirely in Q3 demand holding to forecast.'],
      confidenceFactors: ['Lane pricing confirmed', 'Cover buffer adequate', 'Q3 demand uncertain'],
      disclaimer: 'The reorder point increase and expedite policy can still be adjusted before you confirm.',
      alternatives: [
        ['Split the lane', 'Move 70% to ocean and keep 30% on air for responsiveness', 'fa-arrows-split-up-and-left'],
        ['Switch after Q3', 'Hold air freight through peak and move in October', 'fa-calendar'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Logistics mode change'),
        row('Reference', 'FINANCE-OPEX'),
        row('Channel', 'Walmart'),
        row('From', 'Air freight'),
        row('To', 'Ocean freight'),
        row('Added transit', '+18 days', 'bad'),
        row('Quarterly saving', '+$92,000', 'good'),
      ],
      cases: ['-$64K', '+$92K', '+$370K'],
      checklist: ['Lane pricing confirmed', 'Cover buffer reviewed', 'Simulations reviewed', 'Expedite lane retained'],
    },
    success: ['Logistics switched', 'The inbound lane is now ocean freight with reorder points lifted for the 18-day transit increase. Air stays available for expedites.', 'LOG-2026-05518'],
  },

  /* ══════════ INVENTORY ══════════ */

  'sig-inv-1': {
    title: ['Stockout predicted in', '4 days'],
    action: 'Restock',
    reason: {
      confidence: ['High', 'Strong outlook', 88],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$280K', 'Potential impact', 74],
      checklist: [
        'Stock on SKU-CHR-42 will run out in 4 days at the current Amazon sell-through rate.',
        'This SKU carries a $280K revenue impact this month in the Home & Garden category.',
        'Demand has increased 18% over the last 30 days versus the prior period.',
        'Cash position is sufficient to fund an expedited inbound without straining working capital.',
      ],
      cannotSettle:
        'Whether the 18% demand lift is partly promo-driven — the organic baseline is unclear for 2 of the 9 related SKUs.',
    },
    analyze: {
      metricsTitle: 'CURRENT INVENTORY POSITION',
      metrics: [
        m('Current stock', '84 units', 'fa-cube'),
        m('Days cover', '4 days', 'fa-calendar', 'bad'),
        m('Incoming inventory', '0 units', 'fa-arrow-right-arrow-left', 'bad'),
        m('Sales velocity', '21 units/day', 'fa-chart-line'),
        m('Forecasted demand (30d)', '690 units', 'fa-chart-bar', 'bad'),
        m('Inventory age', '38 days avg', 'fa-clock'),
        m('Stockout probability', '91%', 'fa-triangle-exclamation', 'bad'),
      ],
      simulationsTitle: 'INVENTORY SIMULATIONS',
      nowTitle: 'If we expedite 200 units now',
      now: {
        cards: [good('REVENUE PROTECTED', '+$280K'), good('COVER EXTENDED', '+9 days')],
        desc:
          'An expedited FBA inbound arrives on day 3, one day before stock runs out, so the Buy Box is never at risk.',
      },
      delay: {
        tabs: ['1 day', '2 days', '4 days'],
        cards: [bad('STOCKOUT RISK', '91% → 100%'), bad('BUY BOX', 'Lost on day 4')],
        desc: 'Expedite lanes need 3 days. Past day 1 there is no shipping option that lands before stock runs out.',
      },
      worst: {
        cards: [bad('EXPEDITE PREMIUM', '-$34K')],
        desc: 'The demand lift was promo-driven, it normalises within a fortnight, and the expedite premium buys cover nobody needed.',
      },
      best: {
        cards: [good('REVENUE PROTECTED', '+$360K')],
        desc: 'Demand holds at the lifted rate, the Buy Box stays intact through the window, and rank improves on the unbroken availability.',
      },
    },
    decide: {
      icon: 'fa-truck-fast',
      title: 'Create an expedited FBA inbound for 200 units of SKU-CHR-42',
      description: 'This action prevents the stockout and protects the Buy Box on a $280K monthly SKU.',
      tiles: [
        tile('Revenue protected', '+$280K', 'fa-shield-halved', 'good'),
        tile('Cash required', '$160K', 'fa-wallet'),
        tile('Days of inventory', '+9 days', 'fa-calendar', 'good'),
        tile('Expedite premium', '$34K', 'fa-plane', 'bad'),
      ],
      approvalSteps: steps([
        ['fa-file-lines', 'An expedited FBA inbound shipment is created for SKU-CHR-42.'],
        ['fa-cube', 'The inventory plan is updated to reflect 200 units of incoming stock.'],
        ['fa-dollar-sign', 'The cash forecast is adjusted for the $160K outflow.'],
        ['fa-arrow-right-arrow-left', 'Supplier payment is scheduled per 30% advance / Net 15 terms.'],
      ]),
      confidence: ['92%', 'High confidence', 'Based on 38 days of sales history and stable supplier lead times.'],
      confidenceFactors: ['Stable sales trend', 'Reliable supplier', 'Sufficient cash balance'],
      disclaimer: 'Quantity and supplier can still be adjusted before you confirm.',
      alternatives: [
        ['Adjust quantity or supplier', 'Fine-tune quantity, supplier or delivery date', 'fa-pen-to-square'],
        ['Run alternate scenarios', 'Compare different order quantities and timelines', 'fa-chart-simple'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Expedited FBA inbound'),
        row('SKU', 'SKU-CHR-42'),
        row('Channel', 'Amazon'),
        row('Quantity', '200 units'),
        row('Lead time', '3 days'),
        row('Total cost', '$160K'),
        row('Inventory impact', '+9 days cover', 'good'),
      ],
      cases: ['-$34K', '+$280K', '+$360K'],
      checklist: ['Inventory implications reviewed', 'Cash flow implications reviewed', 'Simulations reviewed', 'Risks understood'],
    },
    success: ['Inbound created', '200 units of SKU-CHR-42 are booked on a 3-day expedite lane to Amazon. Inventory and cash forecasts have been updated.', 'EXP-2026-06610'],
  },

  'sig-inv-2': {
    title: ['Overstock carrying', '$160K of holding cost'],
    action: 'Run Clearance',
    reason: {
      confidence: ['High', 'Strong outlook', 78],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$160K', 'Potential impact', 56],
      checklist: [
        'SKU-OVS-88 has 118 days of cover against a 45-day target as the season ends.',
        'Long-term storage fees begin on 240 of these units in 31 days.',
        'A 20% end-of-season promo cleared comparable apparel stock at 3.6x normal velocity.',
        'Holding through to next season costs $160K in fees and tied-up capital.',
      ],
      cannotSettle:
        'Whether next season\'s demand for this colourway justifies holding rather than clearing — the buying plan is not locked yet.',
    },
    analyze: {
      metricsTitle: 'CURRENT STOCK POSITION',
      metrics: [
        m('Days of cover', '118 days', 'fa-calendar', 'bad'),
        m('Target cover', '45 days', 'fa-bullseye'),
        m('Units at LTS risk', '240 units', 'fa-warehouse', 'bad'),
        m('Days to LTS fees', '31 days', 'fa-clock', 'bad'),
        m('Holding cost if held', '$160K', 'fa-dollar-sign', 'bad'),
        m('Promo velocity multiple', '3.6x', 'fa-fire', 'good'),
        m('Sell-through (30d)', '42%', 'fa-chart-line'),
      ],
      simulationsTitle: 'CLEARANCE SIMULATIONS',
      nowTitle: 'If we run the clearance now',
      now: {
        cards: [good('HOLDING COST AVOIDED', '+$160K'), good('COVER NORMALISED', '118 → 44 days')],
        desc:
          'Clearing before the 31-day LTS deadline avoids the fee entirely and brings cover back inside the 45-day target.',
      },
      delay: {
        tabs: ['2 weeks', '31 days', '2 months'],
        cards: [bad('LTS FEES BEGIN', 'Day 31'), bad('CAPITAL LOCKED', '$160K')],
        desc: 'The LTS deadline is fixed. Past day 31 the fee is charged monthly on top of the capital already tied up.',
      },
      worst: {
        cards: [bad('MARGIN GIVEN UP', '-$58K')],
        desc: 'The colourway carries into next season strongly and the 20% discount is margin that need not have been sacrificed.',
      },
      best: {
        cards: [good('CASH AND FEES SAVED', '+$210K')],
        desc: 'The promo clears the full excess before the deadline and the freed shelf space goes to a higher-turn SKU.',
      },
    },
    decide: {
      icon: 'fa-percent',
      title: 'Run a 20% end-of-season clearance on SKU-OVS-88',
      description: 'Clears the excess ahead of the 31-day long-term storage deadline and normalises cover to 44 days.',
      tiles: [
        tile('Holding cost avoided', '+$160K', 'fa-warehouse', 'good'),
        tile('Margin given up', '-$58K', 'fa-percent', 'bad'),
        tile('Cover normalised', '44 days', 'fa-calendar', 'good'),
        tile('Deadline', '31 days', 'fa-clock', 'bad'),
      ],
      approvalSteps: steps([
        ['fa-percent', 'A 20% end-of-season discount goes live on SKU-OVS-88 on Shopify.'],
        ['fa-clock', 'The promo runs for 28 days, closing before the LTS deadline.'],
        ['fa-cube', 'The reorder point is suspended until cover returns under 45 days.'],
        ['fa-dollar-sign', 'The cash and holding-cost forecasts are updated.'],
      ]),
      confidence: ['79%', 'High confidence', 'Based on 3 comparable end-of-season clearances averaging 3.6x velocity.'],
      confidenceFactors: ['LTS deadline fixed', 'Promo history comparable', 'Next-season plan open'],
      disclaimer: 'Discount depth and promo duration can still be adjusted before you confirm.',
      alternatives: [
        ['Try 12% first', 'Test a shallower discount for 10 days before deepening', 'fa-scale-balanced'],
        ['Remove from FBA', 'Pull the 240 units to your own warehouse to dodge LTS fees', 'fa-truck'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'End-of-season clearance'),
        row('SKU', 'SKU-OVS-88'),
        row('Channel', 'Shopify'),
        row('Discount', '20%'),
        row('Duration', '28 days'),
        row('LTS deadline', '31 days'),
        row('Cover impact', '118 → 44 days', 'good'),
      ],
      cases: ['-$58K', '+$160K', '+$210K'],
      checklist: ['Cover position verified', 'LTS deadline confirmed', 'Simulations reviewed', 'Margin sacrifice accepted'],
    },
    success: ['Clearance live', 'A 20% end-of-season discount on SKU-OVS-88 is running on Shopify for 28 days, closing before the LTS deadline.', 'CLR-2026-04463'],
  },

  'sig-inv-3': {
    title: ['Reorder point reached on', 'SKU-CLN-04'],
    action: 'Create PO',
    reason: {
      confidence: ['High', 'Strong outlook', 85],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$75,000', 'Potential impact', 40],
      checklist: [
        'SKU-CLN-04 has crossed its 180-unit reorder point with 22 days of cover left.',
        'Supplier lead time is a stable 15 days, leaving a 7-day safety buffer.',
        'A 500-unit PO hits the volume break at $412/unit versus $448 at 300 units.',
        'Working capital is sufficient — the $206K outflow lands after the next Walmart settlement.',
      ],
      cannotSettle:
        'Whether to size for the volume break at 500 units or stay at 300 and preserve flexibility — demand confidence past day 45 is moderate.',
    },
    analyze: {
      metricsTitle: 'CURRENT REORDER POSITION',
      metrics: [
        m('Stock on hand', '176 units', 'fa-cube'),
        m('Reorder point', '180 units', 'fa-bullseye', 'bad'),
        m('Days of cover', '22 days', 'fa-calendar'),
        m('Supplier lead time', '15 days', 'fa-truck-fast'),
        m('Safety buffer', '7 days', 'fa-shield-halved', 'good'),
        m('Unit cost at 500', '$412', 'fa-tag', 'good'),
        m('Unit cost at 300', '$448', 'fa-tag'),
      ],
      simulationsTitle: 'REORDER SIMULATIONS',
      nowTitle: 'If we issue the 500-unit PO now',
      now: {
        cards: [good('VOLUME SAVING', '+$18K'), good('COVER EXTENDED', '+62 days')],
        desc:
          'Ordering 500 units hits the price break and lands 7 days before the reorder point is breached.',
      },
      delay: {
        tabs: ['3 days', '7 days', '14 days'],
        cards: [bad('BUFFER ERODES', '7 → 0 days'), bad('EXPEDITE RISK', 'Rising')],
        desc: 'The 15-day lead time is fixed, so each day of delay eats directly into the 7-day safety buffer.',
      },
      worst: {
        cards: [bad('EXCESS AT DAY 90', '140 units')],
        desc: 'Demand softens after day 45 and the 500-unit order leaves stock to carry into the following quarter.',
      },
      best: {
        cards: [good('SAVING AND COVER', '+$34K')],
        desc: 'Demand holds, the volume break is captured in full, and the longer cover avoids a second PO cycle.',
      },
    },
    decide: {
      icon: 'fa-file-circle-plus',
      title: 'Issue PO #4082 for 500 units of SKU-CLN-04',
      description: 'Hits the $412 volume break on a 15-day lead time, landing 7 days before the reorder point is breached.',
      tiles: [
        tile('Volume saving', '+$18K', 'fa-hand-holding-dollar', 'good'),
        tile('Cash required', '$206K', 'fa-wallet'),
        tile('Days of inventory', '+62 days', 'fa-calendar', 'good'),
        tile('Safety buffer', '7 days', 'fa-shield-halved', 'good'),
      ],
      approvalSteps: steps([
        ['fa-file-circle-plus', 'PO #4082 is issued to the supplier for 500 units of SKU-CLN-04.'],
        ['fa-truck-fast', 'Delivery is booked on the standard 15-day lane.'],
        ['fa-dollar-sign', 'The cash forecast is adjusted for the $206K outflow after settlement.'],
        ['fa-cube', 'The inventory plan is updated with 500 units of incoming stock.'],
      ]),
      confidence: ['85%', 'High confidence', 'Based on a stable 15-day lead time across the last 6 POs and a firm volume break.'],
      confidenceFactors: ['Lead time stable', 'Volume break confirmed', 'Demand past day 45 moderate'],
      disclaimer: 'Order quantity and delivery date can still be adjusted before you confirm.',
      alternatives: [
        ['Order 300 units instead', 'Preserve flexibility at $448/unit and reorder sooner', 'fa-scale-balanced'],
        ['Run alternate scenarios', 'Compare 300, 500 and 750-unit orders against cover', 'fa-chart-simple'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Purchase Order'),
        row('SKU', 'SKU-CLN-04'),
        row('Channel', 'Walmart'),
        row('Quantity', '500 units'),
        row('Unit cost', '$412'),
        row('Total cost', '$206K'),
        row('Inventory impact', '+62 days cover', 'good'),
      ],
      cases: ['-$26K', '+$75K', '+$34K'],
      checklist: ['Reorder point verified', 'Volume break confirmed', 'Simulations reviewed', 'Cash timing checked'],
    },
    success: ['Purchase order issued', 'PO #4082 for 500 units of SKU-CLN-04 is with the supplier on a 15-day lane at $412/unit.', 'PO-2026-04082'],
  },

  /* ══════════ ADS ══════════ */

  'sig-ads-1': {
    title: ['ROAS collapsed from 4.2x to', '1.8x'],
    action: 'Pause Campaign',
    reason: {
      confidence: ['High', 'Strong outlook', 88],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$195K', 'Potential impact', 66],
      checklist: [
        'Smart Camera SP Broad has dropped from 4.2x to 1.8x ROAS over 14 days.',
        'CPC on generic terms rose 42% while conversion rate on the same terms fell by half.',
        'Broad match accounts for 78% of the campaign\'s $92,400 spend and 31% of its revenue.',
        'The paired exact-match campaign is converting at 4.4x and is budget-capped.',
      ],
      cannotSettle:
        'Whether the CPC spike is click fraud or genuine new competition — the traffic quality signals point both ways.',
    },
    analyze: {
      metricsTitle: 'CURRENT CAMPAIGN POSITION',
      metrics: [
        m('Campaign spend (30d)', '$92,400', 'fa-bullhorn'),
        m('Current ROAS', '1.8x', 'fa-chart-line', 'bad'),
        m('Target ROAS', '4.2x', 'fa-bullseye'),
        m('ACoS', '41%', 'fa-percent', 'bad'),
        m('CPC change', '+42%', 'fa-arrow-up', 'bad'),
        m('Broad share of spend', '78%', 'fa-chart-pie', 'bad'),
        m('Exact-match ROAS', '4.4x', 'fa-crosshairs', 'good'),
      ],
      simulationsTitle: 'ADS SIMULATIONS',
      nowTitle: 'If we pause broad and shift budget now',
      now: {
        cards: [good('BLENDED ROAS', '1.8x → 4.1x'), good('SPEND RECOVERED', '+$195K')],
        desc:
          'Moving the broad budget onto the capped exact-match campaign redeploys spend into traffic already converting at 4.4x.',
      },
      delay: {
        tabs: ['3 days', '1 week', '2 weeks'],
        cards: [bad('SPEND WASTED', '$21K/wk'), bad('ACOS DRIFT', '41% → 48%')],
        desc: 'CPC is still climbing, so the gap between broad and exact efficiency widens with every day of delay.',
      },
      worst: {
        cards: [bad('DISCOVERY LOST', '-$28K')],
        desc: 'Broad match was seeding new converting search terms and the exact-match campaign cannot replace that discovery volume.',
      },
      best: {
        cards: [good('PROFIT RECOVERED', '+$240K')],
        desc: 'Exact match absorbs the full budget at 4.4x, the CPC spike proves to be fraud, and blended ROAS clears target.',
      },
    },
    decide: {
      icon: 'fa-circle-pause',
      title: 'Pause broad match and shift budget to exact match',
      description: 'Pauses the underperforming broad keywords and lifts the exact-match campaign daily cap by the freed amount.',
      tiles: [
        tile('Spend recovered', '+$195K', 'fa-shield-halved', 'good'),
        tile('Blended ROAS', '4.1x', 'fa-chart-line', 'good'),
        tile('ACoS', '41% → 24%', 'fa-percent', 'good'),
        tile('Time to effect', '~1 hr', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-circle-pause', 'Broad match keywords on Smart Camera SP Broad are paused.'],
        ['fa-arrow-up-right-dots', 'The exact-match campaign daily cap rises by the freed $72,000/mo.'],
        ['fa-magnifying-glass', 'Search-term mining stays on so new converting terms are still surfaced.'],
        ['fa-chart-line', 'Blended ROAS is reviewed at 14 days against the 4.2x target.'],
      ]),
      confidence: ['88%', 'High confidence', 'Based on 14 days of search-term data and a proven 4.4x exact-match benchmark.'],
      confidenceFactors: ['Spend data unambiguous', 'Exact match proven', 'Discovery loss unquantified'],
      disclaimer: 'The budget shift amount and review window can still be adjusted before you confirm.',
      alternatives: [
        ['Cut broad bids by 60%', 'Keep discovery alive at much lower spend', 'fa-sliders'],
        ['Negate the worst terms only', 'Target the eight highest-CPC terms instead of pausing broad', 'fa-ban'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Campaign pause + budget shift'),
        row('Campaign', 'Smart Camera SP Broad'),
        row('Channel', 'Amazon'),
        row('Budget shifted', '$72,000/mo'),
        row('Destination', 'Exact-match campaign'),
        row('ROAS impact', '1.8x → 4.1x', 'good'),
        row('Spend recovered', '+$195K', 'good'),
      ],
      cases: ['-$28K', '+$195K', '+$240K'],
      checklist: ['Search-term data reviewed', 'Exact-match headroom confirmed', 'Simulations reviewed', 'Discovery risk understood'],
    },
    success: ['Campaign paused', 'Broad match is paused on Smart Camera SP Broad and $72,000/mo has moved to the exact-match campaign.', 'ADS-2026-07219'],
  },

  'sig-ads-2': {
    title: ['Ad dependency reached', '18.4% TACoS'],
    action: 'Optimize Bids',
    reason: {
      confidence: ['High', 'Strong outlook', 82],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$130K', 'Potential impact', 52],
      checklist: [
        'TACoS on SKU-VAC-01 has reached 18.4% against a 12.0% target ceiling.',
        'Ad-attributed sales are 65% of total sales — the listing is leaning on paid traffic to hold rank.',
        'Non-branded keywords carry 71% of the spend at a 3.1x ROAS versus 6.8x on branded.',
        'Organic rank is #4 and stable, so it can carry more volume if bids come down.',
      ],
      cannotSettle:
        'How much organic rank depends on paid velocity on this listing — cutting bids may soften the rank that is meant to absorb the volume.',
    },
    analyze: {
      metricsTitle: 'CURRENT DEPENDENCY POSITION',
      metrics: [
        m('TACoS', '18.4%', 'fa-percent', 'bad'),
        m('Target TACoS', '12.0%', 'fa-bullseye'),
        m('Ad share of sales', '65%', 'fa-chart-pie', 'bad'),
        m('Non-branded ROAS', '3.1x', 'fa-chart-line', 'bad'),
        m('Branded ROAS', '6.8x', 'fa-chart-line', 'good'),
        m('Non-branded share of spend', '71%', 'fa-bullhorn', 'bad'),
        m('Organic rank', '#4', 'fa-ranking-star', 'good'),
      ],
      simulationsTitle: 'DEPENDENCY SIMULATIONS',
      nowTitle: 'If we cut non-branded bids by 15% now',
      now: {
        cards: [good('TACOS', '18.4% → 12.6%'), good('PROFIT PROTECTED', '+$130K')],
        desc:
          'A 15% bid reduction on non-branded terms trims the lowest-efficiency spend while organic rank absorbs the volume.',
      },
      delay: {
        tabs: ['1 week', '2 weeks', '1 month'],
        cards: [bad('PROFIT DRAIN', '$32K/wk'), bad('TACOS DRIFT', '18.4% → 21%')],
        desc: 'Ad dependency is self-reinforcing: the longer paid carries the volume, the weaker the organic signal becomes.',
      },
      worst: {
        cards: [bad('VOLUME LOST', '-18%')],
        desc: 'Organic rank slips to #9 once paid velocity drops and total sales fall further than the ad saving covers.',
      },
      best: {
        cards: [good('PROFIT PROTECTED', '+$180K')],
        desc: 'Organic absorbs the volume fully, TACoS lands under 12%, and net margin recovers 3.4 points.',
      },
    },
    decide: {
      icon: 'fa-sliders',
      title: 'Lower non-branded bids by 15% on SKU-VAC-01',
      description: 'Trims the 3.1x ROAS non-branded spend and lets a stable #4 organic rank carry more of the volume.',
      tiles: [
        tile('Profit protected', '+$130K', 'fa-shield-halved', 'good'),
        tile('TACoS', '18.4% → 12.6%', 'fa-percent', 'good'),
        tile('Volume risk', '-6%', 'fa-cart-shopping', 'bad'),
        tile('Time to effect', '~2 hrs', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-sliders', 'Bids on all non-branded keywords drop by 15%.'],
        ['fa-crown', 'Branded campaigns are left untouched at their 6.8x ROAS.'],
        ['fa-ranking-star', 'Organic rank is tracked daily for signs of slippage below #6.'],
        ['fa-rotate-left', 'Bids restore automatically if organic rank falls past #6.'],
      ]),
      confidence: ['82%', 'High confidence', 'Based on 30 days of TACoS history and a stable organic rank at #4.'],
      confidenceFactors: ['Spend split verified', 'Organic rank stable', 'Paid-organic coupling unclear'],
      disclaimer: 'The bid reduction and the rank guardrail can still be adjusted before you confirm.',
      alternatives: [
        ['Cut by 8% instead', 'Halve the bid reduction and re-measure in 10 days', 'fa-scale-balanced'],
        ['Cut only the worst terms', 'Reduce bids on the 12 lowest-ROAS terms rather than all', 'fa-crosshairs'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Bid optimisation'),
        row('SKU', 'SKU-VAC-01'),
        row('Channel', 'Amazon'),
        row('Bid change', '-15% non-branded'),
        row('Branded campaigns', 'Unchanged'),
        row('Rank guardrail', 'Restore below #6'),
        row('TACoS impact', '18.4% → 12.6%', 'good'),
      ],
      cases: ['-$42K', '+$130K', '+$180K'],
      checklist: ['Spend split reviewed', 'Organic rank verified', 'Simulations reviewed', 'Guardrail set'],
    },
    success: ['Bids updated', 'Non-branded bids on SKU-VAC-01 are down 15% with an automatic restore if organic rank falls past #6.', 'BID-2026-05877'],
  },

  'sig-ads-3': {
    title: ['Campaign capping out at', '11:00 AM daily'],
    action: 'Scale Budget',
    reason: {
      confidence: ['High', 'Strong outlook', 84],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$82,000', 'Potential impact', 38],
      checklist: [
        '"lumbar support chair" is returning 8.4x ROAS against a 5.0x category floor.',
        'The campaign exhausts its $500/day cap by 11:00 AM every day.',
        'Walmart search volume on this term peaks between 2 PM and 8 PM — entirely unserved.',
        'Raising the cap is reversible same-day and needs no creative work.',
      ],
      cannotSettle:
        'Whether efficiency holds at 5x the spend — the 8.4x ROAS is measured on morning traffic only, and afternoon intent may differ.',
    },
    analyze: {
      metricsTitle: 'CURRENT CAMPAIGN POSITION',
      metrics: [
        m('Current daily cap', '$500/day', 'fa-wallet', 'bad'),
        m('Cap exhausted by', '11:00 AM', 'fa-clock', 'bad'),
        m('Current ROAS', '8.4x', 'fa-chart-line', 'good'),
        m('Category ROAS floor', '5.0x', 'fa-bullseye'),
        m('Unserved peak window', '2 PM – 8 PM', 'fa-moon', 'bad'),
        m('Spend (30d)', '$8,200', 'fa-bullhorn'),
        m('Upside (30d)', '$82,000', 'fa-arrow-trend-up', 'good'),
      ],
      simulationsTitle: 'SCALE SIMULATIONS',
      nowTitle: 'If we raise the cap to $2,500/day now',
      now: {
        cards: [good('REVENUE ADDED', '+$82K'), good('DAY COVERAGE', '11 AM → full day')],
        desc:
          'Full-day coverage captures the 2 PM to 8 PM peak that the campaign currently never reaches.',
      },
      delay: {
        tabs: ['1 week', '2 weeks', '1 month'],
        cards: [bad('REVENUE FORGONE', '-$19K/wk'), flat('DOWNSIDE OF WAITING', 'None')],
        desc: 'Nothing degrades by waiting — this is pure opportunity cost while the term stays efficient.',
      },
      worst: {
        cards: [bad('ROAS DILUTION', '8.4x → 3.8x')],
        desc: 'Afternoon traffic converts far worse than morning traffic and the extra $2,000/day lands below the 5.0x floor.',
      },
      best: {
        cards: [good('REVENUE ADDED', '+$140K')],
        desc: 'Efficiency holds near 8x across the full day and the term becomes a second core campaign.',
      },
    },
    decide: {
      icon: 'fa-arrow-up-right-dots',
      title: 'Raise the daily cap from $500 to $2,500',
      description: 'Extends coverage on an 8.4x ROAS term through the unserved 2 PM to 8 PM search peak.',
      tiles: [
        tile('Revenue added', '+$82K', 'fa-arrow-trend-up', 'good'),
        tile('Additional spend', '$2,000/day', 'fa-wallet'),
        tile('Current ROAS', '8.4x', 'fa-chart-line', 'good'),
        tile('Time to effect', 'Same day', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-arrow-up-right-dots', 'The campaign daily cap rises from $500 to $2,500 on Walmart.'],
        ['fa-clock', 'Dayparting stays off so the full search day is covered.'],
        ['fa-chart-line', 'ROAS is reviewed at 7 days against the 5.0x floor.'],
        ['fa-rotate-left', 'The cap reverts automatically if ROAS falls below 5.0x for 3 days.'],
      ]),
      confidence: ['84%', 'High confidence', 'Based on 30 days at 8.4x ROAS, though measured only on pre-11 AM traffic.'],
      confidenceFactors: ['ROAS well above floor', 'Same-day reversibility', 'Afternoon intent untested'],
      disclaimer: 'The cap and the ROAS guardrail can still be adjusted before you confirm.',
      alternatives: [
        ['Raise to $1,200 first', 'Step up gradually and verify afternoon efficiency', 'fa-stairs'],
        ['Add dayparting', 'Weight the extra budget toward the 2 PM to 8 PM window only', 'fa-clock'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Budget scale-up'),
        row('Campaign', 'Lumbar Chair Prospecting'),
        row('Channel', 'Walmart'),
        row('Current cap', '$500/day'),
        row('New cap', '$2,500/day'),
        row('ROAS guardrail', 'Revert below 5.0x'),
        row('Revenue impact', '+$82,000', 'good'),
      ],
      cases: ['-$14K', '+$82K', '+$140K'],
      checklist: ['ROAS history reviewed', 'Peak window confirmed', 'Simulations reviewed', 'Guardrail set'],
    },
    success: ['Budget scaled', 'The Lumbar Chair Prospecting cap is now $2,500/day on Walmart with an automatic revert below 5.0x ROAS.', 'SCL-2026-03361'],
  },

  'sig-ads-4': {
    title: ['Creative fatigued at', 'frequency 7.8'],
    action: 'Refresh Creative',
    reason: {
      confidence: ['High', 'Strong outlook', 80],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$142K', 'Potential impact', 50],
      checklist: [
        'The same three creatives have served the cart-abandoner audience for 46 days.',
        'Frequency has reached 7.8 — each shopper has seen the set nearly eight times.',
        'CTR has decayed from 2.1% to 1.3% while CPM held flat, which is textbook fatigue.',
        'Three replacement lifestyle creatives are already approved and ready to ship.',
      ],
      cannotSettle:
        'Whether the audience itself is exhausted rather than the creative — the cart-abandoner pool has not been refreshed in 46 days either.',
    },
    analyze: {
      metricsTitle: 'CURRENT CREATIVE POSITION',
      metrics: [
        m('Creative age', '46 days', 'fa-clock', 'bad'),
        m('Frequency', '7.8', 'fa-repeat', 'bad'),
        m('CTR now', '1.3%', 'fa-hand-pointer', 'bad'),
        m('CTR at launch', '2.1%', 'fa-hand-pointer'),
        m('CPM change', 'Flat', 'fa-chart-bar'),
        m('Current ROAS', '4.2x', 'fa-chart-line'),
        m('Replacement creatives', '3 approved', 'fa-images', 'good'),
      ],
      simulationsTitle: 'CREATIVE SIMULATIONS',
      nowTitle: 'If we refresh the creative set now',
      now: {
        cards: [good('CTR RECOVERY', '1.3% → 2.0%'), good('REVENUE RECOVERED', '+$142K')],
        desc:
          'Swapping all three creatives and capping frequency at 4 resets the audience without touching targeting or budget.',
      },
      delay: {
        tabs: ['1 week', '2 weeks', '1 month'],
        cards: [bad('CTR DECAY', '1.3% → 0.9%'), bad('ROAS DRIFT', '4.2x → 3.1x')],
        desc: 'Fatigue compounds — frequency keeps climbing on the same pool, so every week costs more CTR than the last.',
      },
      worst: {
        cards: [bad('NO RECOVERY', '$0')],
        desc: 'The audience pool rather than the creative is exhausted, and new creatives serve the same tired shoppers.',
      },
      best: {
        cards: [good('REVENUE RECOVERED', '+$210K')],
        desc: 'CTR returns above launch level at 2.3%, the frequency cap widens reach, and ROAS clears 5x.',
      },
    },
    decide: {
      icon: 'fa-wand-magic-sparkles',
      title: 'Refresh the retargeting creative set on Shopify',
      description: 'Swaps in three approved lifestyle creatives and caps frequency at 4 to reset audience fatigue.',
      tiles: [
        tile('Revenue recovered', '+$142K', 'fa-arrow-trend-up', 'good'),
        tile('Production cost', '$0', 'fa-wallet', 'good'),
        tile('CTR recovery', '2.0%', 'fa-hand-pointer', 'good'),
        tile('Time to effect', '~4 hrs', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-images', 'Three approved lifestyle creatives replace the fatigued set.'],
        ['fa-repeat', 'A frequency cap of 4 is applied to the cart-abandoner audience.'],
        ['fa-hand-pointer', 'CTR and ROAS are tracked daily for 14 days against the pre-fatigue baseline.'],
        ['fa-users', 'The audience pool is refreshed in parallel to rule out pool exhaustion.'],
      ]),
      confidence: ['80%', 'High confidence', 'Flat CPM alongside decaying CTR is a clean fatigue signature across 46 days.'],
      confidenceFactors: ['Fatigue signature clear', 'Creatives ready', 'Pool exhaustion possible'],
      disclaimer: 'Frequency cap and creative mix can still be adjusted before you confirm.',
      alternatives: [
        ['Rotate one creative', 'Swap a single creative to isolate the fatigue variable', 'fa-shuffle'],
        ['Refresh the audience only', 'Rebuild the cart-abandoner pool and keep the creatives', 'fa-users'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Creative refresh'),
        row('Campaign', 'Retargeting Cart Abandoners'),
        row('Channel', 'Shopify'),
        row('Creatives swapped', '3'),
        row('Frequency cap', '4'),
        row('Production cost', '$0'),
        row('CTR impact', '1.3% → 2.0%', 'good'),
      ],
      cases: ['$0', '+$142K', '+$210K'],
      checklist: ['Fatigue signature verified', 'Creatives approved', 'Simulations reviewed', 'Pool refresh queued'],
    },
    success: ['Creative refreshed', 'Three new creatives are live on Retargeting Cart Abandoners with a frequency cap of 4. CTR tracking runs for 14 days.', 'CRF-2026-08145'],
  },

  'sig-ads-5': {
    title: ['Walmart budget pacing at', '62%'],
    action: 'Rebalance Budget',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 70],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$185K', 'Potential impact', 54],
      checklist: [
        'Prospecting Rider Gear is pacing to spend only 62% of its monthly budget.',
        'It is returning 4.9x ROAS against a 3.0x floor, so the unspent budget is efficient headroom.',
        'Impressions are available — the campaign is bid-limited, not inventory-limited.',
        'Raising daily pacing is reversible same-day and needs no creative or targeting change.',
      ],
      cannotSettle:
        'Whether the campaign is bid-limited or genuinely out of qualified audience — Walmart does not expose impression share directly.',
    },
    analyze: {
      metricsTitle: 'CURRENT PACING POSITION',
      metrics: [
        m('Budget pacing', '62%', 'fa-gauge-high', 'bad'),
        m('Spend (30d)', '$55,500', 'fa-bullhorn'),
        m('Current ROAS', '4.9x', 'fa-chart-line', 'good'),
        m('ROAS floor', '3.0x', 'fa-bullseye'),
        m('Impressions (30d)', '12,40,000', 'fa-eye'),
        m('Clicks (30d)', '8,900', 'fa-hand-pointer'),
        m('Unspent budget', '$34,000/mo', 'fa-wallet', 'bad'),
      ],
      simulationsTitle: 'PACING SIMULATIONS',
      nowTitle: 'If we lift daily pacing now',
      now: {
        cards: [good('REVENUE ADDED', '+$185K'), good('PACING', '62% → 96%')],
        desc:
          'Deploying the full monthly budget at the current 4.9x return converts unspent allowance directly into revenue.',
      },
      delay: {
        tabs: ['1 week', '2 weeks', '1 month'],
        cards: [bad('BUDGET UNSPENT', '$8K/wk'), flat('DOWNSIDE OF WAITING', 'None')],
        desc: 'Unspent budget does not roll over, so each week of underpacing is permanently forgone revenue.',
      },
      worst: {
        cards: [bad('ROAS DILUTION', '4.9x → 2.7x')],
        desc: 'The campaign was audience-limited rather than bid-limited, and the extra spend buys unqualified traffic below the floor.',
      },
      best: {
        cards: [good('REVENUE ADDED', '+$280K')],
        desc: 'Efficiency holds at 4.9x on the full budget and the campaign becomes the strongest Walmart line item.',
      },
    },
    decide: {
      icon: 'fa-scale-balanced',
      title: 'Lift daily pacing on Prospecting Rider Gear',
      description: 'Raises daily pacing so the full monthly budget deploys at the current 4.9x ROAS.',
      tiles: [
        tile('Revenue added', '+$185K', 'fa-arrow-trend-up', 'good'),
        tile('Budget deployed', '$34K/mo', 'fa-wallet'),
        tile('Pacing', '62% → 96%', 'fa-gauge-high', 'good'),
        tile('Time to effect', 'Same day', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-gauge-high', 'Daily pacing rises so the full monthly budget deploys evenly.'],
        ['fa-chart-line', 'ROAS is reviewed at 10 days against the 3.0x floor.'],
        ['fa-eye', 'Impression and click volume are tracked to confirm the campaign was bid-limited.'],
        ['fa-rotate-left', 'Pacing reverts automatically if ROAS falls below 3.0x for 3 days.'],
      ]),
      confidence: ['72%', 'Medium confidence', 'Efficiency is well documented; whether headroom is bid-limited or audience-limited is not.'],
      confidenceFactors: ['ROAS above floor', 'Same-day reversibility', 'Impression share unknown'],
      disclaimer: 'Pacing target and the ROAS guardrail can still be adjusted before you confirm.',
      alternatives: [
        ['Lift to 80% first', 'Step pacing up gradually and verify efficiency holds', 'fa-stairs'],
        ['Move budget elsewhere', 'Reallocate the unspent $34K to the retargeting campaign', 'fa-arrows-turn-right'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Budget rebalance'),
        row('Campaign', 'Prospecting Rider Gear'),
        row('Channel', 'Walmart'),
        row('Current pacing', '62%'),
        row('Target pacing', '96%'),
        row('Budget deployed', '$34,000/mo'),
        row('Revenue impact', '+$185K', 'good'),
      ],
      cases: ['-$22K', '+$185K', '+$280K'],
      checklist: ['Pacing gap verified', 'ROAS floor confirmed', 'Simulations reviewed', 'Guardrail set'],
    },
    success: ['Budget rebalanced', 'Prospecting Rider Gear now paces to 96% of its monthly Walmart budget with an automatic revert below 3.0x ROAS.', 'PCE-2026-02736'],
  },

  'sig-ads-6': {
    title: ['12 search terms with', 'no paid coverage'],
    action: 'Scale Budget',
    reason: {
      confidence: ['Medium', 'Moderate outlook', 64],
      agents: ['4 contributed', 'Active in this decision', 60],
      atRisk: ['$42,000', 'Potential impact', 26],
      checklist: [
        'Brand Store Launch SB converts at 29% ACoS, inside the 35% target ceiling.',
        'Twelve brand-adjacent search terms show organic impressions with zero paid coverage.',
        'The campaign is only capturing 45,000 impressions of available category inventory.',
        'Adding exact-match keywords at a $18 opening bid is reversible within the day.',
      ],
      cannotSettle:
        'Whether brand-adjacent terms will convert like branded terms — they sit between branded and generic intent, and neither benchmark clearly applies.',
    },
    analyze: {
      metricsTitle: 'CURRENT COVERAGE POSITION',
      metrics: [
        m('Current ACoS', '29%', 'fa-percent', 'good'),
        m('Target ACoS ceiling', '35%', 'fa-bullseye'),
        m('Impressions (30d)', '45,000', 'fa-eye', 'bad'),
        m('Clicks (30d)', '900', 'fa-hand-pointer'),
        m('Spend (30d)', '$26,000', 'fa-bullhorn'),
        m('Uncovered terms', '12', 'fa-key', 'bad'),
        m('Upside (30d)', '$42,000', 'fa-arrow-trend-up', 'good'),
      ],
      simulationsTitle: 'COVERAGE SIMULATIONS',
      nowTitle: 'If we add the 12 keywords now',
      now: {
        cards: [good('REVENUE ADDED', '+$42K'), good('IMPRESSION REACH', '+68%')],
        desc:
          'Twelve exact-match keywords at $18 widen paid reach across terms that already show organic demand.',
      },
      delay: {
        tabs: ['2 weeks', '1 month', '2 months'],
        cards: [bad('REVENUE FORGONE', '-$42K'), flat('DOWNSIDE OF WAITING', 'None')],
        desc: 'The terms stay uncovered and competitors may establish position on them, but nothing actively degrades.',
      },
      worst: {
        cards: [bad('ACOS DILUTION', '29% → 44%')],
        desc: 'Brand-adjacent terms convert like generics, ACoS breaks the 35% ceiling, and the added spend returns little.',
      },
      best: {
        cards: [good('REVENUE ADDED', '+$96K')],
        desc: 'The terms convert close to branded intent, ACoS holds near 29%, and the campaign doubles its reach profitably.',
      },
    },
    decide: {
      icon: 'fa-arrow-up-right-dots',
      title: 'Add 12 brand-adjacent keywords in exact match',
      description: 'Opens paid coverage on twelve terms that already show organic impressions, at a $18 opening bid.',
      tiles: [
        tile('Revenue added', '+$42K', 'fa-arrow-trend-up', 'good'),
        tile('Opening bid', '$18', 'fa-wallet'),
        tile('Impression reach', '+68%', 'fa-eye', 'good'),
        tile('Time to effect', '~1 day', 'fa-clock'),
      ],
      approvalSteps: steps([
        ['fa-key', 'Twelve brand-adjacent keywords are added in exact match at a $18 bid.'],
        ['fa-percent', 'A 35% ACoS guardrail is applied at the ad-group level.'],
        ['fa-chart-line', 'Per-keyword ACoS is reviewed at 14 days and losers are paused.'],
        ['fa-rotate-left', 'The whole keyword set can be removed in one action.'],
      ]),
      confidence: ['66%', 'Medium confidence', 'Organic demand on the terms is verified; paid conversion intent on brand-adjacent terms is not.'],
      confidenceFactors: ['Organic demand verified', 'ACoS headroom exists', 'Adjacent intent untested'],
      disclaimer: 'Opening bid and the ACoS guardrail can still be adjusted before you confirm.',
      alternatives: [
        ['Start with 4 keywords', 'Test the highest-volume terms before committing to all 12', 'fa-flask'],
        ['Use phrase match', 'Cast slightly wider and mine the search terms first', 'fa-magnifying-glass'],
      ],
    },
    confirm: {
      summary: [
        row('Action', 'Keyword expansion'),
        row('Campaign', 'Brand Store Launch SB'),
        row('Channel', 'Amazon'),
        row('Keywords added', '12'),
        row('Match type', 'Exact'),
        row('Opening bid', '$18'),
        row('Revenue impact', '+$42,000', 'good'),
      ],
      cases: ['-$11K', '+$42K', '+$96K'],
      checklist: ['Organic demand verified', 'ACoS headroom confirmed', 'Simulations reviewed', 'Guardrail set'],
    },
    success: ['Keywords added', 'Twelve brand-adjacent exact-match keywords are live on Brand Store Launch SB at a $18 bid with a 35% ACoS guardrail.', 'KWD-2026-01952'],
  },
};

/* ── channel chip styling ── */

const CHANNEL_CHIPS = {
  amazon: { label: 'Amazon', icon: 'fa-brands fa-amazon', className: 'bg-[#FFF7ED] dark:bg-amber-950/50 text-[#EA580C] dark:text-amber-400' },
  shopify: { label: 'Shopify', icon: 'fa-brands fa-shopify', className: 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400' },
  walmart: { label: 'Walmart', icon: 'fa-solid fa-store', className: 'bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400' },
};

const channelChip = (signal) => {
  const raw = (signal.sourceOwn || signal.channel || signal.marketplace || 'amazon').toLowerCase();
  const key = Object.keys(CHANNEL_CHIPS).find((k) => raw.includes(k)) || 'amazon';
  return CHANNEL_CHIPS[key];
};

/**
 * Scope chip beside the channel and category.
 *
 * A single SKU is worth naming — the user can act on the ID directly. Beyond
 * one, the ID would be a lie about scope (it names only the first of several),
 * so the count is shown instead and the list stays in the Actions table.
 */
const skuChip = (signal) => {
  const count = signal.skuCount || signal.affectedSkusCount || 1;
  if (count > 1) return `${count} SKUs`;
  return signal.campaign || signal.skuCode;
};

/* ── expansion ── */

const AGENT_TONES = {
  blue: 'bg-[#e6f4ff] dark:bg-blue-900/30 text-[#0066cc] dark:text-blue-400',
  orange: 'bg-[#fff0e6] dark:bg-orange-900/30 text-[#cc5200] dark:text-orange-400',
  emerald: 'bg-[#e6ffed] dark:bg-emerald-900/30 text-[#009933] dark:text-emerald-400',
};

const buildAgentTrace = (domain) => {
  const roster = AGENTS[domain] || AGENTS.sales;
  return {
    count: roster.length,
    badges: roster.map(([code, tone]) => ({ code, className: AGENT_TONES[tone] })),
    lines: roster.map(([code, , text]) => ({ code, text })),
  };
};

/**
 * Everything the Simulation panel renders for one action.
 *
 * Falls back to values derived from the signal when a spec is missing, so an
 * action without hand-written copy still renders a coherent, on-topic panel.
 */
export const getSimulation = (signal) => {
  if (!signal) return null;

  const spec = SPECS[signal.id] || {};
  const domain = signal.tabKey || 'sales';
  const exposure =
    typeof signal.exposure === 'number'
      ? formatCompactMoney(signal.exposure)
      : signal.exposureFormatted || '—';

  const [titlePrefix, titleHighlight] = spec.title || [signal.headline || 'Signal detected', ''];
  const r = spec.reason || {};
  const [confValue = signal.confidenceLabel || 'High', confCaption = 'Strong outlook', confPct = 80] = r.confidence || [];
  const [agentsValue = '4 contributed', agentsCaption = 'Active in this decision', agentsPct = 60] = r.agents || [];
  const [riskValue = exposure, riskCaption = 'Potential impact', riskPct = 55] = r.atRisk || [];

  const a = spec.analyze || {};
  const d = spec.decide || {};
  const c = spec.confirm || {};
  const [okTitle = 'Action applied', okDesc = 'The plan has been applied and forecasts updated automatically.', okRef = 'ACT-2026-00000'] = spec.success || [];
  const [confScore = '—', confLevel = 'Confidence', confDesc = ''] = d.confidence || [];
  const cases = c.cases || ['—', exposure, '—'];

  return {
    title: { prefix: titlePrefix, highlight: titleHighlight },
    subtitle: `Opened from Actions • ${spec.action || signal.tagCategory || 'Review'}`,
    chips: {
      channel: channelChip(signal),
      category: signal.category,
      sku: skuChip(signal),
    },
    reason: {
      confidence: { value: confValue, caption: confCaption, pct: confPct },
      agents: { value: agentsValue, caption: agentsCaption, pct: agentsPct },
      atRisk: { value: riskValue, caption: riskCaption, pct: riskPct },
      checklist: r.checklist || [signal.whyMattersText || signal.headline].filter(Boolean),
      agentTrace: buildAgentTrace(domain),
      cannotSettle: r.cannotSettle,
    },
    analyze: {
      metricsTitle: a.metricsTitle || 'CURRENT POSITION',
      metrics: a.metrics || [],
      simulationsTitle: a.simulationsTitle || 'SIMULATIONS',
      simulations: a.nowTitle ? buildSims(a) : [],
    },
    decide: {
      recommendedAction: {
        icon: d.icon || 'fa-circle-check',
        label: 'RECOMMENDED ACTION',
        title: d.title || signal.headlineHighlight || '',
        description: d.description || signal.whyMattersText || '',
        metrics: d.tiles || [],
      },
      approvalStepsTitle: 'WHAT HAPPENS AFTER APPROVAL',
      approvalSteps: d.approvalSteps || [],
      confidenceTitle: 'DECISION CONFIDENCE',
      confidenceScore: confScore,
      confidenceLevel: confLevel,
      confidenceDescription: confDesc,
      confidenceFactors: d.confidenceFactors || [],
      confidenceDisclaimer: d.disclaimer || '',
      alternativesTitle: 'YOU CAN ALSO',
      alternatives: (d.alternatives || []).map(([title, description, icon]) => ({ title, description, icon })),
    },
    confirm: {
      actionSummaryTitle: 'ACTION SUMMARY',
      actionSummary: c.summary || [],
      simulationSummaryTitle: 'SIMULATION SUMMARY',
      simulationCards: [
        { type: 'worst', title: 'Worst Case', value: cases[0], subtitle: 'Potential loss' },
        { type: 'expected', title: 'Expected Case', value: cases[1], subtitle: 'Expected outcome' },
        { type: 'best', title: 'Best Case', value: cases[2], subtitle: 'Potential gain' },
      ],
      checklistTitle: 'FINAL CHECKLIST',
      checklist: c.checklist || [],
    },
    success: { title: okTitle, description: okDesc, referenceCode: okRef },
  };
};

export default SPECS;
