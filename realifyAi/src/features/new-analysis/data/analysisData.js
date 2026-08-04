export const analysisCategories = [
  {
    title: 'Performance',
    icon: 'fa-chart-pie',
    color: 'bg-blue-50 dark:bg-blue-900/30 text-cb-700',
    desc: 'Analyze recent trends in the tech sector and generate a comprehensive report.',
    suggestions: [
      'How did my business perform this month vs last month?',
      'Which SKUs drove the most revenue growth this week?',
      'Where am I losing money right now?',
      'What should I focus on this week to improve performance?',
      'Give me a full business health check across sales, margins, and inventory.'
    ],
  },
  {
    title: 'Positioning',
    icon: 'fa-users',
    color: 'bg-indigo-50 dark:bg-indigo-900/30 text-cb-600',
    desc: 'Compare pricing strategies of top 3 competitors in our industry space.',
    suggestions: [
      'Which of my ASINs are most vulnerable to competition right now?',
      'Am I losing the Buy Box on any listings — and why?',
      'How does my pricing compare to competitors in my category?',
      'Which competitors have been gaining rank while I have been losing it?',
      'Where should I cut price vs. hold margin to stay competitive?',
    ],
  },
  {
    title: 'Product',
    icon: 'fa-file-invoice-dollar',
    color: 'bg-blue-50 dark:bg-blue-900/30 text-cb-500',
    desc: 'Create a 3-year revenue projection based on current growth metrics.',
    suggestions: [
      'Which SKUs are at risk and need my attention today?',
      'What are my top 10 SKUs by profit — not just revenue?',
      'Which products have the worst margin and what is dragging it down?',
      'Show me SKUs that are selling well but running low on stock.',
      'Which products should I consider discontinuing?',
    ],
  },
  {
    title: 'Portfolio',
    icon: 'fa-magnifying-glass-chart',
    color: 'bg-indigo-50 dark:bg-indigo-900/30 text-cb-800',
    desc: 'Extract key metrics from the uploaded Q3 earnings call transcript.',
    suggestions: [
      'How is my Amazon India performance trending this quarter?',
      'Which SKUs are underperforming on a specific channel?',
      'Do I have any pricing inconsistencies across channels?',
      'Where am I seeing the highest return rates and why?',
      'Which channel is driving the most profitable orders?',
    ],
  },
];

/**
 * Canned analysis replies for the demo chat.
 *
 * `match` is checked against the lowercased prompt, first hit wins; the last
 * entry has no `match` and acts as the fallback so any prompt gets an answer.
 */
export const ANALYSIS_REPLIES = [
  {
    match: ['buy box', 'reprice', 'price', 'pricing', 'competitor'],
    headline: 'Buy Box share is slipping on one high-revenue listing.',
    body: 'B0DM28PRG7 has held only 71% Buy Box share for the last 11 days after a competitor undercut you by $420. At $8,499 you would reclaim the Buy Box and still clear the margin floor by $559.',
    metrics: [
      { label: 'Buy Box share', value: '71%', tone: 'bad' },
      { label: 'Revenue at risk', value: '$240K', tone: 'bad' },
      { label: 'Recoverable', value: '+$240K', tone: 'good' },
    ],
    bullets: [
      'The category promo window closes in 6 days, after which traffic drops about 40%.',
      'Two more listings are within $200 of their floor and worth watching this week.',
      'Repricing takes effect within about 2 hours of the next repricer sweep.',
    ],
    followUp: 'Want me to open the reprice simulation for B0DM28PRG7?',
  },
  {
    match: ['stock', 'inventory', 'stockout', 'restock', 'reorder', 'cover'],
    headline: 'Two SKUs will run out before their next inbound lands.',
    body: 'SKU-CHR-42 has 4 days of cover against a 3-day expedite lane, and SKU-CAM-01 is running 61 units/day after a viral lift with 244 units left. Both need a decision today.',
    metrics: [
      { label: 'SKUs at risk', value: '2', tone: 'bad' },
      { label: 'Days of cover', value: '4 days', tone: 'bad' },
      { label: 'Revenue protected', value: '+$280K', tone: 'good' },
    ],
    bullets: [
      'Expediting 200 units of SKU-CHR-42 costs a $34K premium but protects the Buy Box.',
      'SKU-CAM-01 needs 350 units to bridge the 5-day lane at the new run rate.',
      'Working capital covers both without straining the week-6 cash position.',
    ],
    followUp: 'Should I draft both inbound shipments for review?',
  },
  {
    match: ['margin', 'profit', 'cm2', 'cogs', 'fee'],
    headline: 'Margin is leaking in two places worth $355K a month.',
    body: 'SKU-EAR-10 is billed in the wrong Amazon size tier — $50 per unit across 4,180 units over 7 months. Separately, the broad keyword "heavy jackets" has spent $162K for $17K of sales.',
    metrics: [
      { label: 'Fee overcharge', value: '$210K', tone: 'bad' },
      { label: 'Wasted ad spend', value: '$145K', tone: 'bad' },
      { label: 'Recoverable', value: '+$355K', tone: 'good' },
    ],
    bullets: [
      'The fee claim is inside Amazon\'s 18-month reimbursement window, so the full period is claimable.',
      'Negating the keyword takes effect within the hour and is fully reversible.',
      'Together these lift blended CM2 by roughly 2.4 points.',
    ],
    followUp: 'Want the dimensional audit filed first, or the keyword negated?',
  },
  {
    match: ['ad', 'ads', 'roas', 'campaign', 'tacos', 'keyword', 'spend'],
    headline: 'Ad efficiency splits sharply across your six campaigns.',
    body: 'Smart Camera SP Broad has fallen to 1.8x ROAS while the paired exact-match campaign converts at 4.4x and is budget-capped. Moving the broad budget across recovers most of the gap.',
    metrics: [
      { label: 'Worst ROAS', value: '1.8x', tone: 'bad' },
      { label: 'Best ROAS', value: '8.4x', tone: 'good' },
      { label: 'Recoverable', value: '+$195K', tone: 'good' },
    ],
    bullets: [
      'Lumbar Chair Prospecting caps out at 11:00 AM daily and never sees the afternoon peak.',
      'The Shopify retargeting set has run 46 days at frequency 7.8 — textbook creative fatigue.',
      'Walmart prospecting is pacing at only 62% of budget while returning 4.9x.',
    ],
    followUp: 'Want me to rank all six campaigns by recoverable spend?',
  },
  {
    match: ['cash', 'payout', 'working capital', 'runway', 'burn'],
    headline: 'A 14-day payout gap lands before your next supplier payment.',
    body: 'Amazon settles on day 21 but PO-01 is due on day 7, leaving a $185K shortfall against a $120K buffer. This supplier has granted a terms extension twice before at no cost.',
    metrics: [
      { label: 'Gap', value: '14 days', tone: 'bad' },
      { label: 'Shortfall', value: '$185K', tone: 'bad' },
      { label: 'Fee avoidable', value: '$26K', tone: 'good' },
    ],
    bullets: [
      'Early payout is available at 1.4%, which costs $26K on this cycle.',
      'Clearing 400 excess units of SKU-OVS-12 would free $340K and extend runway 11 days.',
      'Terms requests need notice — past day 4 the paid payout is the only lever left.',
    ],
    followUp: 'Should I prepare the terms extension request?',
  },
  {
    headline: 'Here is where your business stands right now.',
    body: 'Across the last 30 days revenue is $248.5K (+14.2%) with $42.8K of CM2 margin. Twenty-two actions are open, and the five largest together carry about $1.1M of exposure.',
    metrics: [
      { label: 'Revenue', value: '$248.5K', tone: 'good' },
      { label: 'Open actions', value: '22', tone: 'neutral' },
      { label: 'Total exposure', value: '$1.1M', tone: 'bad' },
    ],
    bullets: [
      'Inventory holds the largest single exposure at $280K across two at-risk SKUs.',
      'Margin has two recoverable leaks worth $355K a month combined.',
      'Ads efficiency ranges from 1.8x to 8.4x ROAS — the spread is the opportunity.',
    ],
    followUp: 'Want me to break any of these down further?',
  },
];

/** First matching reply for a prompt; the last entry is the catch-all. */
export const getAnalysisReply = (prompt) => {
  const text = (prompt || '').toLowerCase();
  return (
    ANALYSIS_REPLIES.find((r) => r.match?.some((k) => text.includes(k))) ||
    ANALYSIS_REPLIES[ANALYSIS_REPLIES.length - 1]
  );
};
