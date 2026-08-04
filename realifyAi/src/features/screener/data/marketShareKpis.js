/** KPI cards and their deep-dive tables for the MarketShare tab. */
import { trendData } from '@/features/screener/data/screenerData';

const yourBrandTrend = trendData.map(d => ({ name: d.name, val: d.yourBrand }));

export const kpis = [
  {
    title: 'Your Market Share', shortLabel: 'Mkt Share', value: '18.4%', change: '+2.1% vs last month', isPositive: true,
    chartData: yourBrandTrend, chartColor: '#FDA4AF',
    deepDive: {
      title: 'Your Market Share', icon: 'fa-chart-pie',
      cards: [
        { label: 'CURRENT', val: '18.4%', delta: '+2.1%', color: 'text-blue-600' },
        { label: 'PREV MONTH', val: '16.3%', delta: 'Baseline', color: 'text-blue-500' },
        { label: 'RANK', val: '#3', delta: 'of 47', color: 'text-purple-600' },
        { label: 'TARGET', val: '20%', delta: '+1.6% Gap', color: 'text-emerald-600' },
      ],
      tableColumns: [
        { header: 'BRAND', key: 'name', bold: true },
        { header: 'SHARE', key: 'share', align: 'right', bold: true },
        { header: 'RANK', key: 'rank', align: 'right' },
        { header: 'REVENUE', key: 'revenue', align: 'right' },
      ],
      tableData: [
        { name: 'Market Leader', share: '28.7%', rank: '#1', revenue: '$4.3M' },
        { name: 'TechMaster Pro', share: '22.3%', rank: '#2', revenue: '$3.4M' },
        { name: 'Your Brand', share: '18.4%', rank: '#3', revenue: '$2.8M' },
        { name: 'EliteGadgets', share: '14.8%', rank: '#4', revenue: '$2.2M' },
        { name: 'Others', share: '15.8%', rank: '43 brands', revenue: '$2.4M' },
      ],
    },
  },
  {
    title: 'Category Rank', shortLabel: 'Cat Rank', value: '#3', change: '+2 ranks this month', isPositive: true, subtext: 'Out of 47 brands',
    chartData: [{ name: 'Jan', val: 5 }, { name: 'Mar', val: 4 }, { name: 'Jun', val: 4 }, { name: 'Sep', val: 3 }, { name: 'Dec', val: 3 }], chartColor: '#8b5cf6',
    deepDive: {
      title: 'Category Rank', icon: 'fa-ranking-star',
      cards: [
        { label: 'CURRENT', val: '#3', delta: 'Improved', color: 'text-purple-600' },
        { label: 'PREV QTR', val: '#5', delta: 'Last Qtr', color: 'text-purple-500' },
        { label: 'TOTAL', val: '47 brands', delta: 'In Cat.', color: 'text-purple-500' },
        { label: 'TARGET', val: '#2', delta: 'Next Goal', color: 'text-purple-500' },
      ],
      tableColumns: [
        { header: 'BRAND', key: 'name', bold: true },
        { header: 'RANK', key: 'rank', align: 'right', bold: true },
        { header: 'SHARE', key: 'share', align: 'right' },
      ],
      tableData: [
        { name: 'Market Leader', rank: '#1', share: '28.7%' },
        { name: 'TechMaster Pro', rank: '#2', share: '22.3%' },
        { name: 'Your Brand', rank: '#3', share: '18.4%' },
        { name: 'EliteGadgets', rank: '#4', share: '14.8%' },
      ],
    },
  },
  {
    title: 'Revenue Share', shortLabel: 'Revenue', value: '$2.8M', change: '+12% MoM', isPositive: true,
    chartData: [{ name: 'Jan', val: 2.1 }, { name: 'Mar', val: 2.2 }, { name: 'Jun', val: 2.4 }, { name: 'Sep', val: 2.6 }, { name: 'Dec', val: 2.8 }], chartColor: '#10b981',
    deepDive: {
      title: 'Revenue Share', icon: 'fa-dollar-sign',
      cards: [
        { label: 'REVENUE', val: '$2.8M', delta: '+12% MoM', color: 'text-emerald-600' },
        { label: 'CATEGORY', val: '$15.2M', delta: 'Market', color: 'text-emerald-500' },
        { label: 'SHARE %', val: '18.4%', delta: 'Of Cat.', color: 'text-emerald-500' },
        { label: 'FORECAST', val: '$3.1M', delta: 'Next Mo.', color: 'text-emerald-500' },
      ],
      tableColumns: [
        { header: 'CHANNEL', key: 'channel', bold: true },
        { header: 'REVENUE', key: 'revenue', align: 'right', bold: true },
        { header: 'SHARE', key: 'share', align: 'right' },
      ],
      tableData: [
        { channel: 'Amazon US', revenue: '$1.96M', share: '70%' },
        { channel: 'Shopify', revenue: '$560K', share: '20%' },
        { channel: 'Walmart', revenue: '$280K', share: '10%' },
      ],
    },
  },
  {
    title: 'Growth Rate', shortLabel: 'Growth', value: '+15.2%', change: 'Year over year', isPositive: true,
    chartData: yourBrandTrend, chartColor: '#f59e0b',
    deepDive: {
      title: 'Growth Rate', icon: 'fa-chart-line',
      cards: [
        { label: 'YOY', val: '+15.2%', delta: 'Strong', color: 'text-orange-600' },
        { label: 'MOM', val: '+2.1%', delta: 'vs Last Mo.', color: 'text-orange-500' },
        { label: 'BEST MO.', val: 'Nov', delta: '19.2% Share', color: 'text-orange-500' },
        { label: 'MOMENTUM', val: 'Positive', delta: '3 Mos. Up', color: 'text-orange-500' },
      ],
      tableColumns: [
        { header: 'QUARTER', key: 'quarter', bold: true },
        { header: 'GROWTH', key: 'growth', align: 'right', bold: true },
        { header: 'SHARE', key: 'share', align: 'right' },
      ],
      tableData: [
        { quarter: 'Q1 2024', growth: '+12.1%', share: '16.5%' },
        { quarter: 'Q2 2024', growth: '+13.8%', share: '17.2%' },
        { quarter: 'Q3 2024', growth: '+14.9%', share: '18.0%' },
        { quarter: 'Q4 2024', growth: '+15.2%', share: '18.4%' },
      ],
    },
  },
];
