/**
 * The product watchlist. Consumed by Workspace and by the Product View page,
 * so it is app-level data rather than Revenue-domain data.
 */
export const salesWatchlistItems = [
  {
    title: 'Premium Wireless Headphones',
    sku: 'WH-PRO-2024',
    stock: '47',
    velocity: '23/day',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/829ed95905-98415edd6aab0bba6e05.png',
    status: 'LOW',
    statusColor: 'bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 border-red-200 dark:border-red-900/50',
    progress: 28,
    progressColor: 'bg-red-500',
    subtext: '2 days until stockout'
  },
  {
    title: 'Smart Home Security Camera',
    sku: 'CAM-SEC-5000',
    stock: '342',
    velocity: '+287%',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/a92a4ffb64-d9b6565e03e56b627c33.png',
    status: 'HOT',
    statusColor: 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-900/50',
    progress: 95,
    progressColor: 'bg-green-500',
    subtext: 'Trending on social media'
  },
  {
    title: 'Organic Pet Food 15lb',
    sku: 'PF-ORG-15LB',
    stock: '218',
    velocity: '14/day',
    image: null,
    status: 'HOT',
    statusColor: 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-900/50',
    progress: 72,
    progressColor: 'bg-green-500',
    subtext: 'Strong seasonal demand'
  },
  {
    title: 'Ergonomic Office Chair Pro',
    sku: 'CH-ERGO-PRO',
    stock: '63',
    velocity: '8/day',
    image: null,
    status: 'LOW',
    statusColor: 'bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-950/20 dark:to-amber-950/20 border-yellow-200 dark:border-yellow-900/50',
    progress: 35,
    progressColor: 'bg-yellow-500',
    subtext: '8 days of stock remaining'
  },
  {
    title: 'USB-C Hub 7-in-1',
    sku: 'HUB-USBC-7IN1',
    stock: '524',
    velocity: '31/day',
    image: null,
    status: 'HOT',
    statusColor: 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-900/50',
    progress: 88,
    progressColor: 'bg-green-500',
    subtext: 'Top seller this week'
  },
];
