export const COLORS = ['#8B5CF6', '#22D3EE', '#10B981', '#F59E0B', '#3B82F6', '#F43F5E'];

export const pieData = [
  { name: 'Market Leader', value: 28.7 },
  { name: 'TechMaster Pro', value: 22.3 },
  { name: 'Your Brand', value: 18.4 },
  { name: 'EliteGadgets', value: 14.8 },
  { name: 'Others', value: 15.8 },
];

export const trendData = [
  { name: 'Jan', yourBrand: 16.2, leader: 26.5, techMaster: 20.8, elite: 15.2 },
  { name: 'Feb', yourBrand: 16.5, leader: 26.8, techMaster: 21.0, elite: 15.1 },
  { name: 'Mar', yourBrand: 16.8, leader: 27.1, techMaster: 21.2, elite: 15.0 },
  { name: 'Apr', yourBrand: 17.1, leader: 27.3, techMaster: 21.4, elite: 14.9 },
  { name: 'May', yourBrand: 17.4, leader: 27.6, techMaster: 21.6, elite: 14.8 },
  { name: 'Jun', yourBrand: 17.6, leader: 27.8, techMaster: 21.8, elite: 14.7 },
  { name: 'Jul', yourBrand: 17.9, leader: 28.0, techMaster: 22.0, elite: 14.6 },
  { name: 'Aug', yourBrand: 18.1, leader: 28.2, techMaster: 22.2, elite: 14.5 },
  { name: 'Sep', yourBrand: 18.3, leader: 28.4, techMaster: 22.4, elite: 14.6 },
  { name: 'Oct', yourBrand: 18.5, leader: 28.6, techMaster: 22.5, elite: 14.7 },
  { name: 'Nov', yourBrand: 19.2, leader: 28.8, techMaster: 22.4, elite: 14.8 },
  { name: 'Dec', yourBrand: 18.4, leader: 28.7, techMaster: 22.3, elite: 14.8 },
];

export const matrixData = [
  { name: 'Market Leader', x: 28.7, y: 22, size: 50, color: '#8B5CF6' },
  { name: 'TechMaster', x: 22.3, y: 18, size: 45, color: '#22D3EE' },
  { name: 'Your Brand', x: 18.4, y: 15, size: 40, color: '#10B981' },
  { name: 'EliteGadgets', x: 14.8, y: 5, size: 35, color: '#F59E0B' },
  { name: 'ValueMart', x: 11.6, y: 3, size: 30, color: '#3B82F6' },
  { name: 'SmartBuy', x: 9.2, y: 24, size: 25, color: '#F43F5E' },
  { name: 'BudgetTech', x: 5.4, y: -2, size: 20, color: '#64748b' },
];

export const priceTrendData7d = [
  { day: 'Mon', yourPrice: 68.50, marketAvg: 72.30, competitor: 70.10 },
  { day: 'Tue', yourPrice: 66.20, marketAvg: 70.80, competitor: 69.50 },
  { day: 'Wed', yourPrice: 62.30, marketAvg: 68.90, competitor: 67.00 },
  { day: 'Thu', yourPrice: 63.80, marketAvg: 69.50, competitor: 68.20 },
  { day: 'Fri', yourPrice: 64.50, marketAvg: 70.20, competitor: 68.90 },
  { day: 'Sat', yourPrice: 65.20, marketAvg: 71.00, competitor: 69.40 },
  { day: 'Sun', yourPrice: 67.10, marketAvg: 72.80, competitor: 71.30 },
];

export const priceTrendAnalysis7d = [
  { day: 'Day 1', yourBrand: 65, techMaster: 63 },
  { day: 'Day 2', yourBrand: 64, techMaster: 61 },
  { day: 'Day 3', yourBrand: 62, techMaster: 59 },
  { day: 'Day 4', yourBrand: 63, techMaster: 58 },
  { day: 'Day 5', yourBrand: 64, techMaster: 59 },
  { day: 'Day 6', yourBrand: 65, techMaster: 60 },
  { day: 'Day 7', yourBrand: 67, techMaster: 59 },
];

export const buyBoxCategoryData = [
  { category: 'Electronics', winRate: 75, color: '#2563eb' },
  { category: 'Home & Kitchen', winRate: 68, color: '#7c3aed' },
  { category: 'Sports', winRate: 82, color: '#16a34a' },
  { category: 'Gaming', winRate: 71, color: '#f97316' },
  { category: 'Cameras', winRate: 65, color: '#06b6d4' },
];

export const promoList = [
  { id: 1, title: 'Electronics Clearance', type: 'Flash Sale', status: 'Ends in 2h 15m', icon: 'fa-bolt', avgDiscount: '35%', sales: '$12.4K', conversion: '14.2%' },
  { id: 2, title: 'Buy 2 Get 15% Off', type: 'Bundle Deal', status: 'Active', icon: 'fa-gift', avgDiscount: '15%', sales: '$8.9K', conversion: '8.2%' },
  { id: 3, title: '20% Off First Order', type: 'Coupon', status: 'Active', icon: 'fa-ticket', avgDiscount: '20%', sales: '$28K', conversion: '18.5%' },
  { id: 4, title: 'Free Shipping Over $50', type: 'All categories', status: 'Active', icon: 'fa-truck', avgDiscount: '0%', sales: '$89K', conversion: 'N/A' },
];

export const assortmentCategoryData = [
  { name: 'Electronics', gaps: 48, fill: '#8B5CF6' },
  { name: 'Home & Kitchen', gaps: 34, fill: '#22D3EE' },
  { name: 'Sports & Outdoors', gaps: 28, fill: '#10B981' },
  { name: 'Toys & Games', gaps: 17, fill: '#F59E0B' },
];

export const assortmentPriorityData = [
  { name: 'Critical', value: 43, color: '#F43F5E' },
  { name: 'High', value: 51, color: '#F97316' },
  { name: 'Medium', value: 23, color: '#F59E0B' },
  { name: 'Low', value: 10, color: '#3B82F6' },
];

export const assortmentCompetitorData = [
  { category: 'Electronics', yourBrand: 108, marketLeader: 245, techMaster: 156, eliteGadgets: 89 },
  { category: 'Home & Kitchen', yourBrand: 128, marketLeader: 198, techMaster: 162, eliteGadgets: 76 },
  { category: 'Sports', yourBrand: 67, marketLeader: 132, techMaster: 95, eliteGadgets: 48 },
  { category: 'Toys & Games', yourBrand: 67, marketLeader: 95, techMaster: 54, eliteGadgets: 36 },
];

export const bsrTrendData = [
  { name: 'Day 1', earbuds: 2450, watch: 450, charger: 1200 },
  { name: 'Day 5', earbuds: 2150, watch: 438, charger: 1550 },
  { name: 'Day 10', earbuds: 1550, watch: 423, charger: 2210 },
  { name: 'Day 15', earbuds: 980, watch: 430, charger: 2860 },
  { name: 'Day 20', earbuds: 850, watch: 442, charger: 3510 },
  { name: 'Day 25', earbuds: 840, watch: 445, charger: 3800 },
  { name: 'Day 30', earbuds: 850, watch: 435, charger: 3850 },
];

export const bsrForecastData = [
  { month: 'Jan', forecast: 507500, baseline: 350000 },
  { month: 'Feb', forecast: 297500, baseline: 350000 },
  { month: 'Mar', forecast: 297500, baseline: 350000 },
  { month: 'Apr', forecast: 350000, baseline: 350000 },
  { month: 'May', forecast: 350000, baseline: 350000 },
  { month: 'Jun', forecast: 448000, baseline: 350000 },
  { month: 'Jul', forecast: 448000, baseline: 350000 },
  { month: 'Aug', forecast: 448000, baseline: 350000 },
  { month: 'Sep', forecast: 350000, baseline: 350000 },
  { month: 'Oct', forecast: 350000, baseline: 350000 },
  { month: 'Nov', forecast: 507500, baseline: 350000 },
  { month: 'Dec', forecast: 507500, baseline: 350000 },
];

export const oppDistributionData = [
  { name: '90-100 Excellent', value: 12, color: '#10b981' },
  { name: '80-89 Very Good', value: 35, color: '#3b82f6' },
  { name: '70-79 Good', value: 48, color: '#8b5cf6' },
  { name: '60-69 Fair', value: 32, color: '#f97316' },
  { name: '50-59 Below Avg', value: 18, color: '#ef4444' },
];

export const oppFactorScoresData = [
  { name: 'Revenue $142K', score: 95, color: '#8b5cf6' },
  { name: 'Competition 0.18', score: 82, color: '#10b981' },
  { name: 'Margin 42%', score: 84, color: '#10b981' },
  { name: 'Reviews 185', score: 75, color: '#10b981' },
  { name: 'Entry Low', score: 70, color: '#10b981' },
];
