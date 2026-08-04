/** Static stats, trend series and badge styling for the Product View page. */

export const PERF_STATS = [
  { key: 'revenue', label: 'Revenue', icon: 'fa-arrow-trend-up', value: '$14,250', change: '+12.4%', isPositive: true, sub: 'vs previous 7 days', color: '#6366f1' },
  { key: 'units', label: 'Units Sold', icon: 'fa-cart-shopping', value: '215', change: '+8.7%', isPositive: true, sub: 'vs previous 7 days', color: '#3b82f6' },
  { key: 'conversion', label: 'Conversion Rate', icon: 'fa-percent', value: '3.2%', change: '+0.6pp', isPositive: true, sub: 'vs previous 7 days', color: '#10b981' },
  { key: 'buybox', label: 'Buy Box %', icon: 'fa-trophy', value: '87.4%', change: '-2.1%', isPositive: false, sub: 'vs previous 7 days', color: '#f59e0b' },
];

export const TREND_DATA = {
  revenue: [9800, 11200, 12400, 15200, 13600, 13100, 14250].map((v, i) => ({ date: `May ${14 + i}`, value: v })),
  units: [168, 192, 198, 245, 227, 219, 215].map((v, i) => ({ date: `May ${14 + i}`, value: v })),
  conversion: [2.6, 2.9, 3.1, 3.5, 3.2, 3.1, 3.2].map((v, i) => ({ date: `May ${14 + i}`, value: v })),
  buybox: [92, 91, 89, 88, 87, 88, 87.4].map((v, i) => ({ date: `May ${14 + i}`, value: v })),
};

export const ACTION_BADGE = {
  'CRITICAL': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
  'HIGH': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
  'OPPORTUNITY': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  'INSIGHT': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  'MARKET': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
};


export const defaultDescription = (name) =>
  `${name} is one of your top-performing products, consistently driving strong revenue across channels. It maintains competitive pricing and healthy margin contribution relative to your catalog average. Recent demand signals indicate sustained buyer interest, with particular strength in repeat purchase behaviour. Monitor inventory velocity closely to avoid stockout risk during high-demand periods.`;
