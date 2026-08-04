export const cashStats = [
  { title: "Total Cash Balance", value: "$286K", change: "+8.2%", trend: "up", isPositive: true, subtext: "Across all accounts" },
  { title: "Cash Inflow", value: "$142K", change: "+12%", trend: "up", isPositive: true, subtext: "30-day total income" },
  { title: "Cash Outflow", value: "$118K", change: "-5%", trend: "down", isPositive: false, subtext: "30-day total expenses" },
  { title: "Net Cash Flow", value: "$24K", change: "+38.2%", trend: "up", isPositive: true, subtext: "30-day net gain" },
  { title: "Payouts Pending", value: "$24.8K", change: "3 days", trend: "up", isPositive: true, subtext: "Next settlement" },
  { title: "Working Capital", value: "$142K", change: "+$8K", trend: "up", isPositive: true, subtext: "Current liquidity" },
  { title: "Cash Conv. Cycle", value: "18 days", change: "-2d", trend: "down", isPositive: true, subtext: "Cycle efficiency" },
  { title: "Fees % Revenue", value: "19.2%", change: "+1.8%", trend: "up", isPositive: false, subtext: "Profitability leak" },
  { title: "Dead Inventory $", value: "$22.8K", change: "+$3.4K", trend: "up", isPositive: false, subtext: "Capital tied up" }
];

export const cashIntel = [
  {
    id: 'signal-1',
    type: 'CRITICAL',
    time: '5 min ago',
    title: 'Low Cash Balance Alert',
    description: 'Operating cash balance dropped below minimum threshold - immediate action required',
    severityColor: 'bg-cb-900',
    impactValue: '',
    impactLabel: '',
    tags: [
      { label: 'Below $50K Threshold', className: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 border border-blue-200 dark:border-blue-900/30' },
      { label: 'Operating Account', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Impact Assessment', desc: 'Current balance of $42,800 is $7,200 below minimum operating threshold', icon: 'fa-solid fa-circle-exclamation text-cb-900' },
        { label: 'Recommended Actions', desc: 'Transfer funds from savings or accelerate receivables collection', icon: 'fa-solid fa-chart-line text-cb-700' },
        { label: 'Timeline', desc: 'Balance declining steadily over past 72 hours', icon: 'fa-solid fa-clock text-cb-400' }
      ],
      actions: [
        { label: 'Transfer Funds Now', icon: 'fa-solid fa-arrows-rotate', customClass: 'bg-cb-900 text-white hover:bg-blue-900 dark:bg-blue-950 dark:hover:bg-blue-900' }
      ]
    }
  },
  {
    id: 'signal-2',
    type: 'WARNING',
    time: '28 min ago',
    title: 'Overdue Payments Detected',
    description: '5 vendor payments totaling $38,200 are past due date - potential late fees',
    severityColor: 'bg-cb-400',
    impactValue: '',
    impactLabel: '',
    tags: [
      { label: '5 Overdue Payments', className: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900/30' },
      { label: '$38.2K Total', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Payment Details', desc: '5 payments ranging from 3 to 12 days overdue', icon: 'fa-solid fa-file-invoice-dollar text-cb-400' },
        { label: 'Late Fee Risk', desc: 'Potential late fees up to $1,910 if not paid within 48 hours', icon: 'fa-solid fa-exclamation-triangle text-cb-900' },
        { label: 'Vendor Relations', desc: 'May impact credit terms and relationships with key suppliers', icon: 'fa-solid fa-handshake text-cb-700' }
      ],
      actions: [
        { label: 'Process Payments', icon: 'fa-solid fa-money-check', customClass: 'bg-cb-400 text-white hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700' }
      ]
    }
  },
  {
    id: 'signal-3',
    type: 'INSIGHT',
    time: '1 hour ago',
    title: 'Large Receivable Expected',
    description: '$85K payment from major client expected to clear within 24 hours',
    severityColor: 'bg-blue-500',
    impactValue: '',
    impactLabel: '',
    tags: [
      { label: '+$85K Incoming', className: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 border border-green-200 dark:border-green-900/30' },
      { label: 'Enterprise Client', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Expected Timing', desc: 'Wire transfer initiated, expected to clear by tomorrow 2 PM EST', icon: 'fa-solid fa-calendar-check text-green-500' },
        { label: 'Balance Impact', desc: 'Will bring operating balance to $127,800, well above minimum threshold', icon: 'fa-solid fa-chart-simple text-blue-500' },
        { label: 'Planning Opportunity', desc: 'Consider allocating surplus to high-priority payables or investments', icon: 'fa-solid fa-lightbulb text-purple-500' }
      ],
      actions: [
        { label: 'Plan Allocation', icon: 'fa-solid fa-list-check', customClass: 'bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500' }
      ]
    }
  },
  {
    id: 'signal-4',
    type: 'OPPORTUNITY',
    time: '3 hours ago',
    title: 'Early Payment Discount Available',
    description: 'Save $2,400 by paying 3 invoices early - 2% discount offered by vendors',
    severityColor: 'bg-green-500',
    impactValue: '',
    impactLabel: '',
    tags: [
      { label: '$2.4K Savings', className: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 border border-green-200 dark:border-green-900/30' },
      { label: '3 Vendors', className: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-300' }
    ],
    details: {
      analysisList: [
        { label: 'Discount Details', desc: '3 vendors offering 2% discount for payment within 5 days', icon: 'fa-solid fa-piggy-bank text-green-500' },
        { label: 'ROI Analysis', desc: 'Annualized return of 14.6% on early payment - excellent opportunity', icon: 'fa-solid fa-calculator text-blue-500' },
        { label: 'Time Sensitivity', desc: 'Discount window closes in 5 days - act soon to capture savings', icon: 'fa-solid fa-clock text-orange-500' }
      ],
      actions: [
        { label: 'Claim Discount', icon: 'fa-solid fa-bolt', customClass: 'bg-green-600 text-white hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700' }
      ]
    }
  }
];

export const cashWatchlist = [
  {
    id: 'acct-operating',
    title: 'Operating Account',
    account: 'Chase Business',
    status: 'LOW',
    statusColor: 'bg-cb-900 text-white',
    bgGradient: 'from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10',
    borderColor: 'border-blue-200 dark:border-blue-900/30',
    icon: 'fa-building-columns',
    iconColor: 'text-cb-700',
    balance: '$42.8K',
    trend: '-12.4%',
    trendColor: 'text-gray-900 dark:text-slate-100',
    trendLabel: '7-Day Trend',
    progress: 42,
    progressColor: 'bg-cb-900',
    message: 'Below minimum threshold'
  },
  {
    id: 'acct-savings',
    title: 'Savings Account',
    account: 'High-Yield Savings',
    status: 'HEALTHY',
    statusColor: 'bg-cb-600 text-white',
    bgGradient: 'from-blue-50 to-cyan-50 dark:from-blue-900/10 dark:to-cyan-900/10',
    borderColor: 'border-blue-200 dark:border-blue-900/30',
    icon: 'fa-piggy-bank',
    iconColor: 'text-cb-600',
    balance: '$186K',
    trend: '4.5%',
    trendColor: 'text-gray-900 dark:text-slate-100',
    trendLabel: 'APY',
    progress: 93,
    progressColor: 'bg-cb-600',
    message: 'Excellent reserve position'
  },
  {
    id: 'acct-payroll',
    title: 'Payroll Account',
    account: 'Payroll Reserve',
    status: 'FUNDED',
    statusColor: 'bg-cb-700 text-white',
    bgGradient: 'from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10',
    borderColor: 'border-blue-200 dark:border-blue-900/30',
    icon: 'fa-users',
    iconColor: 'text-cb-700',
    balance: '$57.2K',
    trend: '5 days',
    trendColor: 'text-gray-900 dark:text-slate-100',
    trendLabel: 'Next Run',
    progress: 78,
    progressColor: 'bg-cb-700',
    message: 'Ready for next cycle'
  }
];

export const cashAnomalies = [
  {
    id: '1',
    ref: '#CASH-8421',
    title: 'Critical Cash Balance Alert',
    description: 'Operating account balance below minimum threshold - immediate liquidity action required',
    type: 'CRITICAL',
    category: 'CRITICAL',
    time: '5 min ago',
    icon: 'fa-solid fa-triangle-exclamation',
    iconColor: 'text-red-600',
    bgColor: 'bg-red-100',
    tags: ['$7.2K Below Target'],
    details: {
      rootCause: 'Current balance of $42,800 is $7,200 below minimum operating threshold due to consecutive large payments clearing.',
      resolution: 'Transfer funds from savings or accelerate receivables collection. Halt non-essential disbursements.',
      risks: 'Potential overdrafts on incoming debits and violation of cash covenants.',
      actionLabel: 'Transfer Funds',
      actionIcon: 'fa-solid fa-arrows-rotate',
      actionColor: 'bg-red-600'
    }
  },
  {
    id: '2',
    ref: '#CASH-8420',
    title: 'Overdue Payment Accumulation',
    description: '5 vendor payments totaling $38.2K past due - potential late fees and credit impact',
    type: 'HIGH',
    category: 'HIGH',
    time: '28 min ago',
    icon: 'fa-solid fa-file-invoice',
    iconColor: 'text-orange-600',
    bgColor: 'bg-orange-100',
    tags: ['Late Fee Risk: $1.9K'],
    details: {
      rootCause: '5 payments ranging from 3 to 12 days overdue are awaiting secondary authorization.',
      resolution: 'Process payments within 48 hours to avoid $1,910 in late fees.',
      risks: 'Late fees will be assessed if not paid within 48 hours, damaging vendor relationships.',
      actionLabel: 'Process Payments',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-orange-600'
    }
  },
  {
    id: '3',
    ref: '#CASH-8419',
    title: 'Delayed Receivables',
    description: '8 invoices totaling $52K are 15+ days past due date - collection action needed',
    type: 'MEDIUM',
    category: 'MEDIUM',
    time: '1 hour ago',
    icon: 'fa-solid fa-clock',
    iconColor: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    tags: ['DSO: 42 days'],
    details: {
      rootCause: 'Days Sales Outstanding increased to 42 days due to client delays in processing approvals.',
      resolution: 'Implement collection calls and payment plans with clients immediately.',
      risks: 'Negative impact on near-term cash flow and working capital.',
      actionLabel: 'Follow Up Now',
      actionIcon: 'fa-solid fa-phone',
      actionColor: 'bg-yellow-600'
    }
  },
  {
    id: '4',
    ref: '#CASH-8418',
    title: 'Burn Rate Acceleration',
    description: 'Cash burn rate increased 42% week-over-week - runway analysis required',
    type: 'CRITICAL',
    category: 'CRITICAL',
    time: '3 hours ago',
    icon: 'fa-solid fa-chart-line',
    iconColor: 'text-red-600',
    bgColor: 'bg-red-100',
    tags: ['Runway: 4.2 months'],
    details: {
      rootCause: 'Unplanned operating expenses combined with delayed incoming wire transfers.',
      resolution: 'Review and reduce discretionary spending immediately.',
      risks: 'Current runway reduced to 4.2 months at current burn rate.',
      actionLabel: 'Analyze Spend',
      actionIcon: 'fa-solid fa-magnifying-glass',
      actionColor: 'bg-red-600'
    }
  },
  {
    id: '5',
    ref: '#CASH-8417',
    title: 'Unusual Transfer Pattern',
    description: 'Multiple large transfers between accounts detected - verify for accuracy',
    type: 'MEDIUM',
    category: 'MEDIUM',
    time: '5 hours ago',
    icon: 'fa-solid fa-money-bill-transfer',
    iconColor: 'text-purple-600',
    bgColor: 'bg-purple-100',
    tags: ['6 Transfers: $124K'],
    details: {
      rootCause: '6 transfers totaling $124K between accounts in 24 hours detected outside standard thresholds.',
      resolution: 'Verify all transfers are authorized, accurate, and map correctly to treasury policies.',
      risks: 'Potential compliance or unauthorized access risk if not properly verified.',
      actionLabel: 'Review Transfers',
      actionIcon: 'fa-solid fa-shield-halved',
      actionColor: 'bg-purple-600'
    }
  },
  {
    id: '6',
    ref: '#CASH-8416',
    title: 'Strong Collection Performance',
    description: 'Collections improved 28% this week - excellent AR management',
    type: 'POSITIVE',
    category: 'POSITIVE',
    time: '7 hours ago',
    icon: 'fa-solid fa-rocket',
    iconColor: 'text-green-600',
    bgColor: 'bg-green-100',
    tags: ['+28% Collections'],
    details: {
      rootCause: 'New automated dunning emails resulted in significantly faster invoice fulfillment.',
      resolution: 'Continue current collection strategies and consider scaling the automation to other tiers.',
      risks: 'None - Positive development.',
      actionLabel: 'View Report',
      actionIcon: 'fa-solid fa-file-lines',
      actionColor: 'bg-green-600'
    }
  }
];

export const cashRecommendations = [
  {
    id: '1',
    title: 'Optimize Early Payment Discounts',
    description: 'Take advantage of 2% early payment discounts from 3 vendors.',
    type: 'HIGH PRIORITY',
    category: 'OPTIMIZATION',
    impactValue: 'Save $2,400',
    impactLabel: 'Impact',
    time: 'Recent',
    stats: [
      { label: 'Details', value: '3 vendors', sub: 'offering 2% discount' },
      { label: 'Timeline', value: '5 days', sub: 'window closes' }
    ],
    icon: 'fa-solid fa-lightbulb',
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-100',
    details: {
      rootCause: '3 vendors offering 2% discount for payment within 5 days.',
      resolution: 'Annualized return of 14.6% on early payment - excellent opportunity.',
      risks: 'Discount window closes in 5 days - act soon to capture savings.',
      actionLabel: 'Implement Recommendation',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-blue-600'
    }
  },
  {
    id: '2',
    title: 'Transfer Funds to Operating Account',
    description: 'Your operating balance is critically low. Transfer $15K from savings.',
    type: 'URGENT',
    category: 'URGENT',
    impactValue: 'Avoid $1,910 fees',
    impactLabel: 'Impact',
    time: 'Immediate',
    stats: [
      { label: 'Balance Issue', value: '$7.2K', sub: 'below minimum' },
      { label: 'Action', value: '$15K transfer', sub: 'required' }
    ],
    icon: 'fa-solid fa-arrows-rotate',
    iconColor: 'text-orange-600',
    bgColor: 'bg-orange-100',
    details: {
      rootCause: 'Current balance of $42,800 is $7,200 below minimum threshold.',
      resolution: 'Avoid overdraft fees and maintain banking relationship by transferring immediately.',
      risks: 'Transfer should be completed within 24 hours to avoid penalty.',
      actionLabel: 'Implement Recommendation',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-orange-600'
    }
  },
  {
    id: '3',
    title: 'Accelerate Receivables Collection',
    description: '8 invoices significantly overdue - implement collection strategies.',
    type: 'MEDIUM',
    category: 'MEDIUM',
    impactValue: 'Recover $52K',
    impactLabel: 'Impact',
    time: 'Recent',
    stats: [
      { label: 'Customers', value: '8', sub: 'outstanding' },
      { label: 'Age', value: '15+ Days', sub: 'overdue' }
    ],
    icon: 'fa-solid fa-phone',
    iconColor: 'text-purple-600',
    bgColor: 'bg-purple-100',
    details: {
      rootCause: '8 customers with invoices 15+ days overdue affecting working capital.',
      resolution: 'Improve cash flow and reduce Days Sales Outstanding through targeted collection calls.',
      risks: 'Begin collection efforts immediately for best results.',
      actionLabel: 'Implement Recommendation',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-purple-600'
    }
  },
  {
    id: '4',
    title: 'Optimize Idle Cash Investment',
    description: '$85K could earn more in higher-yield investments.',
    type: 'OPPORTUNITY',
    category: 'OPPORTUNITY',
    impactValue: '+$850/month',
    impactLabel: 'Impact',
    time: 'Recent',
    stats: [
      { label: 'Current APY', value: '4.5%', sub: 'savings' },
      { label: 'Target APY', value: '5.2%', sub: 'treasury' }
    ],
    icon: 'fa-solid fa-chart-line',
    iconColor: 'text-green-600',
    bgColor: 'bg-green-100',
    details: {
      rootCause: 'Cash sitting in 4.5% standard yield versus 5.2% treasury target.',
      resolution: 'Additional $10,200 annual income with minimal risk.',
      risks: 'Research and transfer within 2 weeks to maximize returns.',
      actionLabel: 'Implement Recommendation',
      actionIcon: 'fa-solid fa-check',
      actionColor: 'bg-green-600'
    }
  }
];

export const categoryBreakdown = [
  {
    title: 'Customer Payments',
    subtext: 'Invoices & Receivables',
    status: 'PRIMARY',
    statusColor: 'bg-cb-700 text-white',
    amount: '$98K',
    count: '42',
    avg: '$2.3K',
    progress: 69,
    progressColor: 'bg-cb-700',
    wrapperClass: 'bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 dark:from-blue-900/10 dark:to-blue-900/20 dark:border-blue-900/30'
  },
  {
    title: 'Credit Line',
    subtext: 'Business Line of Credit',
    status: 'AVAILABLE',
    statusColor: 'bg-cb-600 text-white',
    amount: '$28K',
    count: '$100K', // Using 'count' for limit for reuse
    countLabel: 'Limit',
    avg: '28%',
    avgLabel: 'Used',
    progress: 28,
    progressColor: 'bg-cb-600',
    wrapperClass: 'bg-gradient-to-br from-indigo-50 to-indigo-100 border border-indigo-200 dark:from-indigo-900/10 dark:to-indigo-900/20 dark:border-indigo-900/30'
  },
  {
    title: 'Other Income',
    subtext: 'Interest & Misc',
    status: 'PASSIVE',
    statusColor: 'bg-cb-500 text-white',
    amount: '$16K',
    count: '8',
    avg: '$2.0K',
    progress: 11,
    progressColor: 'bg-cb-500',
    wrapperClass: 'bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 dark:from-blue-900/10 dark:to-blue-900/20 dark:border-blue-900/30'
  }
];

export const cashFlowTrendData = [
  { day: 'Mon', inflow: 18, outflow: 15 },
  { day: 'Tue', inflow: 22, outflow: 18 },
  { day: 'Wed', inflow: 19, outflow: 16 },
  { day: 'Thu', inflow: 25, outflow: 17 },
  { day: 'Fri', inflow: 28, outflow: 19 },
  { day: 'Sat', inflow: 24, outflow: 16 },
  { day: 'Sun', inflow: 26, outflow: 18 }
];

export const inflowCategoryChartData = [
  { value: 98, name: 'Customer Payments', color: '#1D4ED8' },
  { value: 28, name: 'Credit Line', color: '#94A3B8' },
  { value: 16, name: 'Other Income', color: '#CBD5E1' }
];

export const paymentMetricsChartData = {
  dso: [38, 42, 45, 41, 39, 42],
  paymentTiming: [12, 15, 14, 11, 16, 13],
  collectionRate: [85, 88, 82, 86, 91, 87],
  vendorPayments: [45, 52, 48, 55, 50, 47],
  payroll: [55, 55, 58, 55, 55, 60],
  opex: [32, 35, 31, 38, 34, 30]
};

export const settlementsData = [
  { date: 'Apr 30', marketplace: 'Amazon', gross: '$12,400', fees: '$2,480', net: '$9,920', status: 'Processing', reconciliation: '✓', action: 'View' },
  { date: 'Apr 28', marketplace: 'Shopify', gross: '$5,800', fees: '$870', net: '$4,930', status: 'Settled', reconciliation: '✓', action: 'View' },
  { date: 'Apr 24', marketplace: 'Amazon', gross: '$14,200', fees: '$2,840', net: '$11,360', status: 'Settled', reconciliation: '⚠ -$320', action: 'Dispute' },
  { date: 'Apr 18', marketplace: 'Amazon', gross: '$9,800', fees: '$1,960', net: '$7,840', status: 'Settled', reconciliation: '⚠ -$540', action: 'Dispute' },
  { date: 'Apr 14', marketplace: 'Shopify', gross: '$6,200', fees: '$930', net: '$5,270', status: 'Settled', reconciliation: '✓', action: 'View' },
  { date: 'Apr 10', marketplace: 'Amazon', gross: '$11,600', fees: '$2,320', net: '$9,280', status: 'Settled', reconciliation: '⚠ -$380', action: 'Dispute' },
];

export const settlementDispositionData = [
  { name: 'Gross Sales', value: 28400, type: 'absolute' },
  { name: 'Selling Fees', value: -2840, type: 'relative' },
  { name: 'FBA Fees', value: -3400, type: 'relative' },
  { name: 'Storage', value: -280, type: 'relative' },
  { name: 'Returns', value: -420, type: 'relative' },
  { name: 'Ad Spend', value: -1200, type: 'relative' },
  { name: 'Net Deposit', value: 20260, type: 'total' },
];

export const upcomingDeposits = [
  { amount: '$48,200', source: 'Amazon · Settlement #4821', date: 'May 8', status: 'Confirmed' },
  { amount: '$32,400', source: 'Amazon · Settlement #4822', date: 'May 10', status: 'Confirmed' },
  { amount: '$18,600', source: 'Shopify · Payout', date: 'May 12', status: 'Confirmed' },
  { amount: '$28,100', source: 'Amazon · Settlement #4823', date: 'May 15', status: 'Scheduled' },
  { amount: '$15,500', source: 'Shopify · Payout', date: 'May 19', status: 'Scheduled' }
];

export const feesBreakdownData = [
  { name: 'Selling Fees', value: 54200, color: '#032C85' },
  { name: 'FBA Fees', value: 32100, color: '#01329E' },
  { name: 'Ad Spend', value: 63520, color: '#0A52E7' },
  { name: 'Other Fees', value: 8400, color: '#1D63FF' }
];

export const workingCapitalTrendData = [
  { name: 'Feb', value: 560 },
  { name: 'Mar W1', value: 575 },
  { name: 'Mar W2', value: 580 },
  { name: 'Mar W3', value: 595 },
  { name: 'Mar W4', value: 600 },
  { name: 'Apr W1', value: 610 },
  { name: 'Apr W2', value: 615 },
  { name: 'Apr W3', value: 620 },
  { name: 'Apr W4', value: 625 },
  { name: 'May W1', value: 629 }
];

export const cashFlowByPeriodData = [
  { period: 'Apr 28 – May 4', channel: 'Amazon', revenue: '$148,200', selling: '-$23,712', fba: '-$14,820', ads: '-$18,400', net: '$91,268', date: 'May 8', days: '4d' },
  { period: 'Apr 28 – May 4', channel: 'Shopify', revenue: '$56,400', selling: '-$1,974', fba: '—', ads: '-$6,200', net: '$48,226', date: 'May 7', days: '3d' },
  { period: 'Apr 21 – Apr 27', channel: 'Amazon', revenue: '$138,900', selling: '-$22,224', fba: '-$13,890', ads: '-$16,800', net: '$85,986', date: 'May 1', days: '4d' },
  { period: 'Apr 21 – Apr 27', channel: 'Shopify', revenue: '$51,200', selling: '-$1,792', fba: '—', ads: '-$5,800', net: '$43,608', date: 'Apr 30', days: '3d' }
];
