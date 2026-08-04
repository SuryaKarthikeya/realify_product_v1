/** KPI cards and their deep-dive tables for the OpportunityResearch tab. */
export const kpis = [
  {
    title: 'Total Opps', shortLabel: 'Opps', value: '145', change: '+23', isPositive: true, subtext: 'vs last month',
    chartData: [{ name: 'Jan', val: 98 }, { name: 'Mar', val: 112 }, { name: 'Jun', val: 125 }, { name: 'Sep', val: 135 }, { name: 'Dec', val: 145 }], chartColor: '#8b5cf6',
    deepDive: {
      title: 'Total Opportunities', icon: 'fa-magnifying-glass-chart',
      cards: [
        { label: 'TOTAL', val: '145', delta: '+23', color: 'text-purple-600' },
        { label: 'EXCELLENT', val: '12', delta: '90+ score', color: 'text-green-600' },
        { label: 'VERY GOOD', val: '35', delta: '80-89', color: 'text-blue-600' },
        { label: 'GOOD', val: '48', delta: '70-79', color: 'text-purple-500' },
      ],
      tableColumns: [
        { header: 'CATEGORY', key: 'cat', bold: true },
        { header: 'COUNT', key: 'count', align: 'right', bold: true },
        { header: 'AVG SCORE', key: 'score', align: 'right' },
      ],
      tableData: [
        { cat: 'Home & Kitchen', count: '38', score: '87' },
        { cat: 'Sports & Outdoors', count: '32', score: '84' },
        { cat: 'Accessories', count: '29', score: '82' },
        { cat: 'Pet Supplies', count: '25', score: '79' },
        { cat: 'Luggage', count: '21', score: '76' },
      ],
    },
  },
  {
    title: 'Avg Score', shortLabel: 'Score', value: '84/100', change: '+3', isPositive: true, subtext: 'Opportunity quality',
    chartData: [{ name: 'Jan', val: 75 }, { name: 'Mar', val: 78 }, { name: 'Jun', val: 80 }, { name: 'Sep', val: 82 }, { name: 'Dec', val: 84 }], chartColor: '#3b82f6',
    deepDive: {
      title: 'Average Opportunity Score', icon: 'fa-star',
      cards: [
        { label: 'AVG SCORE', val: '84/100', delta: '+3', color: 'text-blue-600' },
        { label: 'TOP SCORE', val: '94', delta: 'Smart Home', color: 'text-green-600' },
        { label: 'ABOVE 80', val: '47', delta: 'High qual.', color: 'text-blue-500' },
        { label: 'BELOW 70', val: '18', delta: 'Review', color: 'text-amber-600' },
      ],
      tableColumns: [
        { header: 'PRODUCT', key: 'product', bold: true },
        { header: 'SCORE', key: 'score', align: 'right', bold: true },
        { header: 'STATUS', key: 'status', align: 'right' },
      ],
      tableData: [
        { product: 'Smart Home Sensors', score: '94', status: 'Excellent' },
        { product: 'Eco Yoga Mats', score: '91', status: 'Excellent' },
        { product: 'RFID Wallets', score: '88', status: 'Very Good' },
        { product: 'Bamboo Organizers', score: '86', status: 'Very Good' },
      ],
    },
  },
  {
    title: 'Avg Revenue', shortLabel: 'Revenue', value: '$99K', change: '+18%', isPositive: true, subtext: 'Per opp / month',
    chartData: [{ name: 'Jan', val: 72 }, { name: 'Mar', val: 80 }, { name: 'Jun', val: 88 }, { name: 'Sep', val: 94 }, { name: 'Dec', val: 99 }], chartColor: '#10b981',
    deepDive: {
      title: 'Average Revenue Potential', icon: 'fa-dollar-sign',
      cards: [
        { label: 'AVG REVENUE', val: '$99K/mo', delta: '+18%', color: 'text-green-600' },
        { label: 'TOP OPP.', val: '$142K', delta: 'Smart Home', color: 'text-green-500' },
        { label: 'TOTAL TAM', val: '$14.4M', delta: 'Annual', color: 'text-green-500' },
        { label: 'AVG MARGIN', val: '34%', delta: 'Avg Est.', color: 'text-green-500' },
      ],
      tableColumns: [
        { header: 'OPPORTUNITY', key: 'opp', bold: true },
        { header: 'REVENUE', key: 'revenue', align: 'right', bold: true },
        { header: 'MARGIN', key: 'margin', align: 'right' },
      ],
      tableData: [
        { opp: 'Smart Home Sensors', revenue: '$142K', margin: '42%' },
        { opp: 'RFID Wallets', revenue: '$125K', margin: '35%' },
        { opp: 'Eco Yoga Mats', revenue: '$98K', margin: '38%' },
        { opp: 'Pet Grooming Kits', revenue: '$89K', margin: '29%' },
      ],
    },
  },
  {
    title: 'Low Competition', shortLabel: 'Low Comp.', value: '67%', change: '+5%', isPositive: true, subtext: 'Of all opportunities',
    chartData: [{ name: 'Jan', val: 52 }, { name: 'Mar', val: 56 }, { name: 'Jun', val: 60 }, { name: 'Sep', val: 64 }, { name: 'Dec', val: 67 }], chartColor: '#f97316',
    deepDive: {
      title: 'Low Competition Opportunities', icon: 'fa-shield',
      cards: [
        { label: 'LOW COMP.', val: '67%', delta: '+5%', color: 'text-orange-600' },
        { label: 'VERY LOW', val: '28', delta: 'Opps', color: 'text-orange-500' },
        { label: 'MED COMP.', val: '33%', delta: 'Review', color: 'text-amber-600' },
        { label: 'AVG DENSITY', val: '0.32', delta: 'Score', color: 'text-orange-500' },
      ],
      tableColumns: [
        { header: 'LEVEL', key: 'level', bold: true },
        { header: 'COUNT', key: 'count', align: 'right', bold: true },
        { header: 'AVG DENSITY', key: 'density', align: 'right' },
      ],
      tableData: [
        { level: 'Very Low', count: '28', density: '0.18-0.24' },
        { level: 'Low', count: '69', density: '0.25-0.39' },
        { level: 'Medium', count: '32', density: '0.40-0.59' },
        { level: 'High', count: '16', density: '0.60+' },
      ],
    },
  },
];
