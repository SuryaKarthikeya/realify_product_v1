export const trendingTopicsData = [
  { label: '#TechRally', count: '24.5K posts', icon: 'fa-fire text-cb-700', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-100 dark:border-blue-900/20' },
  { label: '#FedDecision', count: '18.2K posts', icon: 'fa-fire text-cb-600', bg: 'bg-indigo-50 dark:bg-indigo-900/10', border: 'border-indigo-100 dark:border-indigo-900/20' },
  { label: '#CryptoAdoption', count: '15.7K posts', icon: 'fa-arrow-trend-up text-cb-500', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-100 dark:border-blue-900/20' },
  { label: '#ESGInvesting', count: '12.4K posts', icon: 'fa-arrow-trend-up text-cb-400', bg: 'bg-indigo-50 dark:bg-indigo-900/10', border: 'border-indigo-100 dark:border-indigo-900/20' },
  { label: '#EarningsSeason', count: '9.8K posts', icon: 'fa-chart-line text-cb-800', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-100 dark:border-blue-900/20' },
];

export const suggestedFollowsData = [
  { name: 'Robert Chen', role: 'Hedge Fund Manager', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-4.jpg' },
  { name: 'Anna Foster', role: 'Market Analyst', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-1.jpg' },
  { name: 'Marcus Johnson', role: 'Trading Expert', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-8.jpg' },
];

export const marketSummaryData = [
  { label: 'S&P 500', value: '4,847.52', change: '+1.2%', trend: 'up' },
  { label: 'NASDAQ', value: '14,847.52', change: '+2.3%', trend: 'up' },
  { label: 'Dow Jones', value: '38,247.18', change: '+0.8%', trend: 'up' },
  { label: 'VIX', value: '18.42', change: '-2.4%', trend: 'down' },
];

export const upcomingEventsData = [
  { date: '16', month: 'APR', title: 'Earnings Call', desc: 'TechCorp Q1 Results', time: '4:00 PM EST', bg: 'bg-blue-50 dark:bg-blue-900/10', text: 'text-cb-700 dark:text-blue-400' },
  { date: '18', month: 'APR', title: 'Economic Data', desc: 'Retail Sales Report', time: '8:30 AM EST', bg: 'bg-indigo-50 dark:bg-indigo-900/10', text: 'text-cb-600 dark:text-indigo-400' },
  { date: '22', month: 'APR', title: 'Webinar', desc: 'Q2 Market Outlook', time: '2:00 PM EST', bg: 'bg-blue-50 dark:bg-blue-900/10', text: 'text-cb-500 dark:text-blue-400' },
];

export const feedData = [
  {
    userName: "Michael Chen",
    userAvatar: "https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-3.jpg",
    userRole: "Senior Market Analyst",
    followers: "12.4K",
    time: "2 hours ago",
    title: "Tech Sector Shows Strong Recovery Signals",
    content: "Major tech stocks are displaying bullish patterns after recent consolidation. Key indicators suggest potential upward momentum in the coming weeks. NASDAQ composite up 2.3% today driven by semiconductor and cloud computing sectors.",
    tags: [
      { label: "Technology", bg: "bg-blue-50 dark:bg-blue-900/40", text: "text-blue-700 dark:text-blue-400" },
      { label: "BullishTrend", bg: "bg-green-50 dark:bg-green-900/40", text: "text-green-700 dark:text-green-400" },
      { label: "MarketAnalysis", bg: "bg-purple-50 dark:bg-purple-900/40", text: "text-purple-700 dark:text-purple-400" }
    ],
    dataType: "market",
    dataSection: [
      { label: "NASDAQ", value: "+2.3%", trend: "up", subtext: "14,847.52" },
      { label: "Volume", value: "$124.5B", trend: "neutral", subtext: "+18% above avg" }
    ],
    likes: 847,
    comments: 124,
    shares: 56,
    isVerified: false,
    isFollowing: false
  },
  {
    userName: "Sarah Williams",
    userAvatar: "https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-5.jpg",
    userRole: "Financial Strategist",
    followers: "8.7K",
    time: "3 hours ago",
    title: "Breaking: Federal Reserve Maintains Interest Rates",
    content: "The Federal Reserve has decided to keep interest rates unchanged at 5.25%-5.50% range. This decision reflects confidence in the economy's trajectory while remaining vigilant about inflation. Markets reacted positively to the stability signal.",
    tags: [
      { label: "FederalReserve", bg: "bg-orange-50 dark:bg-orange-900/40", text: "text-orange-700 dark:text-orange-400" },
      { label: "InterestRates", bg: "bg-red-50 dark:bg-red-900/40", text: "text-red-700 dark:text-red-400" },
      { label: "BreakingNews", bg: "bg-blue-50 dark:bg-blue-900/40", text: "text-blue-700 dark:text-blue-400" }
    ],
    dataType: "gradient",
    dataSection: { icon: "fa-landmark", label: "Current Rate Range", value: "5.25% - 5.50%" },
    likes: "1.2K",
    comments: 287,
    shares: 143,
    isVerified: false,
    isFollowing: true
  },
  {
    userName: "David Rodriguez",
    userAvatar: "https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-8.jpg",
    userRole: "Chief Investment Officer",
    followers: "24.8K",
    time: "5 hours ago",
    title: "Portfolio Diversification Strategy for Q2 2024",
    content: "As we enter the second quarter, it's crucial to reassess portfolio allocation. My analysis suggests increasing exposure to emerging markets and sustainable energy sectors while maintaining core positions in established tech. Here's my recommended breakdown:",
    tags: [
      { label: "Investment", bg: "bg-blue-50 dark:bg-blue-900/40", text: "text-blue-700 dark:text-blue-400" },
      { label: "Diversification", bg: "bg-green-50 dark:bg-green-900/40", text: "text-green-700 dark:text-green-400" },
      { label: "Q2Strategy", bg: "bg-purple-50 dark:bg-purple-900/40", text: "text-purple-700 dark:text-purple-400" }
    ],
    dataType: "grid",
    dataSection: [
      { label: "Tech", value: "35%", bg: "bg-blue-50 dark:bg-blue-900/20", border: "border-blue-100 dark:border-blue-900/30", labelColor: "text-blue-600 dark:text-blue-400", valueColor: "text-blue-700 dark:text-blue-400" },
      { label: "Energy", value: "25%", bg: "bg-green-50 dark:bg-green-900/20", border: "border-green-100 dark:border-green-900/30", labelColor: "text-green-600 dark:text-green-400", valueColor: "text-green-700 dark:text-green-400" },
      { label: "Emerging", value: "20%", bg: "bg-purple-50 dark:bg-purple-900/20", border: "border-purple-100 dark:border-purple-900/30", labelColor: "text-purple-600 dark:text-purple-400", valueColor: "text-purple-700 dark:text-purple-400" },
      { label: "Bonds", value: "20%", bg: "bg-orange-50 dark:bg-orange-900/20", border: "border-orange-100 dark:border-orange-900/30", labelColor: "text-orange-600 dark:text-orange-400", valueColor: "text-orange-700 dark:text-orange-400" }
    ],
    likes: "2.4K",
    comments: 456,
    shares: 234,
    isVerified: true,
    isFollowing: false
  }
];
