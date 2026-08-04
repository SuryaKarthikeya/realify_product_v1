export const marginIntelItems = [
  {
    id: 'signal-1',
    type: 'CRITICAL',
    time: '15 min ago',
    title: 'Supplier Cost Increase Detected',
    description: 'Major supplier increased wholesale prices by 12% on 18 SKUs in Electronics category, impacting margin by $14,200',
    impactValue: '-$14.2K',
    impactLabel: 'Margin Impact',
    severityColor: 'bg-red-500',
    details: {
      stats: [
        { label: 'Affected SKUs', value: '18', sub: 'Products impacted' },
        { label: 'Cost Increase', value: '+12%', sub: 'Avg across SKUs', color: 'text-red-600' },
        { label: 'Margin Drop', value: '-8.4%', sub: 'Category impact' }
      ],
      products: [
        { name: 'Wireless Headphones Pro', trend: '+12% COGS', trendColor: 'text-red-600' },
        { name: 'Smart Watch Series 5', trend: '+12% COGS', trendColor: 'text-red-600' }
      ],
      actions: [
        { label: 'Adjust Pricing', icon: 'fa-solid fa-tag', primary: true },
        { label: 'Set Alert', icon: 'fa-solid fa-bell' }
      ]
    }
  },
  {
    id: 'signal-2',
    type: 'OPPORTUNITY',
    time: '32 min ago',
    title: 'High-Margin Product Trending',
    description: 'Premium Wireless Headphones (58% margin) showing 240% demand increase with strong profitability',
    impactValue: '+$28K',
    impactLabel: 'Profit Opp',
    severityColor: 'bg-green-500',
    details: {
      stats: [
        { label: 'Demand Growth', value: '+240%', sub: 'Last 24 hours', color: 'text-green-600' },
        { label: 'Gross Margin', value: '58%', sub: 'Unit average' },
        { label: 'Profit Potential', value: '$28K', sub: 'Next 7 days' }
      ],
      actions: [
        { label: 'Increase Inventory', icon: 'fa-solid fa-rocket', primary: true },
        { label: 'Share Insight', icon: 'fa-solid fa-share' }
      ]
    }
  },
  {
    id: 'signal-3',
    type: 'INSIGHT',
    time: '1 hour ago',
    title: 'Category Margin Compression',
    description: 'Apparel category margins declined 4.2% due to increased shipping costs and promotional activity',
    impactValue: '-4.2%',
    impactLabel: 'Margin Diff',
    severityColor: 'bg-blue-500',
    details: {
      stats: [
        { label: 'Shipping Impact', value: '-2.5%', sub: 'Cost increase', color: 'text-red-600' },
        { label: 'Promo Impact', value: '-1.7%', sub: 'Discounting' },
        { label: 'Products', value: '127', sub: 'In category' }
      ],
      actions: [
        { label: 'View Recommendations', icon: 'fa-solid fa-lightbulb', primary: true },
        { label: 'Export Data', icon: 'fa-solid fa-download' }
      ]
    }
  },
  {
    id: 'signal-4',
    type: 'MARKET',
    time: '2 hours ago',
    title: 'Freight Cost Optimization',
    description: 'New logistics partner offering 18% lower shipping rates for West Coast deliveries',
    impactValue: '-18%',
    impactLabel: 'Cost Reduction',
    severityColor: 'bg-orange-500',
    details: {
      stats: [
        { label: 'Rate Reduction', value: '18%', sub: 'West Coast', color: 'text-green-600' },
        { label: 'Monthly Savings', value: '$9.8K', sub: 'Est. reduction' },
        { label: 'Payback', value: '0 days', sub: 'Instant ROI' }
      ],
      actions: [
        { label: 'Contact Partner', icon: 'fa-solid fa-truck', primary: true },
        { label: 'Review Contract', icon: 'fa-solid fa-file-contract' }
      ]
    }
  }
];

export const marginWatchlistItems = [
  {
    title: 'Premium Wireless Headphones',
    sku: 'WH-PRO-2024',
    stock: '58.2%',
    velocity: '$87.40',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/829ed95905-98415edd6aab0bba6e05.png',
    status: 'HIGH',
    statusColor: 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-900/50',
    progress: 58,
    progressColor: 'bg-green-500',
    subtext: 'Top performer in category',
    metricLabel1: 'Margin',
    metricLabel2: 'Profit/Unit'
  },
  {
    title: 'Organic Cotton T-Shirt',
    sku: 'APP-TS-ORG-01',
    stock: '18.4%',
    velocity: '$4.60',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/a500720697-b057d7260ef8941e1df2.png',
    status: 'LOW',
    statusColor: 'bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 border-red-200 dark:border-red-900/50',
    progress: 18,
    progressColor: 'bg-red-500',
    subtext: 'Margin improvement needed',
    metricLabel1: 'Margin',
    metricLabel2: 'Profit/Unit'
  },

];

export const marginAnomalies = [
  {
    id: '3421',
    type: 'CRITICAL',
    title: 'Margin Erosion Alert',
    description: 'Electronics category margins dropped 8.4% in last 48 hours due to supplier cost increases',
    time: '1 hour ago',
    icon: 'fa-solid fa-arrow-trend-down',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Sudden 12% increase in wholesale prices from primary electronics supplier (TechFlow Corp) without prior notice. Impacting high-volume SKUs including Wireless Pro series.',
      resolution: 'Initiated price adjustment of +5% across affected SKUs. Renegotiating bulk discount terms with TechFlow. Identifying alternative secondary suppliers for diversification.',
      risks: 'Potential 3-5% drop in sales volume due to price hike. Competitor price matching may lead to further margin compression if they do not follow the trend.'
    }
  },
  {
    id: '3420',
    type: 'HIGH',
    title: 'Shipping Cost Spike',
    description: 'Freight costs increased 22% for West Coast shipments impacting overall margins',
    time: '3 hours ago',
    icon: 'fa-solid fa-truck',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'High',
    details: {
      rootCause: 'Fuel surcharges and port congestion on the West Coast leading to premium freight rates and longer lead times.',
      resolution: 'Re-routing 40% of future shipments through East Coast ports. Consolidating smaller shipments into full containers. Negotiating fixed-rate contract for next 6 months.',
      risks: 'Increased lead time (+4-6 days) for West Coast customers. Higher inventory holding costs if East Coast warehouses reach capacity.'
    }
  },
  {
    id: '3419',
    type: 'MEDIUM',
    title: 'Promotional Margin Impact',
    description: 'Heavy discounting in Apparel reducing margins by 6.2% vs target',
    time: '5 hours ago',
    icon: 'fa-solid fa-percentage',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    iconColor: 'text-yellow-600',
    category: 'Medium',
    details: {
      rootCause: 'Summer sale campaign overlaps with aggressive stackable coupons from influencer partnerships, exceeding the planned 15% discount cap.',
      resolution: 'Modified coupon logic to prevent stacking on already discounted clearance items. Adjusting upcoming "Back to School" promo to prioritize higher-margin bundles.',
      risks: 'Reduced customer satisfaction if coupons are revoked. Potential slowdown in inventory turnover for slow-moving apparel.'
    }
  },
  {
    id: '3418',
    type: 'CRITICAL',
    title: 'Low-Margin Product Volume',
    description: 'T-Shirt line (18% margin) driving 34% of volume but only 12% of profit',
    time: '6 hours ago',
    icon: 'fa-solid fa-coins',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Aggressive ad spend on Basic T-Shirts category. While volume is high, the CAC (Customer Acquisition Cost) is eroding nearly all profitability.',
      resolution: 'Re-allocating 60% of T-Shirt ad budget to Premium Hoodies and Accessories. Setting hard stop on ad campaigns with ROAS below 2.5x.',
      risks: 'Significant drop in overall unit sales volume. May impact store-wide traffic if T-Shirts served as a "loss leader" entry point.'
    }
  },
  {
    id: '3417',
    type: 'POSITIVE',
    title: 'Supplier Negotiation Win',
    description: 'New supplier agreement secured 14% cost reduction on Home & Garden category',
    time: '8 hours ago',
    icon: 'fa-solid fa-arrow-trend-up',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Positive',
    details: {
      rootCause: 'Successful multi-round negotiation leveraging increased order volumes and longer contract commitment (18 months).',
      resolution: 'Maintaining current prices to capture the 14% margin gain. Reinvesting 20% of savings into expanded Home & Garden marketing.',
      risks: 'Long-term contract limits flexibility if market wholesale prices drop significantly below our new fixed rate.'
    }
  },
  {
    id: '3416',
    type: 'POSITIVE',
    title: 'Product Mix Improvement',
    description: 'High-margin products now representing 58% of sales mix, up from 42%',
    time: '10 hours ago',
    icon: 'fa-solid fa-chart-pie',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600',
    category: 'Positive',
    details: {
      rootCause: 'Effective cross-selling strategies on checkout page and improved "Recommended for you" AI performance prioritising profitability.',
      resolution: 'Further optimizing the product recommendation engine. Introducing tiered loyalty rewards for purchasing high-margin "Premium" collection items.',
      risks: 'Over-exposure of premium items might alienate budget-conscious segments. Continuous monitoring of conversion rates required.'
    }
  }
];

export const marginRecommendations = [
  {
    id: '9841',
    type: 'HIGH IMPACT',
    title: 'Optimize Pricing Strategy',
    description: 'Increase prices by 3-5% on 27 high-demand products to capture $24,800 additional margin without impacting volume.',
    stats: [
      { label: 'Est. Margin', value: '+$24,800' },
      { label: 'Confidence', value: '92%' }
    ],
    time: '8 min ago',
    icon: 'fa-solid fa-tags',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600',
    category: 'High Impact',
    details: {
      rootCause: 'Elascity of demand analysis suggests that 27 products in the Electronics category are underpriced relative to current market equilibrium, following a recent competitor price hike.',
      resolution: 'Implement a staggered price increase of 1.5% per week over three weeks to monitor conversion impact. Automate price monitoring to revert if conversion drops below a 5% threshold.',
      risks: 'Potential loss of price-sensitive customers. Risk of competitor undercut if they choose to maintain lower prices for volume.'
    }
  },
  {
    id: '9840',
    type: 'URGENT',
    title: 'Contract Renewal Opp',
    description: 'Supplier contract for Electronics category is up for renewal. Current market rates are 14% lower than our contract.',
    stats: [
      { label: 'Rev. At Risk', value: '$42,350' },
      { label: 'Time', value: '48 hours' }
    ],
    time: '24 min ago',
    icon: 'fa-solid fa-file-contract',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Urgent',
    details: {
      rootCause: 'Existing 2-year contract with "Global Gizmos Inc" is set to expire on the 15th. Market wholesale prices have dropped significantly due to new manufacturing efficiencies in the region.',
      resolution: 'Enter renegotiation with a firm 12% reduction target. Alternatively, we have qualified two secondary suppliers who can match the 14% lower market rate with equivalent quality.',
      risks: 'Transit time fluctuations if switching suppliers. Potential disruption in supply chain continuity during the transition phase.'
    }
  },
  {
    id: '9839',
    type: 'COST SAVINGS',
    title: 'Shipping Route Optimization',
    description: 'Consolidating West Coast shipments could reduce freight costs by 18% based on current volume.',
    stats: [
      { label: 'Est. ROI', value: '340%' }
    ],
    time: '1 hour ago',
    icon: 'fa-solid fa-truck-fast',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'Cost Savings',
    details: {
      rootCause: 'Current shipping model uses multiple small-batch air freight shipments. Data shows that 42% of these could be consolidated into weekly ocean freight without impacting SLA.',
      resolution: 'Switch 3 regional hubs to "Consolidated LCL" (Less than Container Load) shipping model. Update inventory lead-time buffers by 4 days to account for longer transit.',
      risks: 'Increased lead time volatility. Higher working capital tied up in "in-transit" inventory.'
    }
  },
  {
    id: '9838',
    type: 'PRICING',
    title: 'Bundle High-Margin Items',
    description: 'Create bundles including Premium Headphones and Cases to increase AOV and overall category margin.',
    stats: [
      { label: 'Customers', value: '1,247' }
    ],
    time: '2 hours ago',
    icon: 'fa-solid fa-layer-group',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600',
    category: 'Pricing',
    details: {
      rootCause: 'Premium Headphones have a 58% margin, while cases have an 82% margin. Customers buying both increase the overall transaction margin by 12.4% vs buying headphones alone.',
      resolution: 'Introduce the "Audiophile Starter Kit" on the product page. Use high-margin items as "add-ons" in the cart with a "Bundle & Save 10%" incentive.',
      risks: 'Minor cannibalization of individual case sales at full price. Inventory imbalance if one bundle component runs out.'
    }
  },
  {
    id: '9837',
    type: 'COST SAVINGS',
    title: 'Packaging Reduction',
    description: 'Switching to eco-friendly reduced packaging for Small Apparel could save $0.45 per unit in shipping costs.',
    stats: [
      { label: 'Unit Savings', value: '$0.45' }
    ],
    time: '3 hours ago',
    icon: 'fa-solid fa-leaf',
    bgColor: 'bg-pink-100 dark:bg-pink-900/30',
    iconColor: 'text-pink-600',
    category: 'Cost Savings',
    details: {
      rootCause: 'Current oversized boxes for lightweight apparel lead to high "Dimensional Weight" charges from carriers. 60% of the box volume is empty.',
      resolution: 'Switch to recycled poly-mailers for all t-shirt and light apparel orders. These reduce dimensional weight by 70% and lower unit packaging cost by $0.12.',
      risks: 'Reduced protection for items if mailers are mishandled. Customer perception of "less premium" unboxing experience.'
    }
  },
  {
    id: '9836',
    type: 'HIGH IMPACT',
    title: 'Ad Spend Reallocation',
    description: 'Shift ad budget from low-margin to high-margin electronics to improve ROAS and overall profitability.',
    stats: [
      { label: 'Est. ROAS', value: '+24%' }
    ],
    time: '4 hours ago',
    icon: 'fa-solid fa-ad',
    bgColor: 'bg-cyan-100 dark:bg-cyan-900/30',
    iconColor: 'text-cyan-600',
    category: 'High Impact',
    details: {
      rootCause: 'Google Ads currently spends 35% of budget on "Budget Headphones" (12% margin). High-margin Pro series (58% margin) only gets 12% of the budget despite similar conversion rates.',
      resolution: 'Re-balance Automated Bidding rules to prioritize "Profit Margin" over "Revenue". Increase budget cap on Pro series by 150%.',
      risks: 'Initial drop in total order volume. Potentially higher Customer Acquisition Cost (CAC) for premium segments.'
    }
  }
];

export const unprofitableSKUs = [
  { name: 'Portable Charger X 20000mAh', sku: 'B09MNO1234', channel: 'Amazon', loss: '-$3,420', sub: 'CM2 / 30d' },
  { name: 'Bamboo Cutting Board Set', sku: 'B09PQR5678', channel: 'Shopify', loss: '-$2,180', sub: 'CM2 / 30d' },
  { name: 'LED Desk Lamp Smart', sku: 'B09VWX3456', channel: 'Amazon', loss: '-$1,890', sub: 'CM2 / 30d' },
  { name: 'Yoga Mat Eco Premium', sku: 'B09STU9012', channel: 'Amazon', loss: '-$1,240', sub: 'CM2 / 30d' },
  { name: 'Kitchen Timer Digital 3-Pack', sku: 'B09YZA7890', channel: 'Shopify', loss: '-$870', sub: 'CM2 / 30d' }
];

export const adSpendImpact = [
  { name: 'Premium Wireless Headphones', spend: '$21,450', impact: 'CM2 $48.2K → CM3 $26.7K', erosion: '-44.6%', erosionType: 'danger' },
  { name: 'Smart Home Security Camera', spend: '$18,200', impact: 'CM2 $34.1K → CM3 $15.9K', erosion: '-53.4%', erosionType: 'danger' },
  { name: 'USB-C Hub 7-in-1', spend: '$12,800', impact: 'CM2 $19.8K → CM3 $7.0K', erosion: '-64.6%', erosionType: 'danger' }
];

export const cogsCompressions = [
  { name: 'Stainless Water Bottle 32oz', trend: 'COGS: $8.40 → $11.20', increase: '+33.3%', impact: 'CM2 eroded $4.5K' },
  { name: 'Organic Pet Food 15lb', trend: 'COGS: $18.50 → $22.10', increase: '+19.5%', impact: 'CM2 eroded $6.8K' },
  { name: 'Smart LED Strip 16ft RGB', trend: 'COGS: $4.20 → $4.90', increase: '+16.7%', impact: 'CM2 eroded $1.1K' }
];

export const returnsImpact = [
  { name: 'Premium Wireless Headphones', meta: '142 returns · 6.5% rate', loss: '-$8,114', sub: 'CM2 erosion' },
  { name: 'Ergonomic Office Chair Pro', meta: '28 returns · 8.2% rate', loss: '-$6,228', sub: 'CM2 erosion' },
  { name: 'Smart Home Security Camera', meta: '84 returns · 5.9% rate', loss: '-$5,880', sub: 'CM2 erosion' }
];

export const channelFeeData = [
  { name: 'Amazon', percentage: 16.0, value: '$98,240', share: '16.0%', color: '#2E4CB9' },
  { name: 'Shopify', percentage: 3.5, value: '$8,210', share: '3.5%', color: '#1D63FF' }
];

export const marginAnalysisData = [
  { sku: 'B09XYZ1234', title: 'Premium Wireless Headphones', channel: 'Amazon', revenue: '$124,500', cogs: '2,180', ads: '1,845', cm2: '$67.48', cm3: '+34.2%', gross: '92.1%', cm2pct: '5.8x' },
  { sku: 'B09ABC5678', title: 'Smart Home Security Camera', channel: 'Amazon', revenue: '$98,700', cogs: '1,410', ads: '1,320', cm2: '$74.77', cm3: '+28.1%', gross: '89.3%', cm2pct: '4.1x' },
  { sku: 'B09DEF9012', title: 'Organic Pet Food 15lb', channel: 'Shopify', revenue: '$76,340', cogs: '1,890', ads: '1,540', cm2: '$49.57', cm3: '+22.5%', gross: '—', cm2pct: '3.6x' },
  { sku: 'B09GHI3456', title: 'Ergonomic Office Chair Pro', channel: 'Amazon', revenue: '$68,900', cogs: '340', ads: '310', cm2: '$222.26', cm3: '+19.8%', gross: '94.8%', cm2pct: '6.2x' },
  { sku: 'B09JKL7890', title: 'USB-C Hub 7-in-1', channel: 'Amazon', revenue: '$54,120', cogs: '1,240', ads: '1,180', cm2: '$45.86', cm3: '+15.3%', gross: '88.2%', cm2pct: '3.9x' },
];

export const bleedingMarginData = [
  { sku: 'YM-STR-42', title: 'Yoga Mat Pro', cm2: -142, cmpct: -0.017, rev: 8520, risk: 1420, bb: 0.42, action: 'Reprice' },
  { sku: 'LED-DK-7', title: 'LED Desk Lamp', cm2: -98, cmpct: -0.014, rev: 6840, risk: 980, bb: 0.95, action: 'Investigate' },
  { sku: 'PH-CASE-X', title: 'Phone Case Ultra', cm2: -84, cmpct: -0.026, rev: 3200, risk: 840, bb: 1.0, action: 'Reprice' },
  { sku: 'SS-BTL-V2', title: 'Water Bottle', cm2: 12, cmpct: 0.003, rev: 4480, risk: 540, bb: 0.65, action: 'Reprice' },
  { sku: 'BK-STAND-1', title: 'Book Stand', cm2: 28, cmpct: 0.007, rev: 3840, risk: 380, bb: 0.51, action: 'Investigate' },
];

export const marginTrendData = [
  { name: 'Mon', margin: 42.3, cogs: 45000, revenue: 82000 },
  { name: 'Tue', margin: 41.8, cogs: 48000, revenue: 79000 },
  { name: 'Wed', margin: 43.1, cogs: 42000, revenue: 84000 },
  { name: 'Thu', margin: 42.5, cogs: 46000, revenue: 81000 },
  { name: 'Fri', margin: 42.9, cogs: 44000, revenue: 85000 },
  { name: 'Sat', margin: 41.7, cogs: 49000, revenue: 78000 },
  { name: 'Sun', margin: 42.3, cogs: 43000, revenue: 83000 },
];
