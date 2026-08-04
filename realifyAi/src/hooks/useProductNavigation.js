import { useNavigate } from 'react-router-dom';

const DEFAULT_STATUS_COLOR = 'bg-gray-50 dark:bg-slate-800/60 border-gray-200 dark:border-slate-700';

// Shared by every "no specific data available" product state across the app.
export const NO_SPECIFIC_INSIGHTS = ['No specific insights available'];


// The placeholder watchlistItem shape used whenever no real watchlist entry is
// found. `overrides` lets callers replace individual fields (e.g. Inventory's
// low-stock styling) while keeping the rest of the shared default shape.
export const buildFallbackWatchlistItem = (name, sku, overrides = {}) => ({
  title: name,
  sku,
  stock: '—',
  velocity: null,
  image: null,
  status: null,
  statusColor: DEFAULT_STATUS_COLOR,
  progress: 50,
  progressColor: 'bg-gray-400',
  subtext: 'No watchlist data available',
  ...overrides,
});

// The Sales / Margin / Inventory 3-group KPI skeleton shared verbatim by the
// Workspace, Revenue, Margin and Inventory "open product" handlers — only the
// underlying values differ per page's data source.
export const buildAnalyticsKpiGroups = (values) => [
  {
    label: 'Sales',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-900/10',
    kpis: [
      { label: 'Total Revenue', value: values.totalRevenue },
      { label: 'Units Sold', value: values.unitsSold },
      { label: 'Avg Price', value: values.avgPrice },
      { label: 'Buy Box %', value: values.buyBoxPct },
    ],
  },
  {
    label: 'Margin',
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/10',
    kpis: [
      { label: 'Margin %', value: values.marginPct },
      { label: 'CM2 Profit', value: values.cm2Profit },
      { label: 'Revenue', value: values.revenue },
      { label: 'Units', value: values.units },
    ],
  },
  {
    label: 'Inventory',
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-900/10',
    kpis: [
      { label: 'On-Hand', value: values.onHand },
      { label: 'DOC', value: values.doc },
      { label: 'Velocity', value: values.velocity },
      { label: 'Reorder Qty', value: values.reorderQty },
    ],
  },
];

// Navigates to the shared Product Detail page (`/product-view`) with a
// pre-built `product` state object plus the route the user came from.
const useProductNavigation = () => {
  const navigate = useNavigate();

  const goToProduct = (product, from) => {
    navigate('/product-view', { state: { from, product } });
  };

  return { goToProduct, buildFallbackWatchlistItem, buildAnalyticsKpiGroups, NO_SPECIFIC_INSIGHTS };
};

export default useProductNavigation;
