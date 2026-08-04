/** KPI cards and their deep-dive tables for the AssortmentGaps tab. */
export const kpis = [
  {
    title: 'Total Gaps', shortLabel: 'Gaps', value: '127', subtext: 'Across all categories', isPositive: false,
    chartData: [{ name: 'Jan', val: 145 }, { name: 'Mar', val: 138 }, { name: 'Jun', val: 132 }, { name: 'Sep', val: 129 }, { name: 'Dec', val: 127 }], chartColor: '#f97316',
    deepDive: {
      title: 'Total Gaps', icon: 'fa-exclamation-triangle',
      cards: [
        { label: 'TOTAL GAPS', val: '127', delta: 'All Cat.', color: 'text-orange-600' },
        { label: 'HIGH PRI.', val: '43', delta: 'Urgent', color: 'text-red-600' },
        { label: 'MED PRI.', val: '56', delta: 'Review', color: 'text-amber-600' },
        { label: 'LOW PRI.', val: '28', delta: 'Monitor', color: 'text-orange-500' },
      ],
      tableColumns: [
        { header: 'CATEGORY', key: 'cat', bold: true },
        { header: 'GAPS', key: 'gaps', align: 'right', bold: true },
        { header: 'PRIORITY', key: 'priority', align: 'right' },
      ],
      tableData: [
        { cat: 'Electronics', gaps: '48', priority: 'Critical' },
        { cat: 'Home & Kitchen', gaps: '34', priority: 'High' },
        { cat: 'Sports & Outdoors', gaps: '28', priority: 'High' },
        { cat: 'Toys & Games', gaps: '17', priority: 'Medium' },
      ],
    },
  },
  {
    title: 'High Priority', shortLabel: 'Priority', value: '43', change: '+12', isPositive: false, subtext: 'Requires action',
    chartData: [{ name: 'Jan', val: 28 }, { name: 'Mar', val: 33 }, { name: 'Jun', val: 38 }, { name: 'Sep', val: 40 }, { name: 'Dec', val: 43 }], chartColor: '#ef4444',
    deepDive: {
      title: 'High Priority Gaps', icon: 'fa-fire',
      cards: [
        { label: 'HIGH PRI.', val: '43', delta: '+12', color: 'text-red-600' },
        { label: 'IMMEDIATE', val: '28', delta: 'Action Req.', color: 'text-red-500' },
        { label: 'REV. RISK', val: '$892K', delta: 'Annual', color: 'text-red-500' },
        { label: 'AVG SCORE', val: '87/100', delta: 'Priority', color: 'text-red-500' },
      ],
      tableColumns: [
        { header: 'CATEGORY', key: 'cat', bold: true },
        { header: 'COUNT', key: 'count', align: 'right', bold: true },
        { header: 'REV. OPP.', key: 'opp', align: 'right' },
      ],
      tableData: [
        { cat: 'Electronics', count: '18', opp: '$420K' },
        { cat: 'Home & Kitchen', count: '14', opp: '$280K' },
        { cat: 'Sports & Outdoors', count: '11', opp: '$192K' },
      ],
    },
  },
  {
    title: 'Revenue Opp', shortLabel: 'Rev Opp', value: '$1.8M', change: '+15%', isPositive: true, subtext: 'Annual potential',
    chartData: [{ name: 'Jan', val: 1.4 }, { name: 'Mar', val: 1.5 }, { name: 'Jun', val: 1.6 }, { name: 'Sep', val: 1.7 }, { name: 'Dec', val: 1.8 }], chartColor: '#22c55e',
    deepDive: {
      title: 'Revenue Opportunity', icon: 'fa-dollar-sign',
      cards: [
        { label: 'TOTAL OPP.', val: '$1.8M', delta: '+15%', color: 'text-green-600' },
        { label: 'QUICK WINS', val: '$420K', delta: 'Fast Fill', color: 'text-green-500' },
        { label: 'HIGH VALUE', val: '$980K', delta: 'Top 20%', color: 'text-green-500' },
        { label: 'TIMELINE', val: '6 months', delta: 'To Fill', color: 'text-green-500' },
      ],
      tableColumns: [
        { header: 'OPPORTUNITY', key: 'opp', bold: true },
        { header: 'VALUE', key: 'value', align: 'right', bold: true },
        { header: 'EFFORT', key: 'effort', align: 'right' },
      ],
      tableData: [
        { opp: 'Electronics Expansion', value: '$420K', effort: 'Medium' },
        { opp: 'Home & Kitchen', value: '$340K', effort: 'Low' },
        { opp: 'Sports & Outdoors', value: '$280K', effort: 'Medium' },
        { opp: 'Seasonal Products', value: '$760K', effort: 'High' },
      ],
    },
  },
  {
    title: 'Avg Fill Rate', shortLabel: 'Fill Rate', value: '73%', subtext: 'vs cat avg 85%', isPositive: false,
    chartData: [{ name: 'Jan', val: 68 }, { name: 'Mar', val: 70 }, { name: 'Jun', val: 71 }, { name: 'Sep', val: 72 }, { name: 'Dec', val: 73 }], chartColor: '#3b82f6',
    deepDive: {
      title: 'Avg Fill Rate', icon: 'fa-chart-simple',
      cards: [
        { label: 'YOUR RATE', val: '73%', delta: 'vs 85% avg', color: 'text-blue-600' },
        { label: 'CAT AVG', val: '85%', delta: 'Benchmark', color: 'text-blue-500' },
        { label: 'GAP', val: '-12%', delta: 'To Close', color: 'text-red-500' },
        { label: 'BEST CAT.', val: '82%', delta: 'Electronics', color: 'text-blue-500' },
      ],
      tableColumns: [
        { header: 'CATEGORY', key: 'cat', bold: true },
        { header: 'FILL RATE', key: 'rate', align: 'right', bold: true },
        { header: 'BENCHMARK', key: 'bench', align: 'right' },
      ],
      tableData: [
        { cat: 'Electronics', rate: '82%', bench: '88%' },
        { cat: 'Home & Kitchen', rate: '76%', bench: '85%' },
        { cat: 'Sports', rate: '71%', bench: '83%' },
        { cat: 'Toys', rate: '65%', bench: '80%' },
      ],
    },
  },
];
