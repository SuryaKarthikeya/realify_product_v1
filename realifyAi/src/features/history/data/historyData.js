export const historyStats = [
  {
    label: "Total Searches",
    value: "247",
    subLabel: "All time",
    icon: "fa-clock-rotate-left",
    color: "blue",
  },
  {
    label: "This Week",
    value: "32",
    subLabel: "This week",
    icon: "fa-calendar-week",
    color: "green",
  },
  {
    label: "Bookmarked",
    value: "18",
    subLabel: "Saved",
    icon: "fa-bookmark",
    color: "purple",
  },
  {
    label: "Most Used",
    value: "12",
    subLabel: "Trending",
    icon: "fa-fire",
    color: "orange",
  },
];

export const historyItems = {
  today: [
    {
      id: 1,
      title: "Q3 Market Analysis for Tech Sector and recent trends",
      description: "Analyzed market trends across major tech companies including revenue growth, market share changes, and investment patterns in emerging technologies.",
      time: "2 hours ago",
      messages: 12,
      files: 3,
      icon: "fa-chart-pie",
      iconBg: "blue",
      bookmarked: false,
    },
    {
      id: 2,
      title: "Competitor breakdown: Acme vs Globex pricing strategies and market positioning. Detailed analysis of strengths, weaknesses, and strategic implications for our own pricing model adjustments.",
      description: "Comprehensive comparison of pricing models, discount structures, and value propositions between Acme and Globex in the enterprise software space.",
      richContent: [
        {
          type: 'paragraph',
          text: 'Comprehensive comparison of pricing models, discount structures, and value propositions between two leading competitors in the enterprise software space.',
        },
        {
          type: 'section',
          heading: 'Acme',
          bullets: [
            'Tiered subscription with volume discounts',
            'Strong focus on customer support and retention',
            'Annual billing incentives with long-term lock-in benefits',
          ],
        },
        {
          type: 'section',
          heading: 'Globex',
          bullets: [
            'Usage-based pricing with flexible contract terms',
            'Emphasis on product innovation and frequent feature releases',
            'Frequent promotional offers targeting new customer acquisition',
          ],
        },
        {
          type: 'section',
          heading: 'Key Differentiators',
          bullets: [
            "Acme's customer-centric approach vs Globex's innovation-driven strategy",
            'Different impacts on market positioning and long-term customer loyalty',
            'Acme suits enterprise clients seeking stability; Globex attracts growth-stage companies',
          ],
        },
        {
          type: 'section',
          heading: 'Strategic Recommendations',
          bullets: [
            'Explore hybrid pricing options to capture both customer segments',
            'Enhance customer support offerings to differentiate from Globex',
            'Monitor competitor promotional activities to maintain market competitiveness',
            'Consider annual billing incentives to improve revenue predictability',
          ],
        },
      ],
      time: "4 hours ago",
      messages: 8,
      files: 2,
      icon: "fa-users",
      iconBg: "green",
      bookmarked: true,
    },
    {
      id: 3,
      title: "Revenue projection model based on current metrics",
      description: "Built a 3-year financial forecast incorporating historical growth rates, market conditions, and planned expansion initiatives.",
      time: "6 hours ago",
      messages: 15,
      charts: 5,
      icon: "fa-file-invoice-dollar",
      iconBg: "purple",
      bookmarked: false,
    },
    {
      id: 8,
      title: "New Market Analysis for Tech Sector and recent trends",
      description: "Analyzed market trends across major tech companies including revenue growth, market share changes, and investment patterns in emerging technologies.",
      time: "2 hours ago",
      messages: 12,
      files: 3,
      icon: "fa-chart-pie",
      iconBg: "blue",
      bookmarked: false,
    },
    {
      id: 9,
      title: "Super New Market Analysis for Tech Sector and recent trends",
      description: "Analyzed market trends across major tech companies including revenue growth, market share changes, and investment patterns in emerging technologies.",
      time: "2 hours ago",
      messages: 12,
      files: 3,
      icon: "fa-chart-pie",
      iconBg: "blue",
      bookmarked: false,
    },
  ],
  yesterday: [
    {
      id: 4,
      title: "Extract key metrics from Q3 earnings call transcript",
      description: "Identified and extracted critical financial metrics, growth indicators, and strategic initiatives mentioned during the quarterly earnings presentation.",
      time: "Yesterday, 3:45 PM",
      messages: 10,
      files: 1,
      icon: "fa-magnifying-glass-chart",
      iconBg: "orange",
      bookmarked: false,
    },
    {
      id: 5,
      title: "Draft cold outreach email template for sales team",
      description: "Created personalized email templates with multiple variations for different prospect segments and industries.",
      time: "Yesterday, 11:20 AM",
      messages: 6,
      icon: "fa-envelope",
      iconBg: "indigo",
      bookmarked: true,
    },
  ],
  week: [
    {
      id: 6,
      title: "Best practices for user onboarding flows in SaaS products",
      description: "Research on effective onboarding strategies, including progressive disclosure, interactive tutorials, and milestone-based engagement.",
      time: "3 days ago",
      messages: 14,
      icon: "fa-user-check",
      iconBg: "teal",
      bookmarked: true,
    },
    {
      id: 7,
      title: "Summarize Q2 earnings report PDF for stakeholder presentation",
      description: "Generated executive summary highlighting key financial achievements, challenges, and forward-looking statements from the quarterly report.",
      time: "5 days ago",
      messages: 9,
      files: 1,
      icon: "fa-file-lines",
      iconType: "regular",
      iconBg: "pink",
      bookmarked: false,
    },
  ],
};

export const quickFilters = [
  { id: 'all',        name: "All History", icon: "fa-clock-rotate-left", count: 247 },
  { id: 'bookmarked', name: "Bookmarked",  icon: "fa-bookmark",          count: 18  },
  { id: 'analytics',  name: "Analytics",   icon: "fa-chart-line",        count: 42  },
  { id: 'artifacts',  name: "Artifacts",   icon: "fa-file",              count: 67  },
];

export const modules = [
  {
    name: 'Intel',
    key: 'intel',
    icon: 'fa-chart-line',
    searches: [
      { text: 'Price drop impact on margin',   chatId: 3 },
      { text: 'Inventory reorder analysis',     chatId: 2 },
      { text: 'Ads ROAS optimization',          chatId: 8 },
      { text: 'Cash flow runway forecast',      chatId: 9 },
    ],
  },
  {
    name: 'Research',
    key: 'research',
    icon: 'fa-chart-column',
    searches: [
      { text: 'Q3 Market Analysis for Tech',   chatId: 1 },
      { text: 'Competitor pricing breakdown',   chatId: 2 },
      { text: 'Revenue projection model',       chatId: 3 },
      { text: 'Industry benchmark report',      chatId: 7 },
    ],
  },
];

export const MODULE_ITEM_IDS = {
  intel:    [2, 3, 8, 9],
  research: [1, 2, 3, 7],
};

export const mostUsedSearches = [
  { title: "Market trend analysis", count: 12 },
  { title: "Competitor pricing",    count: 9  },
  { title: "Revenue forecasting",   count: 8  },
];
