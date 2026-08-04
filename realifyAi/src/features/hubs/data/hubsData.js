// ─── Plugin Registry ──────────────────────────────────────────────────────────

export const PLUGINS = {
  agentic: {
    id: 'agentic',
    icon: 'fa-envelope-open-text',
    iconBg: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    title: 'Agentic Mailbox AI',
    author: 'Realify Labs',
    price: '$49',
    priceSuffix: '/mo',
    priceModal: '$49.00',
    priceBadge: 'bg-green-100 text-green-700',
    rating: '4.9',
    reviewsBadge: '2.4k',
    detailReviews: '2,481',
    installsBadge: '12k+',
    detailInstalls: '12,000+',
    categoryBadge: 'Productivity',
    detailCategory: 'Productivity, AI',
    featured: true,
    description:
      'AI-powered email service. Connect accounts, track threads, auto-respond, and perform complex actions autonomously.',
    overview:
      'Agentic Mailbox AI transforms your chaotic inbox into a streamlined, automated command center. By connecting your email accounts, our advanced AI agents continuously monitor incoming messages, categorize them by urgency and context, and can even auto-respond to routine inquiries or perform complex multi-step actions based on your predefined rules.',
    features: [
      { title: 'Intelligent Auto-Sorting', desc: 'Automatically categorizes emails into Action Required, FYI, Newsletters, and Spam with 99% accuracy.' },
      { title: 'Agentic Auto-Responses', desc: 'Drafts and sends context-aware replies to common inquiries, scheduling requests, and follow-ups.' },
      { title: 'Action Execution', desc: 'Extracts data from emails to update CRM, create calendar events, or trigger webhooks automatically.' },
      { title: 'Multi-Account Sync', desc: 'Connect Gmail, Outlook, and IMAP accounts into one unified AI-managed interface.' },
    ],
    screenshots: [
      'https://storage.googleapis.com/uxpilot-auth.appspot.com/05d89e0eca-1e1cf21ea8e885af1be8.png',
      'https://storage.googleapis.com/uxpilot-auth.appspot.com/d06427edab-22ce81e8f65196846f07.png',
    ],
    detailRatingBars: [85, 10, 3, 1, 1],
    detailReviewsList: [
      { name: 'Sarah Mitchell', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-5.jpg', stars: 5, date: '2 days ago', text: "This plugin has completely transformed how I manage my emails! The AI categorization is incredibly accurate, and I love how it auto-responds to routine inquiries. It's saved me at least 2 hours every day.", helpful: 24 },
      { name: 'Michael Chen', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-3.jpg', stars: 5, date: '1 week ago', text: "Outstanding email management tool! The multi-account sync works flawlessly. I can manage all my business and personal emails from one interface. The automation features are powerful yet easy to set up.", helpful: 18 },
      { name: 'Emily Rodriguez', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-1.jpg', stars: 4, date: '2 weeks ago', text: "Great plugin overall. The AI is very smart and learns your preferences quickly. My only minor complaint is that the mobile app could use some improvements, but the desktop version is perfect.", helpful: 12 },
    ],
    detailFaqs: [
      { q: 'How does the AI learn my email preferences?', a: 'The AI uses machine learning to observe how you interact with emails over time. Within the first week, it typically achieves 90%+ accuracy in categorizing your emails according to your preferences.', btn: 'Start Free Trial' },
      { q: 'Can I customize the auto-response templates?', a: 'Yes! You have full control over all auto-response templates. You can create custom templates for different scenarios, set conditions for when they should be used, and include dynamic variables.', btn: 'View Templates' },
      { q: 'Which email providers are supported?', a: 'We support Gmail, Google Workspace, Outlook.com, Office 365, Yahoo Mail, and any IMAP-enabled email service. Connect unlimited email accounts in one interface.', btn: 'Connect Email' },
      { q: 'Is my email data secure and private?', a: 'All your email data is encrypted in transit and at rest using AES-256. We never share your data with third parties. Our servers are SOC 2 compliant and regularly audited.', btn: 'Security Details' },
      { q: 'Can I integrate this with my CRM or other tools?', a: 'Yes! Native integrations with Salesforce, HubSpot, and Pipedrive. We also support Zapier for 5,000+ apps and provide a REST API for custom integrations.', btn: 'View Integrations' },
    ],
  },

  rora: {
    id: 'rora',
    icon: 'fa-bullseye',
    iconBg: 'bg-purple-100',
    iconColor: 'text-purple-600',
    title: 'Rora',
    author: 'Realify Labs',
    price: '$29',
    priceSuffix: '/mo',
    priceModal: '$29.00',
    priceBadge: 'bg-green-100 text-green-700',
    rating: '4.8',
    reviewsBadge: '1.2k',
    detailReviews: '1,200',
    installsBadge: '15k+',
    detailInstalls: '15,000+',
    categoryBadge: 'Marketing',
    detailCategory: 'Marketing, Analytics',
    featured: false,
    description:
      'Advanced marketing integration and insights platform. Track campaigns, analyze ROI, and optimize your marketing spend automatically.',
    overview:
      'Rora is an advanced marketing integration and insights platform that helps you track campaigns, analyze ROI, and optimize your marketing spend automatically. With powerful analytics and real-time reporting, you can make data-driven decisions to grow your business faster.',
    features: [
      { title: 'Campaign Tracking', desc: 'Monitor all your marketing campaigns across channels in one unified dashboard with real-time updates.' },
      { title: 'ROI Analytics', desc: 'Deep-dive into return on investment metrics for each campaign and marketing channel.' },
      { title: 'Automated Optimization', desc: 'AI-powered suggestions to automatically optimize your ad spend and audience targeting.' },
      { title: 'Custom Dashboards', desc: 'Build personalized dashboards with the KPIs that matter most to your business.' },
    ],
    screenshots: [],
    detailRatingBars: [80, 14, 4, 1, 1],
    detailReviewsList: [
      { name: 'Emily Rodriguez', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-1.jpg', stars: 5, date: '1 week ago', text: "Rora has been a game-changer for our marketing team. The ROI analytics are detailed and actionable. We've optimized our ad spend and increased conversions by 40% in just two months!", helpful: 31 },
    ],
    detailFaqs: [
      { q: 'How do I connect my ad accounts?', a: 'Rora supports direct integration with Google Ads, Facebook Ads, LinkedIn Ads, and more. Go to Settings > Integrations and follow the OAuth flow.', btn: 'Connect Accounts' },
      { q: 'Can I export reports?', a: 'Yes! Export reports as PDF, CSV, or Excel. You can also schedule automated email reports on a daily, weekly, or monthly basis.', btn: 'View Reports' },
    ],
  },

  savings: {
    id: 'savings',
    icon: 'fa-piggy-bank',
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600',
    title: 'Savings Catcher',
    author: 'FinTech Solutions',
    price: 'Free',
    priceSuffix: '',
    priceModal: '$0.00',
    priceBadge: 'bg-blue-100 text-blue-700',
    rating: '4.6',
    reviewsBadge: '856',
    detailReviews: '856',
    installsBadge: '42k+',
    detailInstalls: '42,000+',
    categoryBadge: 'Finance',
    detailCategory: 'Finance, Productivity',
    featured: false,
    description:
      'Automatically analyzes your spending habits to identify savings opportunities and provides actionable tips to increase your wealth.',
    overview:
      'Savings Catcher automatically analyzes your spending habits to identify savings opportunities and provides actionable tips to increase your wealth. Track subscriptions, find better deals, and get personalized recommendations to save money effortlessly.',
    features: [
      { title: 'Spending Analysis', desc: 'Deep analysis of your spending patterns to identify areas for improvement and potential savings.' },
      { title: 'Subscription Tracker', desc: 'Find and track all your subscriptions to eliminate forgotten recurring charges.' },
      { title: 'Savings Recommendations', desc: 'Personalized tips and recommendations to help you save more money every month.' },
      { title: 'Wealth Building Tips', desc: 'Actionable advice to grow your wealth through smart financial decisions.' },
    ],
    screenshots: [],
    detailRatingBars: [72, 18, 6, 3, 1],
    detailReviewsList: [
      { name: 'Jessica Park', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-7.jpg', stars: 4, date: '2 weeks ago', text: "Love the automated savings recommendations! It found subscriptions I forgot about and helped me save over $200/month. The interface is clean and easy to use. Would be perfect with a mobile app!", helpful: 15 },
    ],
    detailFaqs: [
      { q: 'How does Savings Catcher analyze my spending?', a: 'It connects to your bank accounts and credit cards via secure bank-grade APIs to analyze your transaction history and identify patterns.', btn: 'Connect Account' },
      { q: 'Is it really free?', a: 'Yes! The core features are completely free. We offer a premium tier for advanced analytics and personalized financial coaching.', btn: 'View Plans' },
    ],
  },

  finance: {
    id: 'finance',
    icon: 'fa-chart-pie',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    title: 'Finance Plugin',
    author: 'Capital Systems',
    price: '$15',
    priceSuffix: '/mo',
    priceModal: '$15.00',
    priceBadge: 'bg-green-100 text-green-700',
    rating: '4.9',
    reviewsBadge: '3.1k',
    detailReviews: '3,100',
    installsBadge: '89k+',
    detailInstalls: '89,000+',
    categoryBadge: 'Finance',
    detailCategory: 'Finance, Analytics',
    featured: false,
    description:
      'Comprehensive financial tracking. Check loan eligibility, manage debts, and get a unified view of your entire financial status.',
    overview:
      'Comprehensive financial tracking solution that helps you check loan eligibility, manage debts, and get a unified view of your entire financial status. Make informed decisions with real-time insights and personalized recommendations.',
    features: [
      { title: 'Loan Eligibility Checker', desc: 'Instantly check your eligibility for various loan types with detailed breakdowns and requirements.' },
      { title: 'Debt Management', desc: 'Track and manage all your debts with smart payoff strategies and custom timelines.' },
      { title: 'Financial Overview', desc: 'Unified view of your entire financial status including assets, liabilities, and net worth.' },
      { title: 'Real-time Insights', desc: 'Get real-time financial insights and personalized recommendations to improve your financial health.' },
    ],
    screenshots: [],
    detailRatingBars: [85, 10, 3, 1, 1],
    detailReviewsList: [
      { name: 'Michael Chen', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-3.jpg', stars: 5, date: '5 days ago', text: "Outstanding financial management tool! The loan eligibility checker is super accurate and the debt management features have helped me pay off my credit cards faster. Highly recommend!", helpful: 18 },
    ],
    detailFaqs: [
      { q: 'How does the loan eligibility checker work?', a: 'It analyzes your credit profile, income, and existing debts to estimate your eligibility for various loan types with instant results.', btn: 'Check Eligibility' },
      { q: 'Can I connect multiple bank accounts?', a: 'Yes! Connect unlimited bank accounts and credit cards to get a complete picture of your financial health.', btn: 'Connect Accounts' },
    ],
  },
};

export const PLUGINS_LIST = Object.values(PLUGINS);

// ─── Marketplace FAQs ─────────────────────────────────────────────────────────

export const MAIN_FAQS = [
  { q: 'How do I install a plugin from the marketplace?', a: 'Installing a plugin is simple and straightforward. Just click on any plugin card to view its details, then click the "Start Free Trial" or "Install" button. The plugin will be automatically added to your account and you can start using it immediately.', btn: 'Get Started' },
  { q: 'Can I try plugins before purchasing?', a: "Yes! Most plugins offer a 14-day free trial period. You can explore all features without any commitment. If you're not satisfied, you can cancel anytime during the trial period without being charged.", btn: 'Browse Plugins' },
  { q: 'How do I cancel a plugin subscription?', a: 'You can cancel any plugin subscription at any time from your account settings. Go to "Installed Plugins", select the plugin you want to cancel, and click "Cancel Subscription". Your access will continue until the end of your billing period.', btn: 'Manage Subscriptions' },
  { q: 'Are my data and information secure with these plugins?', a: 'Absolutely. All plugins in our marketplace are thoroughly vetted and verified by our security team. They must comply with industry-standard security protocols and data protection regulations. Your information is encrypted and handled with the highest security standards.', btn: 'Learn More' },
  { q: 'What payment methods do you accept?', a: 'We accept all major credit cards (Visa, Mastercard, American Express, Discover), PayPal, and bank transfers for enterprise customers. All payments are processed securely through our encrypted payment gateway.', btn: 'View Payment Options' },
  { q: 'Can I get support if I have issues with a plugin?', a: "Yes! Each plugin developer provides dedicated support. Premium plugins typically offer priority 24/7 support. You can contact support directly through the plugin's detail page or reach out to our marketplace support team for assistance.", btn: 'Contact Support' },
];

// ─── Marketplace Reviews ──────────────────────────────────────────────────────

export const MAIN_REVIEWS = [
  { name: 'Sarah Mitchell', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-5.jpg', stars: 5, plugin: 'Agentic Mailbox AI', date: '2 days ago', text: "This plugin has completely transformed how I manage my emails! The AI categorization is incredibly accurate, and I love how it auto-responds to routine inquiries. It's saved me at least 2 hours every day.", helpful: 24 },
  { name: 'Michael Chen', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-3.jpg', stars: 5, plugin: 'Finance Plugin', date: '5 days ago', text: "Outstanding financial management tool! The loan eligibility checker is super accurate and the debt management features have helped me pay off my credit cards faster. Highly recommend!", helpful: 18 },
  { name: 'Emily Rodriguez', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-1.jpg', stars: 5, plugin: 'Rora', date: '1 week ago', text: "Rora has been a game-changer for our marketing team. The ROI analytics are detailed and actionable. We've optimized our ad spend and increased conversions by 40% in just two months!", helpful: 31 },
  { name: 'Jessica Park', avatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-7.jpg', stars: 4, plugin: 'Savings Catcher', date: '2 weeks ago', text: "Love the automated savings recommendations! It found subscriptions I forgot about and helped me save over $200/month. The interface is clean and easy to use. Would be perfect with a mobile app!", helpful: 15 },
];

export const RATING_BARS = [
  { label: '5★', pct: 82 },
  { label: '4★', pct: 12 },
  { label: '3★', pct: 4 },
  { label: '2★', pct: 1 },
  { label: '1★', pct: 1 },
];

// ─── Subscription Sidebar Meta ────────────────────────────────────────────────

export const SUBSCRIPTION_META = [
  { label: 'Billed:', value: 'Monthly' },
  { label: 'Cancelation:', value: 'Anytime' },
  { label: 'Support:', value: '24/7 Priority' },
];

export const PLUGIN_META_LINKS = [
  { icon: 'fa-shield-halved', text: 'Verified by Security' },
  { icon: 'fa-rotate', text: 'Last updated: 2 days ago' },
  { icon: 'fa-code-branch', text: 'Version: 2.4.1' },
];
