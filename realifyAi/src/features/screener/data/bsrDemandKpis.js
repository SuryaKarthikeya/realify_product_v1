/** KPI cards and their deep-dive tables for the BSRDemand tab. */
export const kpis = [
  {
    title: 'Avg BSR Rank', shortLabel: 'BSR Rank', value: '#2,145', change: '+285', isPositive: true, subtext: 'vs last month',
    chartData: [{ name: 'Jan', val: 3200 }, { name: 'Mar', val: 2900 }, { name: 'Jun', val: 2600 }, { name: 'Sep', val: 2400 }, { name: 'Dec', val: 2145 }], chartColor: '#3b82f6',
    deepDive: {
      title: 'Average BSR Rank', icon: 'fa-ranking-star',
      cards: [
        { label: 'AVG BSR', val: '#2,145', delta: '+285', color: 'text-blue-600' },
        { label: 'BEST RANK', val: '#435', delta: 'Smart Watch', color: 'text-green-600' },
        { label: 'TRACKED', val: '42', delta: 'Products', color: 'text-purple-600' },
        { label: 'TREND', val: 'Improving', delta: 'Monthly', color: 'text-blue-600' },
      ],
      tableColumns: [
        { header: 'CATEGORY', key: 'cat', bold: true },
        { header: 'AVG BSR', key: 'bsr', align: 'right', bold: true },
        { header: 'CHANGE', key: 'change', align: 'right' },
      ],
      tableData: [
        { cat: 'Electronics', bsr: '#2,145', change: '+285' },
        { cat: 'Home & Kitchen', bsr: '#3,680', change: '+156' },
        { cat: 'Sports & Outdoors', bsr: '#4,520', change: '+92' },
      ],
    },
  },
  {
    title: 'Demand Score', shortLabel: 'Demand', value: '87/100', change: '+4', isPositive: true, subtext: 'Composite demand',
    chartData: [{ name: 'Jan', val: 72 }, { name: 'Mar', val: 76 }, { name: 'Jun', val: 80 }, { name: 'Sep', val: 84 }, { name: 'Dec', val: 87 }], chartColor: '#10b981',
    deepDive: {
      title: 'Demand Score', icon: 'fa-fire',
      cards: [
        { label: 'DEMAND SCORE', val: '87/100', delta: '+4', color: 'text-green-600' },
        { label: 'HIGH DEMAND', val: '18', delta: 'Products', color: 'text-green-500' },
        { label: 'SEASONALITY', val: 'High', delta: 'Q4 peak', color: 'text-amber-600' },
        { label: 'TREND', val: 'Rising', delta: '+12% YoY', color: 'text-green-500' },
      ],
      tableColumns: [
        { header: 'PRODUCT', key: 'product', bold: true },
        { header: 'SCORE', key: 'score', align: 'right', bold: true },
        { header: 'TREND', key: 'trend', align: 'right' },
      ],
      tableData: [
        { product: 'Wireless Earbuds', score: '94', trend: 'Surging' },
        { product: 'Smart Watch', score: '91', trend: 'Stable' },
        { product: 'USB Hub', score: '83', trend: 'Growing' },
      ],
    },
  },
  {
    title: 'BSR Velocity', shortLabel: 'Velocity', value: '+1,640', change: '+8%', isPositive: true, subtext: 'Avg rank improvement',
    chartData: [{ name: 'Jan', val: 800 }, { name: 'Mar', val: 1000 }, { name: 'Jun', val: 1200 }, { name: 'Sep', val: 1450 }, { name: 'Dec', val: 1640 }], chartColor: '#8b5cf6',
    deepDive: {
      title: 'BSR Velocity', icon: 'fa-bolt',
      cards: [
        { label: 'AVG VELOCITY', val: '+1,640', delta: '+8%', color: 'text-purple-600' },
        { label: 'FASTEST', val: '+2,800', delta: 'Earbuds', color: 'text-purple-500' },
        { label: 'DECLINING', val: '4', delta: 'Products', color: 'text-red-500' },
        { label: 'TRENDING', val: '28', delta: 'Improving', color: 'text-green-500' },
      ],
      tableColumns: [
        { header: 'PRODUCT', key: 'product', bold: true },
        { header: 'VELOCITY', key: 'velocity', align: 'right', bold: true },
        { header: 'STATUS', key: 'status', align: 'right' },
      ],
      tableData: [
        { product: 'Wireless Earbuds', velocity: '+2,800', status: 'Surging' },
        { product: 'USB Hub', velocity: '+1,580', status: 'Growing' },
        { product: 'Smart Watch', velocity: 'Stable', status: 'Neutral' },
      ],
    },
  },
  {
    title: 'Demand Forecast', shortLabel: 'Forecast', value: '$448K', change: '+28%', isPositive: true, subtext: 'Q3 est. revenue',
    chartData: [{ name: 'Jan', val: 507 }, { name: 'Feb', val: 297 }, { name: 'Mar', val: 297 }, { name: 'Jun', val: 448 }, { name: 'Dec', val: 507 }], chartColor: '#f97316',
    deepDive: {
      title: 'Demand Forecast', icon: 'fa-chart-line',
      cards: [
        { label: 'Q3 FORECAST', val: '$448K', delta: '+28%', color: 'text-orange-600' },
        { label: 'Q4 FORECAST', val: '$507K', delta: '+13%', color: 'text-orange-500' },
        { label: 'CONFIDENCE', val: '88%', delta: 'High', color: 'text-green-500' },
        { label: 'SEASONAL', val: '+45%', delta: 'Q4 boost', color: 'text-orange-500' },
      ],
      tableColumns: [
        { header: 'QUARTER', key: 'qtr', bold: true },
        { header: 'FORECAST', key: 'forecast', align: 'right', bold: true },
        { header: 'VS BASELINE', key: 'delta', align: 'right' },
      ],
      tableData: [
        { qtr: 'Q1 (Jan-Mar)', forecast: '$297K', delta: '-15%' },
        { qtr: 'Q2 (Apr-Jun)', forecast: '$370K', delta: '+6%' },
        { qtr: 'Q3 (Jul-Sep)', forecast: '$448K', delta: '+28%' },
        { qtr: 'Q4 (Oct-Dec)', forecast: '$507K', delta: '+45%' },
      ],
    },
  },
];
