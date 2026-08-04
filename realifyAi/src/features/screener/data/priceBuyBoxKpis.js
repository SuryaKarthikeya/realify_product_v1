/** KPI cards and their deep-dive tables for the PriceBuyBox tab. */
export const kpis = [
  {
    title: 'Avg Price Delta', shortLabel: 'Price Delta', value: '-8.3%', change: 'Below market avg', isPositive: false,
    chartData: [{ name: 'Mon', val: -6.2 }, { name: 'Tue', val: -7.1 }, { name: 'Wed', val: -8.3 }, { name: 'Thu', val: -7.8 }, { name: 'Fri', val: -8.3 }], chartColor: '#3b82f6',
    deepDive: {
      title: 'Avg Price Delta', icon: 'fa-arrow-down',
      cards: [
        { label: 'PRICE DELTA', val: '-8.3%', delta: 'vs Market', color: 'text-blue-600' },
        { label: 'YOUR AVG', val: '$64.50', delta: 'Avg SKU', color: 'text-blue-500' },
        { label: 'MKT AVG', val: '$70.20', delta: 'Benchmark', color: 'text-blue-500' },
        { label: 'IMPACT', val: '-$5.70', delta: 'Per Unit', color: 'text-red-500' },
      ],
      tableColumns: [
        { header: 'SKU', key: 'sku', bold: true },
        { header: 'YOUR PRICE', key: 'yours', align: 'right', bold: true },
        { header: 'MKT PRICE', key: 'market', align: 'right' },
        { header: 'DELTA', key: 'delta', align: 'right' },
      ],
      tableData: [
        { sku: 'Wireless Earbuds', yours: '$42.99', market: '$47.99', delta: '-10.4%' },
        { sku: 'USB-C Hub', yours: '$29.99', market: '$32.99', delta: '-9.1%' },
        { sku: 'Smart Watch', yours: '$89.99', market: '$94.99', delta: '-5.3%' },
      ],
    },
  },
  {
    title: 'Buy Box Win Rate', shortLabel: 'Buy Box', value: '72%', change: '+5%', isPositive: true, subtext: 'vs last week',
    chartData: [{ name: 'Mon', val: 68 }, { name: 'Tue', val: 71 }, { name: 'Wed', val: 73 }, { name: 'Thu', val: 70 }, { name: 'Fri', val: 72 }], chartColor: '#6366f1',
    deepDive: {
      title: 'Buy Box Win Rate', icon: 'fa-trophy',
      cards: [
        { label: 'WIN RATE', val: '72%', delta: '+5%', color: 'text-indigo-600' },
        { label: 'PEAK', val: '94.2%', delta: 'Last Wk', color: 'text-indigo-500' },
        { label: 'LOW', val: '72.1%', delta: 'Alert', color: 'text-indigo-500' },
        { label: 'ALERTS', val: '2', delta: 'Active', color: 'text-red-500' },
      ],
      tableColumns: [
        { header: 'SKU', key: 'sku', bold: true },
        { header: 'WIN RATE', key: 'rate', align: 'right', bold: true },
        { header: 'STATUS', key: 'status', align: 'right' },
      ],
      tableData: [
        { sku: 'B09XYZ1234', rate: '92%', status: 'Stable' },
        { sku: 'B09ABC5678', rate: '42%', status: 'Lost' },
        { sku: 'B09DEF9012', rate: '88%', status: 'At Risk' },
      ],
    },
  },
  {
    title: 'Repricing Actions', shortLabel: 'Repricing', value: '24', subtext: 'Pending review', isPositive: false,
    chartData: [{ name: 'Mon', val: 18 }, { name: 'Tue', val: 22 }, { name: 'Wed', val: 19 }, { name: 'Thu', val: 25 }, { name: 'Fri', val: 24 }], chartColor: '#0ea5e9',
    deepDive: {
      title: 'Repricing Actions', icon: 'fa-sync',
      cards: [
        { label: 'PENDING', val: '24', delta: 'Review', color: 'text-sky-600' },
        { label: 'AUTO', val: '12', delta: 'Executed', color: 'text-sky-500' },
        { label: 'MANUAL', val: '8', delta: 'Required', color: 'text-sky-500' },
        { label: 'SAVED', val: '$1,240', delta: 'Revenue', color: 'text-emerald-600' },
      ],
      tableColumns: [
        { header: 'SKU', key: 'sku', bold: true },
        { header: 'ACTION', key: 'action', align: 'right', bold: true },
        { header: 'IMPACT', key: 'impact', align: 'right' },
      ],
      tableData: [
        { sku: 'Wireless Earbuds', action: 'Raise to $44.99', impact: '+$2.00' },
        { sku: 'USB-C Hub', action: 'Match at $29.99', impact: 'No change' },
        { sku: 'Smart Watch', action: 'Drop to $88.99', impact: '-$1.00' },
      ],
    },
  },
  {
    title: 'Price Alerts', shortLabel: 'Alerts', value: '12', change: 'Requires attention', isPositive: false,
    chartData: [{ name: 'Mon', val: 8 }, { name: 'Tue', val: 10 }, { name: 'Wed', val: 9 }, { name: 'Thu', val: 11 }, { name: 'Fri', val: 12 }], chartColor: '#3b82f6',
    deepDive: {
      title: 'Price Alerts', icon: 'fa-bell',
      cards: [
        { label: 'TOTAL', val: '12', delta: 'Active', color: 'text-blue-600' },
        { label: 'CRITICAL', val: '3', delta: 'Urgent', color: 'text-red-600' },
        { label: 'WARNING', val: '5', delta: 'Review', color: 'text-amber-600' },
        { label: 'INFO', val: '4', delta: 'Monitor', color: 'text-blue-500' },
      ],
      tableColumns: [
        { header: 'SKU', key: 'sku', bold: true },
        { header: 'ALERT TYPE', key: 'type', align: 'right', bold: true },
        { header: 'SEVERITY', key: 'severity', align: 'right' },
      ],
      tableData: [
        { sku: 'Wireless Earbuds', type: 'Price Drop', severity: 'Critical' },
        { sku: 'USB-C Hub', type: 'MAP Violation', severity: 'Warning' },
        { sku: 'Smart Watch', type: 'BB Opportunity', severity: 'Info' },
      ],
    },
  },
];
