/** Catalogue fixtures and table configuration for the Products page. */

export const CHANNEL_TABS = ['Amazon', 'Shopify', 'Walmart'];

export const ALL_PRODUCTS = [
  { id: 1, name: 'Premium Wireless Headphones', sku: 'WH-PRO-2024', status: 'Active', price: '$149', cogs: '$80', margin: '46.3%', returns: '2.1%', bb: '98%', salesTrend: 'up', category: 'Electronics', inventory: 47, velocity: '23/day', workspaceLabel: 'Price Drop Alert', workspaceColor: 'text-red-600 dark:text-red-400', createdAt: new Date('2024-01-15'), updatedAt: new Date('2026-06-10') },
  { id: 2, name: 'Security Camera', sku: 'SC-HOME-V2', status: 'Active', price: '$89', cogs: '$40', margin: '55.1%', returns: '1.2%', bb: '95%', salesTrend: 'up', category: 'Electronics', inventory: 12, velocity: '8/day', workspaceLabel: 'Stockout Risk', workspaceColor: 'text-red-600 dark:text-red-400', createdAt: new Date('2024-03-02'), updatedAt: new Date('2026-06-15') },
  { id: 3, name: 'Essential T-Shirt', sku: 'AP-TEE-001', status: 'Active', price: '$24', cogs: '$10', margin: '58.3%', returns: '5.4%', bb: '99%', salesTrend: 'down', category: 'Apparel', inventory: 452, velocity: '112/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2023-11-08'), updatedAt: new Date('2026-05-20') },
  { id: 4, name: 'Minimalist Watch', sku: 'WT-MIN-04', status: 'Active', price: '$199', cogs: '$60', margin: '69.8%', returns: '0.8%', bb: '100%', salesTrend: 'up', category: 'Apparel', inventory: 5, velocity: '4/day', workspaceLabel: 'Competitor Move', workspaceColor: 'text-orange-600 dark:text-orange-400', createdAt: new Date('2024-06-20'), updatedAt: new Date('2026-06-16') },
  { id: 5, name: 'Organic Pet Food 15lb', sku: 'PF-ORG-15LB', status: 'Active', price: '$44', cogs: '$25', margin: '43.2%', returns: '0.5%', bb: '92%', salesTrend: 'up', category: 'Pet', inventory: 218, velocity: '14/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2023-09-14'), updatedAt: new Date('2026-04-30') },
  { id: 6, name: 'Smart Speaker Mini', sku: 'SM-SPK-003', status: 'Active', price: '$69', cogs: '$35', margin: '49.3%', returns: '3.2%', bb: '88%', salesTrend: 'up', category: 'Electronics', inventory: 89, velocity: '6/day', workspaceLabel: 'Opportunity', workspaceColor: 'text-green-600 dark:text-green-400', createdAt: new Date('2024-02-28'), updatedAt: new Date('2026-06-01') },
  { id: 7, name: 'Ergonomic Office Chair', sku: 'FN-CHR-001', status: 'Active', price: '$349', cogs: '$150', margin: '57.0%', returns: '4.1%', bb: '90%', salesTrend: 'down', category: 'Furniture', inventory: 34, velocity: '3/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2023-07-11'), updatedAt: new Date('2026-03-18') },
  { id: 8, name: 'USB-C Hub 7-in-1', sku: 'TEC-USB-007', status: 'Active', price: '$49', cogs: '$15', margin: '69.4%', returns: '1.8%', bb: '96%', salesTrend: 'up', category: 'Electronics', inventory: 156, velocity: '18/day', workspaceLabel: 'Opportunity', workspaceColor: 'text-green-600 dark:text-green-400', createdAt: new Date('2024-04-05'), updatedAt: new Date('2026-06-14') },
  { id: 9, name: 'Wireless Earbuds Pro', sku: 'AUD-EAR-PRO', status: 'Active', price: '$129', cogs: '$40', margin: '69.0%', returns: '6.2%', bb: '85%', salesTrend: 'down', category: 'Electronics', inventory: 203, velocity: '8/day', workspaceLabel: 'Price Drop Alert', workspaceColor: 'text-red-600 dark:text-red-400', createdAt: new Date('2024-05-19'), updatedAt: new Date('2026-06-17') },
  { id: 10, name: 'Yoga Mat Premium', sku: 'FT-YOG-002', status: 'Active', price: '$59', cogs: '$12', margin: '79.7%', returns: '0.9%', bb: '99%', salesTrend: 'up', category: 'Fitness', inventory: 78, velocity: '5/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2023-12-22'), updatedAt: new Date('2026-02-09') },
  { id: 11, name: 'Bamboo Phone Stand', sku: 'ACC-STD-012', status: 'Active', price: '$19', cogs: '$4', margin: '78.9%', returns: '0.2%', bb: '100%', salesTrend: 'up', category: 'Accessories', inventory: 310, velocity: '22/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2024-07-30'), updatedAt: new Date('2026-05-05') },
  { id: 12, name: 'Autofy 100% Waterproof (Tested) Bike Cover ...', sku: 'VKAMCOVER0072', status: 'Active', price: '$451', cogs: '$247', margin: '10.1%', returns: '0.1%', bb: '98%', salesTrend: 'up', category: 'Automotive', inventory: 1138, velocity: '1138', workspaceLabel: 'Listing Suppressed', workspaceColor: 'text-red-600 dark:text-red-400', createdAt: new Date('2023-05-03'), updatedAt: new Date('2025-11-27') },
  { id: 13, name: 'Autofy 100% Waterproof (Tested) Scooter Bik...', sku: 'VKAMCOVER0071', status: 'Active', price: '$426', cogs: '$247', margin: '15.7%', returns: '0.1%', bb: '98%', salesTrend: 'up', category: 'Automotive', inventory: 928, velocity: '928', workspaceLabel: 'Overstock', workspaceColor: 'text-amber-600 dark:text-amber-400', createdAt: new Date('2024-08-12'), updatedAt: new Date('2026-06-12') },
  { id: 14, name: 'Ergonomic Desk Organizer', sku: 'HOME-ORG-006', status: 'Active', price: '$34', cogs: '$15', margin: '55.9%', returns: '1.5%', bb: '94%', salesTrend: 'up', category: 'Home', inventory: 22, velocity: '9/day', workspaceLabel: 'Stockout Risk', workspaceColor: 'text-red-600 dark:text-red-400', createdAt: new Date('2024-09-25'), updatedAt: new Date('2026-06-13') },
  { id: 15, name: 'Cotton Tote Bag', sku: 'APP-TOT-003', status: 'Draft', price: '$14', cogs: '$4', margin: '71.4%', returns: '2.8%', bb: '91%', salesTrend: 'down', category: 'Apparel', inventory: 640, velocity: '28/day', workspaceLabel: 'Stable', workspaceColor: 'text-gray-500 dark:text-slate-400', createdAt: new Date('2023-10-17'), updatedAt: new Date('2026-04-22') },
];

/**
 * The per-SKU fields the catalogue counts as "filled", mirroring the backend's
 * completeness read (realify-mc `routers/skus.py::_COMPLETENESS`) so "x/7 fields
 * filled" means the same thing on both sides.
 */
export const COMPLETENESS_FIELDS = ['price', 'cogs', 'margin', 'returns', 'bb', 'inventory', 'velocity'];

const isFilled = (value) => value !== null && value !== undefined && value !== '';

/**
 * The counts in the Product Catalog header, derived from the rows the page is
 * actually rendering.
 *
 * Deliberately computed rather than written down: a fixed SKU count in the
 * header is read as a live figure, and it silently disagrees with the table the
 * moment either one changes.
 */
export const catalogSummary = (products = []) => {
  const skus = products.length;
  const filled = products.reduce(
    (sum, product) => sum + COMPLETENESS_FIELDS.filter((field) => isFilled(product[field])).length,
    0
  );
  return {
    skus,
    fieldsPerSku: COMPLETENESS_FIELDS.length,
    avgFilled: skus ? Math.round((filled / skus) * 10) / 10 : 0,
    missingCogs: products.filter((product) => !isFilled(product.cogs)).length,
  };
};

export const PAGE_SIZE = 10;
export const CATEGORIES = ['All', 'Electronics', 'Apparel', 'Pet', 'Fitness', 'Furniture', 'Home', 'Accessories'];

export const SORT_OPTIONS = [
  { key: 'name', label: 'Product Name' },
  { key: 'category', label: 'Category' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'velocity', label: 'Velocity' },
  { key: 'intel', label: 'Intel' },
];

export const DEFAULT_COLS = [
  { key: 'status', label: 'Status', visible: true },
  { key: 'price', label: 'Price', visible: true },
  { key: 'category', label: 'Category', visible: true },
  { key: 'inventory', label: 'Inventory', visible: true },
  { key: 'velocity', label: 'Velocity', visible: true },
];

export const STATUS_OPTIONS = ['Active', 'Archived', 'Draft', 'Unlisted'];
export const STATUS_STYLES = {
  Active: { pill: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', dot: 'bg-green-500' },
  Draft: { pill: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400', dot: 'bg-amber-400' },
  Archived: { pill: 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400', dot: 'bg-gray-400' },
  Unlisted: { pill: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400', dot: 'bg-red-400' },
};
