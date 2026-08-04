/** Revenue series rendered by the Dashboard View tables. */

export const salesTopMovers = [
  { name: 'Premium Wireless Headphones', sku: 'B09XYZ1234', revenue: '$124,500', change: '+34.2%' },
  { name: 'Smart Home Security Camera', sku: 'B09ABC5678', revenue: '$98,700', change: '+28.1%' },
  { name: 'Organic Pet Food 15lb', sku: 'B09DEF9012', revenue: '$76,340', change: '+22.5%' },
  { name: 'Ergonomic Office Chair Pro', sku: 'B09GHI3456', revenue: '$68,900', change: '+19.8%' },
  { name: 'USB-C Hub 7-in-1', sku: 'B09JKL7890', revenue: '$54,120', change: '+15.3%' },
];

export const salesBottomMovers = [
  { name: 'Portable Charger X 20000mAh', sku: 'B09MNO1234', revenue: '$8,420', change: '-42.1%' },
  { name: 'Bamboo Cutting Board Set', sku: 'B09PQR5678', revenue: '$5,670', change: '-38.7%' },
  { name: 'Yoga Mat Eco Premium', sku: 'B09STU9012', revenue: '$4,230', change: '-31.4%' },
  { name: 'LED Desk Lamp Smart', sku: 'B09VWX3456', revenue: '$3,890', change: '-28.9%' },
  { name: 'Kitchen Timer Digital 3-Pack', sku: 'B09YZA7890', revenue: '$2,140', change: '-25.3%' },
];

export const salesRevenueData = [
  { sku: 'SKU-001', name: 'Smart Home Security Camera', channel: 'Amazon', units: 312, price: '$89.99', revenue: '$28,077', returns: 18, net: '$26,457' },
  { sku: 'SKU-002', name: 'Wireless Earbuds Pro', channel: 'Shopify', units: 284, price: '$79.99', revenue: '$22,717', returns: 9, net: '$21,997' },
  { sku: 'SKU-004', name: 'Yoga Mat Premium', channel: 'Amazon', units: 198, price: '$54.99', revenue: '$10,888', returns: 12, net: '$10,228' },
  { sku: 'SKU-005', name: 'Organic Pet Food 15lb', channel: 'TikTok', units: 420, price: '$42.99', revenue: '$18,056', returns: 5, net: '$17,841' },
  { sku: 'SKU-008', name: 'Bamboo Cutting Board Set', channel: 'Google', units: 246, price: '$34.99', revenue: '$8,607', returns: 0, net: '$8,607' },
  { sku: 'SKU-009', name: 'Running Shoes Pro', channel: 'Amazon', units: 168, price: '$124.99', revenue: '$20,999', returns: 21, net: '$18,374' },
  { sku: 'SKU-006', name: 'Desk Organizer Premium', channel: 'Amazon', units: 145, price: '$32.99', revenue: '$4,784', returns: 4, net: '$4,652' },
  { sku: 'SKU-007', name: 'Ergonomic Chair Cushion', channel: 'Shopify', units: 204, price: '$52.00', revenue: '$10,608', returns: 7, net: '$10,244' },
  { sku: 'SKU-003', name: 'Stainless Water Bottle', channel: 'eBay', units: 156, price: '$18.99', revenue: '$2,962', returns: 3, net: '$2,905' },
  { sku: 'SKU-010', name: 'Portable Bluetooth Speaker', channel: 'Amazon', units: 47, price: '$89.99', revenue: '$4,230', returns: 2, net: '$4,050' },
];

export const salesUnitsData = [
  { sku: 'SKU-005', name: 'Organic Pet Food 15lb', amazon: 180, shopify: 80, tiktok: 160, ebay: 0, google: 0, total: 420 },
  { sku: 'SKU-001', name: 'Smart Home Security Camera', amazon: 280, shopify: 0, tiktok: 0, ebay: 32, google: 0, total: 312 },
  { sku: 'SKU-002', name: 'Wireless Earbuds Pro', amazon: 0, shopify: 220, tiktok: 0, ebay: 64, google: 0, total: 284 },
  { sku: 'SKU-008', name: 'Bamboo Cutting Board Set', amazon: 0, shopify: 40, tiktok: 0, ebay: 0, google: 206, total: 246 },
  { sku: 'SKU-007', name: 'Ergonomic Chair Cushion', amazon: 80, shopify: 124, tiktok: 0, ebay: 0, google: 0, total: 204 },
  { sku: 'SKU-004', name: 'Yoga Mat Premium', amazon: 160, shopify: 0, tiktok: 38, ebay: 0, google: 0, total: 198 },
  { sku: 'SKU-009', name: 'Running Shoes Pro', amazon: 168, shopify: 0, tiktok: 0, ebay: 0, google: 0, total: 168 },
  { sku: 'SKU-003', name: 'Stainless Water Bottle', amazon: 60, shopify: 0, tiktok: 0, ebay: 96, google: 0, total: 156 },
  { sku: 'SKU-006', name: 'Desk Organizer Premium', amazon: 145, shopify: 0, tiktok: 0, ebay: 0, google: 0, total: 145 },
  { sku: 'SKU-010', name: 'Portable Bluetooth Speaker', amazon: 47, shopify: 0, tiktok: 0, ebay: 0, google: 0, total: 47 },
];

export const salesOrdersData = [
  { channel: 'Amazon', orders: 198, units: 1238, aov: '$302', revenue: '$59,796', pct: '48.1%' },
  { channel: 'Shopify', orders: 86, units: 464, aov: '$298', revenue: '$25,628', pct: '20.6%' },
  { channel: 'TikTok Shop', orders: 62, units: 198, aov: '$291', revenue: '$18,042', pct: '14.5%' },
  { channel: 'eBay', orders: 42, units: 192, aov: '$273', revenue: '$11,466', pct: '9.2%' },
  { channel: 'Google Shopping', orders: 24, units: 206, aov: '$359', revenue: '$8,616', pct: '6.9%' },
  { channel: 'Walmart', orders: 0, units: 0, aov: '—', revenue: '—', pct: '0%' },
];

export const salesAovData = [
  { sku: 'SKU-009', name: 'Running Shoes Pro', price: '$124.99', orders: 168, aov: '$124.99', vsAvg: '+$23', pctVsAvg: '+22.6%', positive: true },
  { sku: 'SKU-001', name: 'Smart Home Security Camera', price: '$89.99', orders: 312, aov: '$89.99', vsAvg: '-$12', pctVsAvg: '-11.8%', positive: false },
  { sku: 'SKU-010', name: 'Portable Bluetooth Speaker', price: '$89.99', orders: 47, aov: '$89.99', vsAvg: '-$12', pctVsAvg: '-11.8%', positive: false },
  { sku: 'SKU-002', name: 'Wireless Earbuds Pro', price: '$79.99', orders: 284, aov: '$79.99', vsAvg: '-$22', pctVsAvg: '-21.6%', positive: false },
  { sku: 'SKU-007', name: 'Ergonomic Chair Cushion', price: '$52.00', orders: 204, aov: '$52.00', vsAvg: '-$50', pctVsAvg: '-49.0%', positive: false },
  { sku: 'SKU-004', name: 'Yoga Mat Premium', price: '$54.99', orders: 198, aov: '$54.99', vsAvg: '-$47', pctVsAvg: '-46.1%', positive: false },
  { sku: 'SKU-005', name: 'Organic Pet Food 15lb', price: '$42.99', orders: 420, aov: '$42.99', vsAvg: '-$59', pctVsAvg: '-57.8%', positive: false },
  { sku: 'SKU-006', name: 'Desk Organizer Premium', price: '$32.99', orders: 145, aov: '$32.99', vsAvg: '-$69', pctVsAvg: '-67.7%', positive: false },
  { sku: 'SKU-008', name: 'Bamboo Cutting Board Set', price: '$34.99', orders: 246, aov: '$34.99', vsAvg: '-$67', pctVsAvg: '-65.7%', positive: false },
  { sku: 'SKU-003', name: 'Stainless Water Bottle', price: '$18.99', orders: 156, aov: '$18.99', vsAvg: '-$83', pctVsAvg: '-81.4%', positive: false },
];

export const CHAN_STYLE = {
  Amazon: { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-700 dark:text-orange-400' },
  Shopify: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-400' },
  TikTok: { bg: 'bg-slate-100 dark:bg-slate-700', text: 'text-slate-700 dark:text-slate-300' },
  Google: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400' },
  eBay: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400' },
};

export const SPARKLINE_DATA = [
  [20, 25, 18, 30, 24, 35, 28], [30, 28, 22, 25, 20, 18, 15], [18, 22, 26, 20, 28, 24, 32],
  [28, 22, 30, 18, 26, 20, 24], [14, 20, 25, 18, 30, 26, 34], [34, 28, 22, 30, 20, 24, 18],
  [20, 22, 24, 26, 28, 30, 32], [32, 28, 24, 20, 22, 18, 16], [20, 30, 16, 28, 22, 32, 25], [25, 18, 28, 20, 14, 22, 18],
];

export const CARD_COLORS = ['bg-violet-50', 'bg-sky-50', 'bg-emerald-50', 'bg-amber-50', 'bg-rose-50', 'bg-indigo-50', 'bg-teal-50', 'bg-orange-50', 'bg-cyan-50', 'bg-pink-50'];
