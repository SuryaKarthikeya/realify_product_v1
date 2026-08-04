import { DOMAIN_SEGMENTS, workspacePath } from '@/features/workspace/workspaceRoutes';

// ─── Static mock data for the Detailed View page ──────────────────────────────

/**
 * The five domain KPIs shown on every Dashboard View.
 *
 * Fixed by design: the cards are the navigation for this page, so they stay put
 * while clicking one swaps the charts and tables below. Values mirror the
 * Workspace domain cards, since both views report the same five metrics.
 */
export const DOMAIN_KPI_CARDS = [
  { domainKey: 'sales', title: 'Revenue', value: '$248.5K', change: '+14.2%', isPositive: true, subtext: 'Last 30 days' },
  { domainKey: 'margin', title: 'Margin', value: '42%', change: '+8.4%', isPositive: true, subtext: 'Last 30 days' },
  { domainKey: 'inventory', title: 'Inventory', value: '$1.82M', change: '+4.2%', isPositive: true, subtext: 'Last 30 days' },
  { domainKey: 'ads', title: 'Ads', value: '$24.8K', change: '+18.2%', isPositive: false, subtext: 'Last 30 days' },
  { domainKey: 'cash', title: 'Cash', value: '$284.6K', change: '+8.2%', isPositive: true, subtext: 'Last 30 days' },
];

/**
 * Per-domain detail metrics. No longer drives the KPI cards (those are fixed —
 * see DOMAIN_KPI_CARDS); kept for panels that want a domain's deeper readouts.
 */
export const STATS_DATA = {
  sales: [
    { title: 'Revenue', value: '$124,500', change: '12.4%', isPositive: true, domainKey: 'sales' },
    { title: 'Margin', value: '34.2%', change: '8.4%', isPositive: true, domainKey: 'margin' },
    { title: 'Inventory', value: '$85,400', change: '4.2%', isPositive: true, domainKey: 'inventory' },
    { title: 'Ads', value: '$14,200', change: '3.1%', isPositive: true, domainKey: 'ads' },
    { title: 'Cash', value: '$48,200', change: '6.8%', isPositive: true, domainKey: 'cash' },
    { title: 'ROAS', value: '4.2x', change: '+0.3x', isPositive: true },
    { title: 'Channel Mix', value: '3.8%', change: '-0.5%', isPositive: false },
    { title: 'Repeat Customers', value: '28%', change: '+4.8%', isPositive: true },
  ],
  margin: [
    { title: 'CM2 (Cross-Channel)', value: '$18,450', change: '+5.2%', isPositive: true },
    { title: 'CM%', value: '28.4%', change: '+2.1%', isPositive: true },
    { title: 'Unprofitable SKUs', value: '12', change: '-2', isPositive: true },
    { title: 'Pricing Opportunities', value: '27', change: '+$24.8K', isPositive: true },
    { title: 'CM2 (USD)', value: '$124,500', change: '+$12K', isPositive: true },
    { title: 'CM3 Channel', value: '12.4%', change: '-0.4%', isPositive: false },
    { title: 'CM3 Cross-Ch', value: '11.8%', change: '+1.2%', isPositive: true },
    { title: 'Gross Margin %', value: '42.3%', change: '1.4%', isPositive: true },
    { title: 'Contribution %', value: '19.4%', change: '+2.1%', isPositive: true },
  ],
  inventory: [
    { title: 'DOC (Avg)', value: '42 Days', change: '-3.2d', isPositive: true },
    { title: 'OOS Risk', value: '12', change: '+3', isPositive: false },
    { title: 'Overstock', value: '8', change: 'flat', isPositive: true },
    { title: 'In-Stock %', value: '94.2%', change: '+2.1%', isPositive: true },
    { title: 'Inbound POs', value: '5', change: '$42.4K', isPositive: true },
    { title: 'In-Stock % (health)', value: '94.2%', change: '+2.1%', isPositive: true },
    { title: 'Avg DOC (days)', value: '42', change: '-3.2', isPositive: true },
    { title: 'OOS Risk (14d)', value: '15', change: '+2', isPositive: false },
    { title: 'Overstock (DOC>180)', value: '8', change: '0', isPositive: true },
    { title: 'Inventory at Cost', value: '$1,800,000', change: '+8.2%', isPositive: true },
  ],
  ads: [
    { title: 'Total Ad Spend', value: '$124K', change: '+12.4%', isPositive: true, subtext: 'vs prior 30 days' },
    { title: 'ROAS', value: '4.8x', change: '+18.2%', isPositive: true, subtext: 'Blended average' },
    { title: 'Average CPC', value: '$2.34', change: '-8.5%', isPositive: true, subtext: 'Cost per click' },
    { title: 'Conversion Rate', value: '3.2%', change: '+0.8%', isPositive: true, subtext: 'Checkout success' },
    { title: 'Margin-Adj. ROAS', value: '4.1x', change: '-0.3x', isPositive: false, subtext: 'Profitability-aware' },
    { title: 'TACOS', value: '14.2%', change: '+0.8%', isPositive: false, subtext: 'Ad spend / Total Rev' },
    { title: 'TMCOS', value: '19.2%', change: '+1.2%', isPositive: false, subtext: 'Ad spend / Total CM' },
    { title: 'Wasted Spend', value: '$4.8K', change: '+12%', isPositive: false, subtext: 'Low ROAS spend' },
  ],
  cash: [
    { title: 'Cash on Hand', value: '$284.6K', change: '+8.2%', isPositive: true, subtext: 'Working capital' },
    { title: 'Cash In (30d)', value: '$196.4K', change: '+11.4%', isPositive: true, subtext: 'Settlements received' },
    { title: 'Cash Out (30d)', value: '$168.2K', change: '+6.1%', isPositive: false, subtext: 'Supplier & opex' },
    { title: 'Net Cash Flow', value: '$28.2K', change: '+18.4%', isPositive: true, subtext: 'In minus out' },
    { title: 'Runway', value: '94 days', change: '+9d', isPositive: true, subtext: 'At current burn' },
    { title: 'Cash Conversion', value: '38 days', change: '-4d', isPositive: true, subtext: 'Order to cash' },
    { title: 'Locked in Stock', value: '$1.82M', change: '+4.2%', isPositive: false, subtext: 'Inventory at cost' },
    { title: 'Pending Payouts', value: '$42.8K', change: '+2.4%', isPositive: true, subtext: 'Awaiting settlement' },
  ],
};

export const PRODUCT_HEATMAP_DATA = [
  { name: 'Smart Hub Pro', abbr: 'SHP', category: 'Electronics', size: 24800, change: 12.4, revenue: '$24,800', margin: '32.1%', units: 412, roas: '4.8x', doc: 28, adSpend: '$850', cashFlow: '+$6.2K' },
  { name: 'LED Strip 5m', abbr: 'LS5', category: 'Electronics', size: 18600, change: 8.2, revenue: '$18,600', margin: '28.4%', units: 820, roas: '3.9x', doc: 45, adSpend: '$620', cashFlow: '+$4.8K' },
  { name: 'Wireless Charger', abbr: 'WCH', category: 'Electronics', size: 15200, change: -3.1, revenue: '$15,200', margin: '24.8%', units: 304, roas: '2.8x', doc: 62, adSpend: '$540', cashFlow: '+$2.1K' },
  { name: 'Smart Plug 4-Pack', abbr: 'SP4', category: 'Electronics', size: 12400, change: 5.7, revenue: '$12,400', margin: '38.2%', units: 248, roas: '5.2x', doc: 34, adSpend: '$310', cashFlow: '+$3.8K' },
  { name: 'Air Purifier XL', abbr: 'APX', category: 'Home & Garden', size: 11800, change: -8.4, revenue: '$11,800', margin: '18.6%', units: 98, roas: '2.1x', doc: 88, adSpend: '$760', cashFlow: '-$0.4K' },
  { name: 'Bamboo Organizer', abbr: 'BOG', category: 'Home & Garden', size: 9800, change: 18.2, revenue: '$9,800', margin: '42.4%', units: 490, roas: '6.1x', doc: 22, adSpend: '$180', cashFlow: '+$3.2K' },
  { name: 'Yoga Mat Pro', abbr: 'YMP', category: 'Apparel', size: 8400, change: 22.8, revenue: '$8,400', margin: '45.8%', units: 280, roas: '7.2x', doc: 18, adSpend: '$140', cashFlow: '+$2.8K' },
  { name: 'Plant Grow Light', abbr: 'PGL', category: 'Home & Garden', size: 7600, change: 0.3, revenue: '$7,600', margin: '29.4%', units: 152, roas: '3.4x', doc: 52, adSpend: '$290', cashFlow: '+$1.4K' },
  { name: 'Stainless Tumbler', abbr: 'STT', category: 'Apparel', size: 6900, change: -12.8, revenue: '$6,900', margin: '22.1%', units: 345, roas: '2.3x', doc: 95, adSpend: '$420', cashFlow: '-$0.8K' },
  { name: 'Resistance Bands', abbr: 'RBX', category: 'Apparel', size: 6200, change: 15.6, revenue: '$6,200', margin: '48.2%', units: 620, roas: '8.4x', doc: 15, adSpend: '$90', cashFlow: '+$2.2K' },
  { name: 'Smart Scale BT', abbr: 'SSB', category: 'Electronics', size: 5800, change: 4.1, revenue: '$5,800', margin: '31.8%', units: 116, roas: '4.1x', doc: 38, adSpend: '$210', cashFlow: '+$1.1K' },
  { name: 'Cat Tree Deluxe', abbr: 'CTD', category: 'Pet Suppliers', size: 5400, change: -5.8, revenue: '$5,400', margin: '26.4%', units: 60, roas: '2.6x', doc: 74, adSpend: '$280', cashFlow: '+$0.6K' },
  { name: 'Foam Roller Set', abbr: 'FRS', category: 'Apparel', size: 4900, change: 9.4, revenue: '$4,900', margin: '44.2%', units: 245, roas: '6.8x', doc: 24, adSpend: '$100', cashFlow: '+$1.6K' },
  { name: 'Cabinet Organizer', abbr: 'COG', category: 'Home & Garden', size: 4400, change: 7.2, revenue: '$4,400', margin: '36.8%', units: 220, roas: '5.6x', doc: 30, adSpend: '$120', cashFlow: '+$1.2K' },
  { name: 'Pet Water Fountain', abbr: 'PWF', category: 'Pet Suppliers', size: 3800, change: 28.4, revenue: '$3,800', margin: '52.4%', units: 190, roas: '9.2x', doc: 12, adSpend: '$60', cashFlow: '+$1.4K' },
  { name: 'Aromatherapy Diffuser', abbr: 'ARD', category: 'Home & Garden', size: 3200, change: -18.2, revenue: '$3,200', margin: '14.8%', units: 128, roas: '1.8x', doc: 112, adSpend: '$390', cashFlow: '-$1.2K' },
  { name: 'Luggage Lock Set', abbr: 'LLS', category: 'Apparel', size: 2800, change: 2.1, revenue: '$2,800', margin: '38.4%', units: 280, roas: '5.1x', doc: 42, adSpend: '$75', cashFlow: '+$0.8K' },
  { name: 'Phone Holder Car', abbr: 'PHC', category: 'Electronics', size: 2400, change: 6.8, revenue: '$2,400', margin: '40.2%', units: 240, roas: '5.8x', doc: 28, adSpend: '$65', cashFlow: '+$0.7K' },
  { name: 'Dog Chew Toy Pack', abbr: 'DCT', category: 'Pet Suppliers', size: 2100, change: 11.4, revenue: '$2,100', margin: '58.2%', units: 420, roas: '10.4x', doc: 10, adSpend: '$30', cashFlow: '+$0.9K' },
];

export const WORKSPACE_METRIC = {
  sales: { label: 'Revenue', valueKey: 'revenue', secondary: 'units', secondaryLabel: 'Units' },
  margin: { label: 'Revenue', valueKey: 'revenue', secondary: 'margin', secondaryLabel: 'Margin' },
  inventory: { label: 'Revenue', valueKey: 'revenue', secondary: 'doc', secondaryLabel: 'DOC (days)' },
  ads: { label: 'Revenue', valueKey: 'revenue', secondary: 'roas', secondaryLabel: 'ROAS' },
  cash: { label: 'Revenue', valueKey: 'revenue', secondary: 'cashFlow', secondaryLabel: 'Cash Flow' },
};

export const PAGE_TITLES = { sales: 'Sales', margin: 'Margin', inventory: 'Inventory', ads: 'Ads', cash: 'Cash' };
export const BACK_ROUTES = Object.fromEntries(
  Object.keys(DOMAIN_SEGMENTS).map((domain) => [domain, workspacePath(domain)])
);

export const CHANNEL_MIX_DATA = [
  { label: 'Online Store', pct: 1.0, amount: '$124,400', color: '#0A52E7', dot: 'bg-blue-600', bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-900/50' },
];

export const DASHBOARD_VIEW_TABS = [
  { key: 'sales', label: 'Revenue', icon: 'fa-dollar-sign' },
  { key: 'margin', label: 'Margin', icon: 'fa-chart-line' },
  { key: 'inventory', label: 'Inventory', icon: 'fa-boxes' },
  { key: 'ads', label: 'Ads', icon: 'fa-bullhorn' },
  { key: 'cash', label: 'Cash', icon: 'fa-money-bill-wave' },
];

// ─── Filter option arrays — never change, defined once at module level ────────

// ─── Sales tab data ─────────────────────────────────────────────────────────────

// ─── Ads tab data ────────────────────────────────────────────────────────────────

// ─── Inventory tab data ──────────────────────────────────────────────────────────

