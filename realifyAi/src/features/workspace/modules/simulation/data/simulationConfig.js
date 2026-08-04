/** Channel list, timeframes, per-tab copy and step definitions for the
 *  Workspace simulation page. Presentation configuration only — no logic. */

/* ── Constants ────────────────────────────────────────────────────────────── */
export const ALL_CHANNELS = ['Amazon', 'Shopify', 'Walmart Marketplace', 'eBay', 'TikTok Shop'];

export const TIMEFRAMES = [
  { value: '2weeks',   label: 'Next 2 Weeks' },
  { value: '4weeks',   label: 'Next 4 Weeks' },
  { value: '3months',  label: 'Next 3 Months' },
  { value: '6months',  label: 'Next 6 Months' },
];

export const WORKSPACE_TAB_META = {
  sales:     { label: 'Sales',     icon: 'fa-dollar-sign'    },
  margin:    { label: 'Margin',    icon: 'fa-chart-line'     },
  inventory: { label: 'Inventory', icon: 'fa-boxes-stacked'  },
  ads:       { label: 'Ads',       icon: 'fa-bullhorn'       },
  cash:      { label: 'Cash',      icon: 'fa-money-bill-wave'},
};

// val1 = "current" input, val2 = "simulated/target" input
export const INPUT_CONFIG = {
  sales:     { val1Label: 'Current Price',           val1Prefix: '$', val2Label: 'Target Price',           val2Prefix: '$', val2Unit: '',      val1Default: 100,   val2Default: 90,   showChannels: true  },
  margin:    { val1Label: 'Current Price',           val1Prefix: '$', val2Label: 'Target Price',           val2Prefix: '$', val2Unit: '',      val1Default: 100,   val2Default: 108,  showChannels: true  },
  inventory: { val1Label: 'Current Stock (Units)',   val1Prefix: '',  val2Label: 'Reorder Quantity',       val2Prefix: '',  val2Unit: 'units', val1Default: 50,    val2Default: 500,  showChannels: false },
  ads:       { val1Label: 'Current Budget ($/mo)',   val1Prefix: '$', val2Label: 'Target Budget ($/mo)',   val2Prefix: '$', val2Unit: '',      val1Default: 800,   val2Default: 2000, showChannels: true  },
  cash:      { val1Label: 'Invoice Amount ($)',      val1Prefix: '$', val2Label: 'Payment Extension',      val2Prefix: '',  val2Unit: 'days',  val1Default: 42000, val2Default: 15,   showChannels: false },
};

export const QUICK_PROMPTS_BY_TAB = {
  sales:     ['Maximize revenue', 'Increase conversion', 'Maintain margin', 'Beat competitors'],
  margin:    ['Recover CM2 target', 'Pass through COGS rise', 'Maximize gross margin', 'Protect contribution'],
  inventory: ['Eliminate OOS risk', 'Minimize capital tied up', 'Optimize reorder point', 'Protect buy box'],
  ads:       ['Maximize ROAS', 'Reduce ACoS', 'Scale ad volume', 'Lower CPC'],
  cash:      ['Maximize cash runway', 'Accelerate collections', 'Minimize interest cost', 'Optimize payment terms'],
};

export const AI_SUGGESTIONS_BY_TAB = {
  sales: {
    'Maximize revenue':    'Reducing your price by 8% to $92 is projected to increase weekly revenue by 32% through higher conversion rates. Consider launching on Walmart Marketplace simultaneously for an additional +18% reach boost.',
    'Increase conversion': 'A price point of $87 aligns with the sweet spot where conversion rate peaks at 4.1% in your category. Pair this with Amazon Sponsored Ads to capture high-intent buyers over the next 2 weeks.',
    'Maintain margin':     'To maintain your current margin while growing volume, target $95 (−5%) — this gives a projected +14% revenue uplift without eroding profitability. Avoid dropping below $88, which is the margin floor.',
    'Beat competitors':    'Your top competitor is currently at $94.99. Pricing at $92 undercuts by 3.1% while keeping healthy margins, projected to capture 12–18% of their market share over the next 4 weeks.',
  },
  margin: {
    'Recover CM2 target':      'Repricing the 18 affected Electronics SKUs by 9% restores CM2 to 28% and recovers an estimated $14,200 in monthly gross margin. Stagger the increase over 5 days to minimise buy box disruption.',
    'Pass through COGS rise':  'A 7.5% price increase across Electronics exactly passes through the 12% supplier cost increase while remaining within 3% of market leaders.',
    'Maximize gross margin':   'Dropping the 4 lowest-margin SKUs from Sponsored Products while raising prices 5% on the top 8 SKUs improves blended GM from 19.1% to 26.4% with minimal revenue impact.',
    'Protect contribution':    'Switching 3 high-fee FBA SKUs to FBM reduces fulfilment cost by 12% per unit, recovering 4.2% in CM3 contribution margin without a price change.',
  },
  inventory: {
    'Eliminate OOS risk':       'Ordering 500 units now gives 28 days of cover at current velocity (14 units/day). Place the PO today to eliminate stockout risk before the demand peak expected next week.',
    'Minimize capital tied up': 'A reorder of 300 units provides 17 days cover with $9,600 capital deployed — balancing OOS risk with cash efficiency given current 5.25% cost of capital.',
    'Optimize reorder point':   'Based on 18-day supplier lead time and 3-day safety stock requirement, the optimal reorder point is 294 units. Set this as an automated trigger in your inventory system.',
    'Protect buy box':          'Amazon requires a minimum 21-day stock cover to maintain Buy Box eligibility. Order 420 units to reach a 24-day buffer — 3 days of safety margin above the Amazon threshold.',
  },
  ads: {
    'Maximize ROAS':   'Reallocating $800 from broad match to exact match keywords on your top 5 converting terms is projected to lift ROAS from 2.8x to 4.1x while maintaining current revenue volume.',
    'Reduce ACoS':     'Pausing the 12 campaigns above 45% ACoS and consolidating into 4 focused campaigns would reduce blended ACoS from 44.6% to an estimated 26.2% within 2 weeks.',
    'Scale ad volume': 'Increasing TikTok budget by $1,200/month at current $0.18 CPC would generate +$22,000 incremental monthly revenue at an estimated 6.1x ROAS — your highest-performing channel.',
    'Lower CPC':       'Switching from broad to phrase match on your top 20 terms would reduce average CPC from $0.94 to an estimated $0.61 while retaining 85% of current impression volume.',
  },
  cash: {
    'Maximize cash runway':    'Negotiating a 15-day payment extension on the $52K Electronics PO frees $52K in operating cash, extending runway from 28 days to 45 days — above the 21-day minimum threshold.',
    'Accelerate collections':  'Offering a 1.5% early payment discount to your top 3 debtors could accelerate $31K in collections within 5 days. Net cost is $465 for $31K of immediate liquidity.',
    'Minimize interest cost':  'Taking the supplier\'s 2.5% early payment discount on the $42K invoice saves $1,050 immediately — an equivalent annualised return of 37.5% on capital deployed.',
    'Optimize payment terms':  'Extending terms from 30 to 45 days on Electronics POs reduces peak cash requirements by $52K. The incremental interest cost at 5.25% is only $220 per cycle.',
  },
};

/* ── Simulation execution steps ─────────────────────────────────────────── */
export const SIM_STEPS = [
  { label: 'Revenue impact analysis completed',   threshold: 40  },
  { label: 'Customer reach projection completed', threshold: 70  },
  { label: 'LTV Improvement calculating',         threshold: 100 },
];
