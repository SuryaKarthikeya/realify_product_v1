export const salesIntelItems = [
  {
    id: 'signal-1',
    type: 'CRITICAL',
    time: '2 min ago',
    title: 'Competitor Price Drop Detected',
    description: 'Major competitor reduced prices by 15% on 23 overlapping SKUs in Electronics category',
    impactValue: '$34K',
    impactLabel: 'Revenue Risk',
    severityColor: 'bg-red-500',
    details: {
      stats: [
        { label: 'Affected SKUs', value: '23', sub: 'Products impacted' },
        { label: 'Average Difference', value: '-15%', sub: 'Below our pricing', color: 'text-red-600' },
        { label: 'Est. Impact', value: '$34K', sub: 'Monthly revenue at risk' }
      ],
      products: [
        { name: 'Premium Wireless Headphones', trend: '-18%', trendColor: 'text-red-600' },
        { name: 'Smart Home Security Camera', trend: '-16%', trendColor: 'text-red-600' }
      ],
      actions: [
        { label: 'Analyze Impact', icon: 'fa-solid fa-chart-line', primary: true },
        { label: 'Adjust Pricing', icon: 'fa-solid fa-tag' }
      ]
    }
  },
  {
    id: 'signal-2',
    type: 'OPPORTUNITY',
    time: '18 min ago',
    title: 'Social Media Viral Product',
    description: 'Smart Home Security Camera gaining massive traction on TikTok and Instagram',
    impactValue: '850',
    impactLabel: 'Est. Demand',
    severityColor: 'bg-green-500',
    details: {
      stats: [
        { label: 'Social Mentions', value: '12.4K', sub: 'Last 6 hours' },
        { label: 'Search Growth', value: '+340%', sub: 'vs 24h avg', color: 'text-green-600' },
        { label: 'Current Stock', value: '124', sub: 'Units available' }
      ],
      actions: [
        { label: 'Increase Stock', icon: 'fa-solid fa-box', primary: true },
        { label: 'Boost Ads', icon: 'fa-solid fa-bullhorn' }
      ]
    }
  },
  {
    id: 'signal-3',
    type: 'INSIGHT',
    time: '1 hour ago',
    title: 'Customer Segment Shift',
    description: 'Premium segment customers showing 28% higher engagement with mid-tier products',
    impactValue: '$52K',
    impactLabel: 'Revenue Opp',
    severityColor: 'bg-blue-500',
    details: {
      stats: [
        { label: 'Customers', value: '2,847', sub: 'Premium segment' },
        { label: 'Engagement', value: '+28%', sub: 'vs baseline', color: 'text-blue-600' },
        { label: 'Avg Purchase', value: '$187', sub: 'Order value' }
      ],
      actions: [
        { label: 'View Segment', icon: 'fa-solid fa-users', primary: true },
        { label: 'Create Campaign', icon: 'fa-solid fa-envelope' }
      ]
    }
  },
  {
    id: 'signal-4',
    type: 'MARKET',
    time: '3 hours ago',
    title: 'Regional Demand Surge',
    description: 'West Coast showing unexpected 47% increase in Home & Garden category',
    impactValue: '156',
    impactLabel: 'Products',
    severityColor: 'bg-orange-500',
    details: {
      stats: [
        { label: 'Growth Rate', value: '+47%', sub: 'vs previous week', color: 'text-orange-600' },
        { label: 'Products', value: '156', sub: 'In category' },
        { label: 'Stock Level', value: '78%', sub: 'Capacity' }
      ],
      actions: [
        { label: 'Rebalance Inventory', icon: 'fa-solid fa-truck', primary: true },
        { label: 'View Trends', icon: 'fa-solid fa-chart-area' }
      ]
    }
  },
  {
    id: 'signal-5',
    type: 'REVIEW',
    time: '5 hours ago',
    title: 'Product Review Spike',
    description: 'Organic Cotton T-Shirt receiving 3x normal review volume with 92% positive sentiment',
    impactValue: '4.8',
    impactLabel: 'Rating',
    severityColor: 'bg-yellow-500',
    details: {
      stats: [
        { label: 'Reviews', value: '247', sub: 'Last 7 days' },
        { label: 'Sentiment', value: '92%', sub: 'Positive', color: 'text-green-600' },
        { label: 'Avg Rating', value: '4.8', sub: 'Out of 5.0' }
      ],
      actions: [
        { label: 'Promote Product', icon: 'fa-solid fa-bullhorn', primary: true },
        { label: 'Read Reviews', icon: 'fa-solid fa-comments' }
      ]
    }
  },
  {
    id: 'signal-6',
    type: 'ALERT',
    time: '8 hours ago',
    title: 'Supply Chain Delay',
    description: 'Supplier notification: 14-day delay on Winter Sports Equipment shipment',
    impactValue: '34',
    impactLabel: 'SKUs',
    severityColor: 'bg-red-500',
    details: {
      stats: [
        { label: 'Delay Duration', value: '14', sub: 'Days' },
        { label: 'Current Stock', value: '9', sub: 'Days remaining', color: 'text-red-600' },
        { label: 'Affected SKUs', value: '34', sub: 'Products' }
      ],
      actions: [
        { label: 'Find Alternative', icon: 'fa-solid fa-search', primary: true },
        { label: 'Contact Supplier', icon: 'fa-solid fa-phone' }
      ]
    }
  }
];

export const salesRecommendations = [
  {
    id: '8471',
    type: 'HIGH IMPACT',
    title: 'Dynamic Pricing Opportunity',
    description: 'Adjust pricing on 34 products to capture $18,400 additional revenue this week based on competitor analysis and demand patterns.',
    stats: [
      { label: 'Est. Revenue', value: '+$18,400' },
      { label: 'Confidence', value: '94%' }
    ],
    time: '5 min ago',
    icon: 'fa-solid fa-chart-line',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600',
    category: 'High Impact',
    details: {
      rootCause: 'Market analysis shows that while demand for smart-home electronics is up, our current price points for 34 key SKUs are roughly 8% above the new competitor baseline set by tech-retailers.',
      resolution: 'Implement a targeted 4-6% price reduction across the affected SKUs while simultaneously launching a "Price Match Guarantee" banner on product pages to boost conversion confidence.',
      risks: 'Minor short-term margin compression. Competitors might further lower prices in a "race to the bottom" scenario.'
    }
  },
  {
    id: '8470',
    type: 'URGENT',
    title: 'Restock Critical Items',
    description: '5 high-velocity products will stock out within 48 hours. Immediate action required to prevent revenue loss.',
    stats: [
      { label: 'Revenue at Risk', value: '$42,350' },
      { label: 'Time', value: '48 hours' }
    ],
    time: '12 min ago',
    icon: 'fa-solid fa-boxes-stacked',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Urgent',
    details: {
      rootCause: 'Unexpected sales velocity spike (+120%) over the weekend for the Premium Wireless series. Current incoming shipment is delayed at regional hub.',
      resolution: 'Authorize expedited air-freight for 500 units from secondary warehouse. Enable "Backorder" status with a clear 5-day delivery promise to capture immediate sales.',
      risks: 'Increased shipping costs ($2.40 per unit). Potential for high return rate if backorder shipments face further delays.'
    }
  },
  {
    id: '8469',
    type: 'GROWTH',
    title: 'Boost Viral Products',
    description: 'Increase marketing spend on 3 trending items to capitalize on social media momentum and maximize revenue potential.',
    stats: [
      { label: 'Social Growth', value: '+427%' },
      { label: 'Est. ROI', value: '340%' }
    ],
    time: '24 min ago',
    icon: 'fa-solid fa-bullhorn',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600',
    category: 'Growth',
    details: {
      rootCause: 'Smart Home Security Camera featured in top tech influencer "Home Safety 2024" roundup, generating 800K+ views and significant organic search volume.',
      resolution: 'Increase Meta and Google Ad spend by $5,000 for these specific SKUs. Use influencer clips for retargeting campaigns. Set up a "As Seen on Social" landing page.',
      risks: 'Inventory stockouts before the campaign ends. Ad fatigue if the creative isn\'t refreshed frequently.'
    }
  },
  {
    id: '8468',
    type: 'RETENTION',
    title: 'Customer Re-engagement',
    description: "Target 1,247 high-value customers who haven't purchased in 30+ days with personalized offers to drive repeat sales.",
    stats: [
      { label: 'Customers', value: '1,247' },
      { label: 'Avg LTV', value: '$842' }
    ],
    time: '1 hour ago',
    icon: 'fa-solid fa-users',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'Retention',
    details: {
      rootCause: 'Seasonal drop in engagement from Q4 peak buyers. Cohort analysis suggests many "one-time" high-spenders haven\'t revisited since December.',
      resolution: 'Trigger a "Win Back" email sequence offering a personalized 15% discount on products frequently bought with their last purchase. A/B test Subject lines focusing on "We Miss You".',
      risks: 'Coupon dependency where customers wait for discounts. Minor unsubscribes from marketing emails.'
    }
  },
  {
    id: '8467',
    type: 'GROWTH',
    title: 'Bundle Optimization',
    description: 'Create 7 product bundles with 89% purchase correlation to boost average order value and increase customer satisfaction.',
    stats: [
      { label: 'AOV Increase', value: '+$47' },
      { label: 'Correlation', value: '89%' }
    ],
    time: '2 hours ago',
    icon: 'fa-solid fa-gift',
    bgColor: 'bg-pink-100 dark:bg-pink-900/30',
    iconColor: 'text-pink-600',
    category: 'Growth',
    details: {
      rootCause: 'Analysis of 10,000 transactions shows that Wireless Headphones are bought with Protective Cases and Extra Charging Cables 89% of the time.',
      resolution: 'Launch "The Complete Mobile Bundle" offering a 10% discount when all three items are bought together. Display the bundle prominently on the product detail page.',
      risks: 'Cannibalization of high-margin individual cable sales. Complexity in inventory management for virtual bundles.'
    }
  },
  {
    id: '8466',
    type: 'HIGH IMPACT',
    title: 'Regional Expansion',
    description: 'West Coast demand surge presents opportunity to expand Home & Garden inventory and capture growing market share.',
    stats: [
      { label: 'Growth', value: '+47%' },
      { label: 'Payback', value: '3.2 weeks' }
    ],
    time: '3 hours ago',
    icon: 'fa-solid fa-map-marked-alt',
    bgColor: 'bg-cyan-100 dark:bg-cyan-900/30',
    iconColor: 'text-cyan-600',
    category: 'High Impact',
    details: {
      rootCause: 'Favorable weather conditions and a local "Home Improvement Expo" in the California region driving atypical demand for garden equipment.',
      resolution: 'Shift 40% of standard Home & Garden inventory from the East Coast hub to the California fulfillment center. Negotiate with local courier for priority shipping.',
      risks: 'Stock shortages on the East Coast if a similar trend starts there. Higher inter-warehouse transfer costs.'
    }
  }
];

export const salesAnomalies = [
  {
    id: '2847',
    type: 'CRITICAL',
    title: 'Inventory Depletion Alert',
    description: 'Premium Wireless Headphones - Current stock: 47 units, Daily velocity: 23 units',
    time: '2 hours ago',
    icon: 'fa-solid fa-box',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Unexpected viral trend on TikTok leading to a 340% increase in daily velocity. Replenishment shipment currently stuck in customs.',
      resolution: 'Redirecting 200 units from East Coast warehouse via express air. Notifying customers of potential 3-day shipping delay.',
      risks: 'Loss of sales if redirect fails. Higher shipping costs impacting unit margin.'
    }
  },
  {
    id: '2846',
    type: 'HIGH',
    title: 'Unusual Sales Spike',
    description: 'Smart Home Security Camera - 7-day sales: 342 units (+287% vs average)',
    time: '4 hours ago',
    icon: 'fa-solid fa-chart-line',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    iconColor: 'text-orange-600',
    category: 'High',
    details: {
      rootCause: 'Product featured as "Top Pick" on a major tech review blog. Strong correlation with secondary accessories sales.',
      resolution: 'Increasing ad spend by 25% to sustain momentum. Launching a limited-time bundle with SecuCam Cloud storage.',
      risks: 'Stockout of accessories. Potential for increased support tickets from new users.'
    }
  },
  {
    id: '2845',
    type: 'MEDIUM',
    title: 'Price Sensitivity Detected',
    description: 'Organic Cotton T-Shirt - Current price: $24.99, Optimal price: $19.99',
    time: '6 hours ago',
    icon: 'fa-solid fa-tag',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    iconColor: 'text-yellow-600',
    category: 'Medium',
    details: {
      rootCause: 'A/B testing shows a 42% lift in conversion rates at the $19.99 price point. Competitors are currently at $21.99.',
      resolution: 'Permanently adjusting MSRP to $19.99. Launching a "Bulk Buy" promo (3 for $50) to offset margin impact with volume.',
      risks: 'Lower per-unit margin. Potential brand perception shift to "budget" segment.'
    }
  },
  {
    id: '2844',
    type: 'CRITICAL',
    title: 'Return Rate Anomaly',
    description: 'Designer Leather Wallet - Return rate: 18.4%, Avg rating: 3.2/5.0',
    time: '8 hours ago',
    icon: 'fa-solid fa-undo',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600',
    category: 'Critical',
    details: {
      rootCause: 'Batches #WM-42 through #WM-48 have structural defects in zipper hardware. Customer feedback consistently mentions "stuck zipper".',
      resolution: 'Pausing sales for the affected SKU immediately. Contacting previous buyers for proactive replacements. Auditing supplier QC process.',
      risks: 'Damage to brand reputation. Financial loss from refunds and replacement stock.'
    }
  },
  {
    id: '2843',
    type: 'INFO',
    title: 'Regional Demand Shift',
    description: 'Home & Garden Category - West Coast: +47%, Products: 156',
    time: '10 hours ago',
    icon: 'fa-solid fa-map-marker-alt',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600',
    category: 'Positive',
    details: {
      rootCause: 'Early spring weather in California and Oregon driving garden preparation sales 3 weeks ahead of schedule.',
      resolution: 'Expediting Home & Garden inventory to West Coast hubs. Running geo-targeted social ads for these regions.',
      risks: 'Potential overstock if the "early spring" turns into a late frost.'
    }
  },
  {
    id: '2842',
    type: 'POSITIVE',
    title: 'Review Sentiment Surge',
    description: 'Bluetooth Speaker Pro receiving exceptional customer reviews with high sentiment scores and ratings.',
    time: '12 hours ago',
    icon: 'fa-solid fa-star',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600',
    category: 'Positive',
    details: {
      rootCause: 'New firmware update resolved previous connectivity issues, leading to a wave of 5-star reviews and improved sentiment.',
      resolution: 'Updating product descriptions to highlight "Improved Connectivity". Using top reviews in marketing copy.',
    }
  }
];

export const revenueTrendData = [
  { name: 'Mon', revenue: 12000, forecast: 10000 },
  { name: 'Tue', revenue: 18000, forecast: 14000 },
  { name: 'Wed', revenue: 15000, forecast: 13000 },
  { name: 'Thu', revenue: 22000, forecast: 18000 },
  { name: 'Fri', revenue: 30000, forecast: 25000 },
  { name: 'Sat', revenue: 25000, forecast: 22000 },
  { name: 'Sun', revenue: 35000, forecast: 28000 },
];

