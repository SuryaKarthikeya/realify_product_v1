export const inventoryStats = [
  {
    label: "Total Inventory Value",
    value: "$2.4M",
    trend: "8.2%",
    trendDir: "up",
    trendText: "vs last period",
    color: "green"
  },
  {
    label: "Inventory Turnover",
    value: "6.8x",
    trend: "+12.4%",
    trendDir: "up",
    trendText: "vs last period",
    color: "green"
  },
  {
    label: "Days of Inventory",
    value: "42 days",
    trend: "-3.2 days",
    trendDir: "up", // The HTML uses green trending for this decrease which is positive
    trendText: "vs last period",
    color: "green"
  },
  {
    label: "Stock Accuracy",
    value: "98.7%",
    trend: "+1.2%",
    trendDir: "down", // HTML uses red text/arrow down for this
    trendText: "vs last period",
    color: "red"
  }
];

export const inventoryIntel = [
  {
    id: 'signal-1',
    type: 'CRITICAL',
    time: '12 min ago',
    title: 'Stockout Risk Detected',
    description: '15 high-demand products approaching zero inventory within 48 hours. Immediate reorder required',
    severityColor: 'bg-red-500',
    impactValue: '$47K',
    impactLabel: 'Impact',
    details: {
      stats: [
        { label: 'Impact Assessment', value: 'High', sub: 'Potential $47K loss', color: 'text-red-600' },
        { label: 'Timeline', value: '48h', sub: 'Critical window', color: 'text-orange-600' },
        { label: 'Inventory Level', value: '5%', sub: 'Avg safety stock', color: 'text-blue-600' }
      ],
      products: [
        { name: 'Premium Wireless Headphones', trend: 'Critical', trendColor: 'text-red-600' },
        { name: 'Smart Security Camera', trend: 'Low Stock', trendColor: 'text-orange-600' },
        { name: 'Bluetooth Speaker', trend: 'Running Out', trendColor: 'text-red-500' }
      ],
      actions: [
        { label: 'Create Emergency PO', icon: 'fa-solid fa-cart-shopping', primary: true },
        { label: 'Notify Warehouse', icon: 'fa-solid fa-envelope', primary: false }
      ]
    }
  },
  {
    id: 'signal-2',
    type: 'WARNING',
    time: '28 min ago',
    title: 'Excess Inventory Alert',
    description: '8 products with 90+ days of stock. Consider promotional pricing or redistribution',
    severityColor: 'bg-orange-500',
    impactValue: '$124K',
    impactLabel: 'Tied Capital',
    details: {
      stats: [
        { label: 'Capital Impact', value: '$124K', sub: 'Working capital', color: 'text-orange-600' },
        { label: 'Storage Cost', value: '$3.2K', sub: 'Monthly fees', color: 'text-blue-600' },
        { label: 'Days of Stock', value: '90+', sub: 'Average aging', color: 'text-red-600' }
      ],
      products: [
        { name: 'Outdoor Camera Mount', trend: '95 days', trendColor: 'text-gray-600' },
        { name: 'Legacy XL Speaker', trend: '112 days', trendColor: 'text-gray-600' },
        { name: 'Pro Studio Stand', trend: '98 days', trendColor: 'text-gray-600' }
      ],
      actions: [
        { label: 'Create Promotion', icon: 'fa-solid fa-percentage', primary: true },
        { label: 'Internal Transfer', icon: 'fa-solid fa-truck', primary: false }
      ]
    }
  },
  {
    id: 'signal-3',
    type: 'INSIGHT',
    time: '1 hour ago',
    title: 'Seasonal Demand Pattern',
    description: 'Electronics category showing 45% demand increase typical of Q4 seasonal trend',
    severityColor: 'bg-blue-500',
    impactValue: '45%',
    impactLabel: 'Demand Surge',
    details: {
      stats: [
        { label: 'Forecast Delta', value: '+45%', sub: 'vs last month', color: 'text-blue-600' },
        { label: 'Affected SKUs', value: '42', sub: 'Electronics', color: 'text-gray-900' },
        { label: 'Confidence', value: '94%', sub: 'AI model rating', color: 'text-green-600' }
      ],
      products: [
        { name: 'Electronics Category', trend: '+45% Demand', trendColor: 'text-blue-600' }
      ],
      actions: [
        { label: 'Adjust Stock Levels', icon: 'fa-solid fa-arrows-rotate', primary: true },
        { label: 'View Forecast', icon: 'fa-solid fa-chart-line', primary: false }
      ]
    }
  },
  {
    id: 'signal-4',
    type: 'OPPORTUNITY',
    time: '2 hours ago',
    title: 'Fast-Moving Inventory Identified',
    description: '12 products with exceptional turnover rates (8.5x) - increase stock levels',
    severityColor: 'bg-green-500',
    impactValue: '8.5x',
    impactLabel: 'Turnover',
    details: {
      stats: [
        { label: 'Avg Turnover', value: '8.5x', sub: 'vs 4.2x category', color: 'text-green-600' },
        { label: 'Revenue Opp', value: '$38K', sub: 'Monthly potential', color: 'text-blue-600' },
        { label: 'Velocity', value: 'High', sub: 'Top 5% of SKUs', color: 'text-purple-600' }
      ],
      products: [
        { name: 'USB-C Charging Hub', trend: '12.4x', trendColor: 'text-green-600' },
        { name: 'Privacy Screen Protector', trend: '9.8x', trendColor: 'text-green-600' }
      ],
      actions: [
        { label: 'Increase Stock', icon: 'fa-solid fa-plus', primary: true },
        { label: 'Optimize Pricing', icon: 'fa-solid fa-tag', primary: false }
      ]
    }
  }
];

export const inventoryWatchlist = [
  {
    id: 'wh-pro-2024',
    title: 'Premium Wireless Headphones',
    sku: 'WH-PRO-2024',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/829ed95905-98415edd6aab0bba6e05.png',
    status: 'LOW',
    statusColor: 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30',
    stock: '24 units',
    velocity: '3.2 days',
    progress: 12,
    progressColor: 'bg-red-500',
    subtext: 'Reorder point: 50 units',
    metricLabel1: 'Stock Level',
    metricLabel2: 'Days Left'
  },
  {
    id: 'cam-sec-5000',
    title: 'Smart Security Camera',
    sku: 'CAM-SEC-5000',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/a92a4ffb64-d9b6565e03e56b627c33.png',
    status: 'MED',
    statusColor: 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-900/30',
    stock: '142 units',
    velocity: '18 days',
    progress: 45,
    progressColor: 'bg-orange-500',
    subtext: 'Optimal level: 320 units',
    metricLabel1: 'Stock Level',
    metricLabel2: 'Days Left'
  },

];

export const inventoryAnomalies = [
  {
    id: '7821',
    type: 'CRITICAL',
    title: 'Imminent Stockout Alert',
    description: '15 high-velocity products will run out of stock within 48 hours without immediate reorder',
    time: '45 min ago',
    icon: 'fa-solid fa-triangle-exclamation',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Sudden demand surge (+180%) coupled with lead time volatility from secondary suppliers.',
      resolution: 'Initiate emergency purchase orders with express air freight. Notify marketing to pause campaigns for affected SKUs.',
      risks: 'Higher landing costs impacting margin ($4.50/unit). Potential fulfillment bottleneck at Newark DC.'
    }
  },
  {
    id: '7820',
    type: 'HIGH',
    title: 'Overstock Situation',
    description: '8 products with 90+ days of inventory tying up $124K in working capital',
    time: '1 hour ago',
    icon: 'fa-solid fa-warehouse',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'High',
    details: {
      rootCause: 'Over-forecasting of Q3 demand for the Outdoor line. Seasonal transition happened 2 weeks earlier than expected.',
      resolution: 'Launch "End of Cycle" clearance campaign (25% off). Transfer excess stock to high-demand West Coast region where warmer weather persists.',
      risks: 'Brand perception impact of high discounts. Inventory transfer costs ($1.2K).'
    }
  },
  {
    id: '7819',
    type: 'MEDIUM',
    title: 'Supplier Shipment Delay',
    description: 'Purchase order PO-8421 delayed by 5 days, impacting 23 SKUs replenishment',
    time: '3 hours ago',
    icon: 'fa-solid fa-truck-fast',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    iconColor: 'text-yellow-600',
    category: 'Medium',
    details: {
      rootCause: 'Labor strikes at port of origin causing backlog in container processing.',
      resolution: 'Coordinate with freight forwarder to prioritize PO-8421 for unloading. Update customer service on new shipping promise dates.',
      risks: 'Stockouts for 12 of the 23 SKUs if delay exceeds 8 days.'
    }
  },
  {
    id: '7818',
    type: 'CRITICAL',
    title: 'Demand Spike Detected',
    description: 'Unexpected 180% demand surge on Smart Camera line, current stock insufficient',
    time: '5 hours ago',
    icon: 'fa-solid fa-chart-line',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Product featured in major tech influencer review video without prior notification.',
      resolution: 'Activate safety stock buffers. Negotiate priority production run with manufacturer.',
      risks: 'High competitor pricing response. Backlog of orders impacting CSAT.'
    }
  },
  {
    id: '7817',
    type: 'MEDIUM',
    title: 'Inventory Accuracy Issue',
    description: '18 SKUs showing discrepancy between system and physical count',
    time: '7 hours ago',
    icon: 'fa-solid fa-exclamation',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600',
    category: 'Medium',
    details: {
      rootCause: 'Process failure in unrecorded returns processing at the Chicago warehouse.',
      resolution: 'Conduct full blind-count of affected aisle. Refresh training for receiving team on return handling.',
      risks: 'Incorrect available-to-promise data leading to overselling.'
    }
  },
  {
    id: '7816',
    type: 'POSITIVE',
    title: 'Improved Turnover Rate',
    description: 'Electronics showing 28% improvement in inventory turnover vs last quarter',
    time: '9 hours ago',
    icon: 'fa-solid fa-rotate',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Positive',
    details: {
      rootCause: 'Successful implementation of dynamic reorder points and AI-driven allocation.',
      resolution: 'Baseline these settings for the Apparel and Home & Garden categories. Document success for quarterly review.',
      risks: 'Potential for being too "lean" if seasonal volatility increases.'
    }
  }
];

export const inventoryRecommendations = [
  {
    id: '3471',
    type: 'REORDER',
    title: 'Optimize Reorder Points',
    description: 'Adjust reorder points for 24 fast-moving SKUs to prevent stockouts',
    stats: [
      { label: 'Est. Impact', value: '$42K Rev' },
      { label: 'Confidence', value: '96%' }
    ],
    time: 'High Priority',
    icon: 'fa-solid fa-lightbulb',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600',
    category: 'Reorder',
    details: {
      rootCause: 'Current static reorder points are based on 2023 demand levels. 2024 velocity for electronics has increased by 14%.',
      resolution: 'Switch to AI-calculated dynamic reorder points based on 30-day trailing sales and forecasted seasonal trends for Q4.',
      risks: 'Minor increase in average daily inventory value (~$12K) to offset stockout risk.'
    }
  },
  {
    id: '3470',
    type: 'TRANSFER',
    title: 'Warehouse Rebalancing',
    description: 'Transfer 12 overstock items from West Coast DC to East Coast DC',
    stats: [
      { label: 'Savings', value: '$8.2K/mo' },
      { label: 'ROI', value: '340%' }
    ],
    time: 'Medium Priority',
    icon: 'fa-solid fa-arrows-rotate',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Transfer',
    details: {
      rootCause: 'Regional demand imbalance: Electronics demand in NYC is 3x higher than in LA for the current SKU mix.',
      resolution: 'Consolidate 1,200 units of slow-moving LA stock and ship via rail to NJ hub for immediate distribution.',
      risks: '7-day lead time for transfer during which LA demand could spike above remaining local stock.'
    }
  },
  {
    id: '3469',
    type: 'PROMOTION',
    title: 'Clearance Campaign',
    description: 'Run 25% discount on 8 slow-moving products to free up capital',
    stats: [
      { label: 'Free Capital', value: '$124K' },
      { label: 'Units', value: '3.4K' }
    ],
    time: 'Medium Priority',
    icon: 'fa-solid fa-percentage',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600',
    category: 'Promotion',
    details: {
      rootCause: 'End-of-life for "Classic" series models. New "Pro" line launching in 30 days.',
      resolution: 'Launch targeted email blast to legacy customers with a "Member-Only" 25% discount code for the Classic series.',
      risks: 'Cannibalization of brand-new "Pro" line if price difference is too wide.'
    }
  },
  {
    id: '3468',
    type: 'FORECAST',
    title: 'Seasonal Stock Adjustment',
    description: 'Increase safety stock for electronics category ahead of Q4 surge',
    stats: [
      { label: 'Demand Delta', value: '+45%' },
      { label: 'Target Date', text: 'Oct 15' }
    ],
    time: 'Low Priority',
    icon: 'fa-solid fa-chart-line',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'Forecast',
    details: {
      rootCause: 'Predictive models show strong early holiday shopping intent. Q4 2024 forecasted to be 12% higher than Q4 2023.',
      resolution: 'Increase safety stock across top 50 electronics SKUs by 1.5x standard deviation. Pre-book carrier space for Nov/Dec.',
      risks: 'Overstock if macroeconomic factors depress holiday consumer spending unexpectedly.'
    }
  }
];

/* ── Inventory trends ── */

/** The three series, in render order. Colours come from CHART_CATEGORICAL. */
export const INVENTORY_CATEGORIES = [
  { key: 'electronics', name: 'Electronics' },
  { key: 'apparel', name: 'Apparel' },
  { key: 'home', name: 'Home & Garden' },
];

export const INVENTORY_GRANULARITIES = ['Daily', 'Weekly', 'Monthly'];

/**
 * Average cost per unit held, by category.
 *
 * Stock value is derived from units rather than being a second hand-written
 * series: the two views of this chart are the same inventory measured two ways,
 * so they have to move together. These costs are also chosen so the latest daily
 * total lands on ₹1.82M — the figure the Inventory KPI card above the chart
 * quotes — instead of the card and the chart disagreeing about the same stock.
 */
export const INVENTORY_UNIT_COST = { electronics: 1100, apparel: 580, home: 430 };

/**
 * Units in stock per period.
 *
 * Weekly and monthly are *average* levels, not sums. Inventory is a stock, not a
 * flow — adding up Monday-to-Sunday would report seven times the stock that was
 * ever actually on the shelf.
 */
const INVENTORY_TREND_UNITS = {
  Daily: [
    { name: 'Mon', electronics: 850, apparel: 620, home: 420 },
    { name: 'Tue', electronics: 920, apparel: 650, home: 440 },
    { name: 'Wed', electronics: 880, apparel: 640, home: 450 },
    { name: 'Thu', electronics: 950, apparel: 680, home: 460 },
    { name: 'Fri', electronics: 1020, apparel: 710, home: 480 },
    { name: 'Sat', electronics: 1100, apparel: 750, home: 500 },
    { name: 'Sun', electronics: 1080, apparel: 730, home: 490 },
  ],
  Weekly: [
    { name: 'W1', electronics: 780, apparel: 590, home: 400 },
    { name: 'W2', electronics: 845, apparel: 615, home: 415 },
    { name: 'W3', electronics: 910, apparel: 640, home: 435 },
    { name: 'W4', electronics: 968, apparel: 683, home: 457 },
    { name: 'W5', electronics: 1035, apparel: 705, home: 472 },
    { name: 'W6', electronics: 1092, apparel: 738, home: 494 },
  ],
  Monthly: [
    { name: 'Feb', electronics: 640, apparel: 505, home: 350 },
    { name: 'Mar', electronics: 705, apparel: 545, home: 372 },
    { name: 'Apr', electronics: 812, apparel: 598, home: 404 },
    { name: 'May', electronics: 884, apparel: 631, home: 428 },
    { name: 'Jun', electronics: 951, apparel: 672, home: 451 },
    { name: 'Jul', electronics: 1024, apparel: 714, home: 478 },
  ],
};

/** Daily units — the shape this module has always exported. */
export const inventoryTrendData = INVENTORY_TREND_UNITS.Daily;

/**
 * The series behind the chart, for one granularity and one metric.
 *
 * `level` is units in stock; `value` is those units priced at
 * `INVENTORY_UNIT_COST`, so switching the toggle re-expresses the same data
 * rather than showing a different dataset.
 */
export const inventoryTrends = (granularity = 'Daily', metric = 'level') => {
  const rows = INVENTORY_TREND_UNITS[granularity] || INVENTORY_TREND_UNITS.Daily;
  if (metric !== 'value') return rows;

  return rows.map((row) => ({
    name: row.name,
    ...INVENTORY_CATEGORIES.reduce(
      (acc, c) => ({ ...acc, [c.key]: row[c.key] * INVENTORY_UNIT_COST[c.key] }),
      {}
    ),
  }));
};

/** What the Level / Value switch says on each side. */
export const INVENTORY_METRICS = {
  level: { key: 'level', label: 'Inventory Level', sub: 'Units in stock', icon: 'fa-layer-group', axis: 'Units' },
  value: { key: 'value', label: 'Inventory Value', sub: 'Stock value (₹)', icon: 'fa-dollar-sign', axis: 'Value (₹)' },
};

/** Compact ₹, and plain counts for units. */
export const formatInventoryMetric = (n, metric, { compact = false } = {}) => {
  if (!Number.isFinite(n)) return '—';
  if (metric !== 'value') return n.toLocaleString('en-US');
  if (!compact) return `₹${n.toLocaleString('en-IN')}`;
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)}Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`;
  if (n >= 1e3) return `₹${(n / 1e3).toFixed(0)}K`;
  return `₹${n}`;
};

export const stockStatusData = [
  { name: 'In Stock', value: 2124, color: '#1D63FF' },
  { name: 'Low Stock', value: 568, color: '#4B69EC' },
  { name: 'Out of Stock', value: 155, color: '#01329E' },
];

export const warehouseDistributionData = [
  { name: 'Main Warehouse', value: 1247, color: '#2E4CB9' },
  { name: 'East Coast DC', value: 894, color: '#5E7BFF' },
  { name: 'West Coast DC', value: 706, color: '#7FA9FF' },
];

export const categoryTurnoverData = [
  { name: 'Electronics', value: 8.5 },
  { name: 'Apparel', value: 6.2 },
  { name: 'Home & Garden', value: 5.8 },
  { name: 'Sports', value: 7.1 },
  { name: 'Books', value: 4.3 },
];

export const categoryDaysData = [
  { name: 'Electronics', value: 42 },
  { name: 'Apparel', value: 58 },
  { name: 'Home & Garden', value: 62 },
  { name: 'Sports', value: 51 },
  { name: 'Books', value: 84 },
];
