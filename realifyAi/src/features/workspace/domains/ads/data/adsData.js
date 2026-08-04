export const adsStats = [
  { label: 'Total Ad Spend', value: '$124K', trend: '+12.4%', trendDir: 'up', color: 'green' },
  { label: 'ROAS', value: '4.8x', trend: '+18.2%', trendDir: 'up', color: 'green' },
  { label: 'Average CPC', value: '$2.34', trend: '-8.5%', trendDir: 'up', color: 'green' }, // Trend up means "improving" usually, but HTML has green arrow up for -8.5% CPC
  { label: 'Conversion Rate', value: '3.2%', trend: '+0.8%', trendDir: 'down', color: 'red' }, // As per HTML visual
];

export const adsIntel = [
  {
    id: 'signal-1',
    type: 'CRITICAL',
    time: '8 min ago',
    title: 'CPC Spike Detected',
    description: '12 campaigns experiencing 40%+ CPC increase - immediate bid adjustment required',
    severityColor: 'bg-red-500',
    impactValue: '+$18K',
    impactLabel: 'Daily Spend',
    tags: [
      { label: '12 Campaigns at Risk', className: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 border border-red-200 dark:border-red-900/30' },
      { label: '+$18K Daily Spend', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Impact Assessment', desc: 'Additional $18,000 daily spend without proportional conversion increase', icon: 'fa-solid fa-circle-exclamation text-red-500' },
        { label: 'Affected Campaigns', desc: 'Winter Sale, Product Launch, Brand Awareness, Holiday Special, and 8 more campaigns', icon: 'fa-solid fa-chart-line text-blue-500' },
        { label: 'Timeline', desc: 'CPC spike started 6 hours ago, trending upward rapidly', icon: 'fa-solid fa-clock text-orange-500' }
      ],
      actions: [
        { label: 'Adjust Bids Now', icon: 'fa-solid fa-sliders', customClass: 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700' }
      ]
    }
  },
  {
    id: 'signal-2',
    type: 'WARNING',
    time: '35 min ago',
    title: 'Low CTR Alert',
    description: '8 ad groups showing CTR below 1% - creative refresh recommended',
    severityColor: 'bg-orange-500',
    impactValue: 'Quality Score Drop',
    impactLabel: 'Status',
    tags: [
      { label: '8 Ad Groups', className: 'bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400 border border-orange-200 dark:border-orange-900/30' },
      { label: 'Quality Score Drop', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Performance Metrics', desc: 'Average CTR of 0.7% vs industry benchmark of 2.1%', icon: 'fa-solid fa-eye text-orange-500' },
        { label: 'Quality Score Impact', desc: 'Quality scores declining from 7/10 to 5/10 over past week', icon: 'fa-solid fa-star text-blue-500' },
        { label: 'Recommended Actions', desc: 'Test new ad copy, update visuals, and refine targeting parameters', icon: 'fa-solid fa-lightbulb text-green-500' }
      ],
      actions: [
        { label: 'Update Creatives', icon: 'fa-solid fa-pen', customClass: 'bg-orange-600 text-white hover:bg-orange-700 dark:bg-orange-600 dark:hover:bg-orange-700' }
      ]
    }
  },
  {
    id: 'signal-3',
    type: 'INSIGHT',
    time: '2 hours ago',
    title: 'Budget Optimization Opportunity',
    description: 'Reallocate $24K from underperforming to high-ROAS campaigns',
    severityColor: 'bg-blue-500',
    impactValue: '35%',
    impactLabel: 'Potential',
    tags: [
      { label: '+35% ROAS Potential', className: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 border border-blue-200 dark:border-blue-900/30' },
      { label: '5 Campaigns', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Budget Reallocation', desc: 'Move $24K from 3 low-ROAS campaigns to 2 high-performers', icon: 'fa-solid fa-dollar-sign text-blue-500' },
        { label: 'Expected Outcome', desc: 'Projected 35% ROAS increase and $42K additional revenue', icon: 'fa-solid fa-chart-simple text-green-500' },
        { label: 'Implementation Timeline', desc: 'Changes can be applied immediately with 3-day ramp period', icon: 'fa-solid fa-clock text-purple-500' }
      ],
      actions: [
        { label: 'Reallocate Budget', icon: 'fa-solid fa-arrows-rotate', customClass: 'bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500' }
      ]
    }
  },
  {
    id: 'signal-4',
    type: 'OPPORTUNITY',
    time: '4 hours ago',
    title: 'High-Performing Keywords',
    description: '18 keywords with exceptional conversion rates - scale up investment',
    severityColor: 'bg-green-500',
    impactValue: '6.8%',
    impactLabel: 'CVR',
    tags: [
      { label: '6.8% CVR Average', className: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 border border-green-200 dark:border-green-900/30' },
      { label: '+$28K Revenue Opp', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Performance Metrics', desc: 'These 18 keywords converting at 6.8% vs campaign average of 3.2%', icon: 'fa-solid fa-rocket text-green-500' },
        { label: 'Revenue Opportunity', desc: 'Increasing bids by 30% could generate additional $28K in monthly revenue', icon: 'fa-solid fa-money-bill-trend-up text-blue-500' },
        { label: 'Expansion Potential', desc: 'Identify similar keyword variations for additional growth', icon: 'fa-solid fa-magnifying-glass text-purple-500' }
      ],
      actions: [
        { label: 'Increase Investment', icon: 'fa-solid fa-plus', customClass: 'bg-green-600 text-white hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700' }
      ]
    }
  }
];

export const adsWatchlist = [
  {
    id: 'win-sale-2024',
    title: 'Winter Sale Campaign',
    sku: 'Google Ads',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/829ed95905-98415edd6aab0bba6e05.png',
    status: 'HIGH CPC',
    statusColor: 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30',
    stock: '$4.28',
    velocity: '2.8x',
    progress: 85,
    progressColor: 'bg-red-500',
    subtext: 'Budget: 85% depleted',
    metricLabel1: 'Current CPC',
    metricLabel2: 'ROAS'
  },
  {
    id: 'prod-launch-01',
    title: 'Product Launch',
    sku: 'Facebook Ads',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/a92a4ffb64-d9b6565e03e56b627c33.png',
    status: 'LOW CTR',
    statusColor: 'bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-900/30',
    stock: '0.8%',
    velocity: '3.2x',
    progress: 38,
    progressColor: 'bg-orange-500',
    subtext: 'Below industry average',
    metricLabel1: 'CTR',
    metricLabel2: 'ROAS'
  },
  {
    id: 'brand-aware-01',
    title: 'Brand Awareness',
    sku: 'Amazon Ads',
    image: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/a500720697-b057d7260ef8941e1df2.png',
    status: 'STRONG',
    statusColor: 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-900/30',
    stock: '4.2%',
    velocity: '6.8x',
    progress: 92,
    progressColor: 'bg-green-500',
    subtext: 'Excellent performance',
    metricLabel1: 'CTR',
    metricLabel2: 'ROAS'
  }
];

export const adSpendTrends = [
  { day: 'Mon', google: 15200, facebook: 12400, amazon: 8200 },
  { day: 'Tue', google: 16800, facebook: 13200, amazon: 8800 },
  { day: 'Wed', google: 18200, facebook: 14800, amazon: 9400 },
  { day: 'Thu', google: 17500, facebook: 13900, amazon: 9100 },
  { day: 'Fri', google: 19200, facebook: 15200, amazon: 9800 },
  { day: 'Sat', google: 20500, facebook: 16100, amazon: 10200 },
  { day: 'Sun', google: 16800, facebook: 14200, amazon: 8900 },
];

export const platformDistribution = [
  { name: 'Google Ads', value: 52000, color: '#0A52E7', percentage: '42%', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-900/30' },
  { name: 'Facebook Ads', value: 44000, color: '#1D63FF', percentage: '35%', bg: 'bg-blue-100 dark:bg-blue-900/20', border: 'border-blue-300 dark:border-blue-900/40' },
  { name: 'Amazon Ads', value: 28000, color: '#2E4CB9', percentage: '23%', bg: 'bg-indigo-50 dark:bg-indigo-900/10', border: 'border-indigo-200 dark:border-indigo-900/30' },
];

export const platformMetrics = [
  {
    name: 'Google Ads',
    type: 'Search & Display',
    status: 'TOP PERFORMER',
    roas: '5.2x',
    ctr: '3.8%',
    cvr: '4.2%',
    progress: 87,
    color: 'bg-indigo-600',
    gradient: 'from-indigo-50 to-indigo-100',
    border: 'border-indigo-200'
  },
  {
    name: 'Facebook Ads',
    type: 'Facebook & Instagram',
    status: 'STRONG',
    roas: '4.6x',
    ctr: '2.4%',
    cvr: '3.1%',
    progress: 76,
    color: 'bg-sky-600',
    gradient: 'from-sky-50 to-sky-100',
    border: 'border-sky-200'
  },
  {
    name: 'Amazon Ads',
    type: 'Sponsored Products',
    status: 'GROWING',
    roas: '4.2x',
    ctr: '1.8%',
    cvr: '2.6%',
    progress: 68,
    color: 'bg-amber-600',
    gradient: 'from-amber-50 to-amber-100',
    border: 'border-amber-200'
  }
];

export const campaignComparisonData = [
  { name: 'Winter Sale', ctr: 3.8, roas: 2.8, cvr: 2.8, spend: 42000, impressions: 1250000, revenue: 117600 },
  { name: 'Product Launch', ctr: 2.4, roas: 3.2, cvr: 3.1, spend: 28000, impressions: 980000, revenue: 89600 },
  { name: 'Brand Awareness', ctr: 4.2, roas: 6.8, cvr: 4.2, spend: 18000, impressions: 750000, revenue: 122400 },
  { name: 'Holiday Special', ctr: 3.1, roas: 4.5, cvr: 3.5, spend: 22000, impressions: 920000, revenue: 99000 },
  { name: 'Flash Sale', ctr: 2.9, roas: 3.9, cvr: 2.6, spend: 14000, impressions: 680000, revenue: 54600 },
];

export const adsAnomalies = [
  {
    id: '1',
    ref: '#ADS-5421',
    title: 'Severe CPC Inflation',
    description: '12 campaigns experiencing 40%+ CPC increase without proportional conversion gains',
    type: 'CRITICAL',
    category: 'CRITICAL',
    time: '15 min ago',
    icon: 'fa-solid fa-triangle-exclamation',
    iconColor: 'text-red-600',
    bgColor: 'bg-red-100',
    tags: ['12 Campaigns Affected'],
    details: {
      rootCause: 'Additional $18,000 daily spend without proportional conversion increase. This represents a 42% efficiency loss.',
      resolution: 'Reduce bids by 20-30% and pause low-quality keywords. Review competitor activity to identify market shifts.',
      risks: 'Potential reduction in overall impression share if bids are cut too drastically across high-intent keywords.',
      actionLabel: 'Adjust Bids Now',
      actionIcon: 'fa-solid fa-sliders',
      actionColor: 'bg-red-600'
    }
  },
  {
    id: '2',
    ref: '#ADS-5420',
    title: 'Ad Fatigue Detected',
    description: '8 ad groups showing declining CTR and increasing CPC - creative refresh needed',
    type: 'HIGH',
    category: 'HIGH',
    time: '42 min ago',
    icon: 'fa-solid fa-eye-slash',
    iconColor: 'text-orange-600',
    bgColor: 'bg-orange-100',
    tags: ['Quality Score Declining'],
    details: {
      rootCause: 'Average CTR declined from 2.4% to 0.8% over 14 days. Quality scores dropping from 7/10 to 5/10 due to high user frequency.',
      resolution: 'Refresh ad copy and update visual assets. Launch A/B tests with new headlines and CTA variations.',
      risks: 'Ad group learning phase reset when making significant creative changes.',
      actionLabel: 'Update Creatives',
      actionIcon: 'fa-solid fa-pen',
      actionColor: 'bg-orange-600'
    }
  },
  {
    id: '3',
    ref: '#ADS-5419',
    title: 'Budget Depletion Alert',
    description: 'Campaign "Product Launch" will exhaust monthly budget in 2 days at current pace',
    type: 'MEDIUM',
    category: 'MEDIUM',
    time: '2 hours ago',
    icon: 'fa-solid fa-wallet',
    iconColor: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    tags: ['85% Budget Used'],
    details: {
      rootCause: '$25,500 spent of $30,000 monthly budget (85%). Current daily spend is $2,250 which is exceeding the allocated daily cap.',
      resolution: 'Increase monthly budget or reduce daily spend cap. Prioritize high-performing keywords to extend remaining budget.',
      risks: 'Paused campaigns during peak period may result in missed revenue opportunities.',
      actionLabel: 'Adjust Budget',
      actionIcon: 'fa-solid fa-sliders',
      actionColor: 'bg-yellow-600'
    }
  },
  {
    id: '4',
    ref: '#ADS-5418',
    title: 'Conversion Rate Drop',
    description: 'Facebook campaign showing 35% conversion rate decline over 48 hours',
    type: 'CRITICAL',
    category: 'CRITICAL',
    time: '4 hours ago',
    icon: 'fa-solid fa-chart-line',
    iconColor: 'text-red-600',
    bgColor: 'bg-red-100',
    tags: ['-35% Conversions'],
    details: {
      rootCause: 'CVR dropped from 4.8% to 3.1% in 48 hours. Projected monthly revenue loss is $12.4K. Likely cause identified as landing page latency.',
      resolution: 'Check landing page status and verify tracking pixel integrity. Review recent creative changes and audience targeting.',
      risks: 'Extended downtime on tracking or landing pages will compound the revenue loss.',
      actionLabel: 'Investigate Issue',
      actionIcon: 'fa-solid fa-magnifying-glass',
      actionColor: 'bg-red-600'
    }
  }
];

export const adsRecommendations = [
  {
    id: '1',
    title: 'Reduce Bids on Low-Performing Keywords',
    description: 'Lower bids by 25% on 18 keywords with CVR below 1.5% to save $4.2K monthly',
    type: 'BID OPTIMIZATION',
    category: 'OPTIMIZATION',
    impactValue: 'High',
    impactLabel: 'Impact',
    time: 'Recent',
    stats: [
      { label: 'Potential Savings', value: '$4.2K', sub: 'per month' },
      { label: 'Keywords', value: '18', sub: 'Low CVR' }
    ],
    icon: 'fa-solid fa-sliders',
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-100',
    details: {
      rootCause: 'Historical data shows these keywords have consistently high spend but low conversion intent. CPA is 3x higher than average.',
      resolution: 'Reduce bids by 25% and relocate the savings to keywords with CVR > 4.5%.',
      risks: 'Loss of volume on broad-match terms that might be assisting other conversions.',
      actionLabel: 'Apply Bid Changes',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-blue-600'
    }
  },
  {
    id: '2',
    title: 'Shift Budget to High-ROAS Campaigns',
    description: 'Move $24K from underperforming to top 3 campaigns for 35% ROAS increase',
    type: 'BUDGET REALLOCATION',
    category: 'BUDGET',
    impactValue: '+35%',
    impactLabel: 'ROAS Uplift',
    time: 'Recent',
    stats: [
      { label: 'Budget Move', value: '$24K', sub: 'Reallocation' },
      { label: 'Projected ROAS', value: '6.2x', sub: 'on top ads' }
    ],
    icon: 'fa-solid fa-arrows-rotate',
    iconColor: 'text-green-600',
    bgColor: 'bg-green-100',
    details: {
      rootCause: 'Three campaigns are currently delivering >6.0x ROAS while others are below 2.0x. Efficiency is suboptimal.',
      resolution: 'Scale top performers by 15% wallet share while reducing bottom-tier budget caps.',
      risks: 'Scaling Winners too fast may lead to diminishing marginal returns.',
      actionLabel: 'Confirm Reallocation',
      actionIcon: 'fa-solid fa-arrows-rotate',
      actionColor: 'bg-green-600'
    }
  },
  {
    id: '3',
    title: 'Update Ad Creatives for Fatigued Ads',
    description: 'Refresh 8 ad groups showing declining CTR to improve quality scores',
    type: 'CREATIVE REFRESH',
    category: 'CREATIVE',
    impactValue: 'Medium',
    impactLabel: 'Impact',
    time: 'Recent',
    stats: [
      { label: 'Target Groups', value: '8', sub: 'Active groups' },
      { label: 'Exp. CTR Gain', value: '+1.2%', sub: 'vs current' }
    ],
    icon: 'fa-solid fa-pen',
    iconColor: 'text-purple-600',
    bgColor: 'bg-purple-100',
    details: {
      rootCause: 'Ads in these groups have reached high frequency levels. Users are no longer engaging, leading to higher CPCs.',
      resolution: 'Deploy new visual assets and copy variations. Refresh landing page hero sections.',
      risks: 'Quality Score reset might temporarily increase CPC further.',
      actionLabel: 'Refresh Creatives',
      actionIcon: 'fa-solid fa-pen',
      actionColor: 'bg-purple-600'
    }
  },
   {
    id: '4',
    title: 'Shift Budget to High-ROAS Campaigns',
    description: 'Move $24K from underperforming to top 3 campaigns for 35% ROAS increase',
    type: 'BUDGET REALLOCATION',
    category: 'BUDGET',
    impactValue: '+35%',
    impactLabel: 'ROAS Uplift',
    time: 'Recent',
    stats: [
      { label: 'Budget Move', value: '$24K', sub: 'Reallocation' },
      { label: 'Projected ROAS', value: '6.2x', sub: 'on top ads' }
    ],
    icon: 'fa-solid fa-arrows-rotate',
    iconColor: 'text-green-600',
    bgColor: 'bg-green-100',
    details: {
      rootCause: 'Three campaigns are currently delivering >6.0x ROAS while others are below 2.0x. Efficiency is suboptimal.',
      resolution: 'Scale top performers by 15% wallet share while reducing bottom-tier budget caps.',
      risks: 'Scaling Winners too fast may lead to diminishing marginal returns.',
      actionLabel: 'Confirm Reallocation',
      actionIcon: 'fa-solid fa-arrows-rotate',
      actionColor: 'bg-green-600'
    }
  },
];
