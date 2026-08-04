/**
 * Margin waterfall: how revenue becomes net profit, one stage at a time.
 *
 * `kind: 'total'` bars are running subtotals and are drawn from zero; `kind:
 * 'deduction'` bars float between the subtotal before and after them. The
 * deduction amounts are what make the totals add up, so they are the source of
 * truth — the subtotals below are the cumulative result and are asserted by the
 * unit-less check in `buildWaterfall`.
 */
export const MARGIN_WATERFALL_STAGES = [
  {
    key: 'revenue',
    label: 'Revenue',
    kind: 'total',
    amount: 75100,
    note: 'Gross booked revenue across Amazon, Shopify and Walmart.',
    contributors: [
      { label: 'Amazon', value: 41300, share: '55%' },
      { label: 'Shopify', value: 22500, share: '30%' },
      { label: 'Walmart', value: 11300, share: '15%' },
    ],
  },
  {
    key: 'cogs',
    label: 'COGS',
    kind: 'deduction',
    amount: -29300,
    note: 'Landed product cost on units sold.',
    contributors: [
      // All five catalogue categories, summing to the -29,300 COGS total above.
      { label: 'Electronics', value: -11700, share: '40%' },
      { label: 'Furniture', value: -7300, share: '25%' },
      { label: 'Home & Garden', value: -5900, share: '20%' },
      { label: 'Apparel', value: -2900, share: '10%' },
      { label: 'Pet Supplies', value: -1500, share: '5%' },
    ],
  },
  {
    key: 'gross-profit',
    label: 'Gross Profit',
    kind: 'total',
    note: 'Revenue less landed product cost.',
    contributors: [
      { label: 'Gross margin %', value: null, share: '61.0%' },
      { label: 'Best category — Apparel', value: null, share: '68.4%' },
      { label: 'Worst category — Electronics', value: null, share: '54.1%' },
    ],
  },
  {
    key: 'fees',
    label: 'Fees',
    kind: 'deduction',
    amount: -9840,
    note: 'Marketplace referral, FBA and payment processing fees.',
    contributors: [
      { label: 'Amazon referral', value: -4900, share: '50%' },
      { label: 'FBA fulfilment', value: -3100, share: '32%' },
      { label: 'Payment processing', value: -1840, share: '18%' },
    ],
  },
  {
    key: 'ads',
    label: 'Ads',
    kind: 'deduction',
    amount: -6150,
    note: 'Paid media across all platforms.',
    contributors: [
      { label: 'Amazon Ads', value: -3900, share: '63%' },
      { label: 'Google Ads', value: -1400, share: '23%' },
      { label: 'Meta Ads', value: -850, share: '14%' },
    ],
  },
  {
    key: 'discounts',
    label: 'Discounts',
    kind: 'deduction',
    amount: -1420,
    note: 'Promotions, coupons and outlet pricing.',
    contributors: [
      { label: 'Outlet promo', value: -780, share: '55%' },
      { label: 'Coupons', value: -420, share: '30%' },
      { label: 'Bundle discount', value: -220, share: '15%' },
    ],
  },
  {
    key: 'shipping',
    label: 'Shipping',
    kind: 'deduction',
    amount: -1050,
    note: 'Outbound shipping not recovered from the customer.',
    contributors: [
      { label: 'Self-fulfilled', value: -620, share: '59%' },
      { label: 'MCF', value: -430, share: '41%' },
    ],
  },
  {
    key: 'returns',
    label: 'Returns',
    kind: 'deduction',
    amount: -860,
    note: 'Refunded value plus non-resellable units.',
    contributors: [
      { label: 'Non-resellable', value: -510, share: '59%' },
      { label: 'Return shipping', value: -350, share: '41%' },
    ],
  },
  {
    key: 'cm2',
    label: 'CM2',
    kind: 'total',
    note: 'Contribution after all variable selling costs.',
    contributors: [
      { label: 'CM2 margin %', value: null, share: '35.3%' },
      { label: 'SKUs above CM2 target', value: null, share: '68%' },
      { label: 'SKUs below CM2 floor', value: null, share: '12' },
    ],
  },
  {
    key: 'storage',
    label: 'Storage',
    kind: 'deduction',
    amount: -1640,
    note: 'Warehouse and FBA storage, including long-term fees.',
    contributors: [
      { label: 'FBA monthly storage', value: -980, share: '60%' },
      { label: 'Long-term storage', value: -410, share: '25%' },
      { label: '3PL storage', value: -250, share: '15%' },
    ],
  },
  {
    key: 'cm3',
    label: 'CM3',
    kind: 'total',
    note: 'Contribution after storage and holding costs.',
    contributors: [
      { label: 'CM3 margin %', value: null, share: '33.1%' },
      { label: 'Storage as % of revenue', value: null, share: '2.2%' },
      { label: 'Overstock SKUs driving cost', value: null, share: '8' },
    ],
  },
  {
    key: 'fixed-costs',
    label: 'Fixed Costs',
    kind: 'deduction',
    amount: -6220,
    note: 'Salaries, software and overhead allocated to this period.',
    contributors: [
      { label: 'Team', value: -3800, share: '61%' },
      { label: 'Software & tools', value: -1520, share: '24%' },
      { label: 'Overhead', value: -900, share: '15%' },
    ],
  },
  {
    key: 'net-profit',
    label: 'Net Profit',
    kind: 'net',
    note: 'What is left after every cost above.',
    contributors: [
      { label: 'Net margin %', value: null, share: '24.8%' },
      { label: 'vs prior 30 days', value: null, share: '+3.1 pts' },
      { label: 'Net profit per order', value: null, share: '$37.24' },
    ],
  },
];

/**
 * Resolves each stage into the geometry a waterfall needs: the value it reports,
 * and the bar's `base`/`top` on the value axis.
 *
 * Subtotal stages take their value from the running total rather than carrying a
 * duplicate number that could drift out of step with the deductions.
 */
export const buildWaterfall = (stages = MARGIN_WATERFALL_STAGES) => {
  let running = 0;

  const bars = stages.map((stage) => {
    if (stage.kind === 'deduction') {
      const top = running;
      running += stage.amount;          // amount is negative
      return { ...stage, value: stage.amount, base: running, top };
    }
    // Revenue seeds the running total; every later subtotal reports it.
    running = stage.key === 'revenue' ? stage.amount : running;
    return { ...stage, value: running, base: 0, top: running };
  });

  return { bars, max: Math.max(...bars.map((b) => b.top)), net: running };
};
