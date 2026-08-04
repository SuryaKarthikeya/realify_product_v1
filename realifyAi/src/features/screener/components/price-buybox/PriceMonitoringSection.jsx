import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const statusPill = {
  green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800',
  red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800',
  orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 border border-orange-200 dark:border-orange-800',
};

const listingLeftBorder = {
  green: 'border-l-green-600',
  red: 'border-l-red-600',
  orange: 'border-l-orange-600',
  blue: 'border-l-blue-600',
};

const ListingIcon = ({ kind }) => {
  const map = {
    laptop: 'fa-laptop',
    mobile: 'fa-mobile',
    keyboard: 'fa-keyboard',
    camera: 'fa-camera',
  };
  return <i className={`fa-solid ${map[kind] || 'fa-box'} text-gray-400`}></i>;
};

const defaultListings = [
  {
    id: 1,
    name: 'Wireless Bluetooth Headphones',
    sku: 'WBH-2024-001',
    category: 'Electronics › Audio',
    icon: 'laptop',
    status: { label: 'Buy Box', color: 'green' },
    yourPrice: '$62.99',
    yourPriceNum: 62.99,
    marketPosition: '2nd',
    marketPositionSub: 'Out of 12 sellers',
    priceDelta: '-5.2%',
    priceDeltaSub: 'Below market avg',
    bsr: '#1,247',
    bsrSub: 'In category',
    competitorPricing: [
      { dot: 'green', label: 'Your Brand', price: '$62.99', emphasis: 'none' },
      { dot: 'red', label: 'TechMaster Pro', price: '$59.99', emphasis: 'down' },
      { dot: 'slate', label: 'SmartBuy Co', price: '$64.99', emphasis: 'none' },
      { dot: 'slate', label: 'EliteGadgets', price: '$79.99', emphasis: 'none' },
    ],
    ctas: [
      { label: 'Adjust Price', tone: 'primary', icon: 'fa-edit' },
      { label: 'Analytics', tone: 'secondary', icon: 'fa-chart-line' },
    ],
  },
  {
    id: 2,
    name: 'USB-C Fast Charger',
    sku: 'USC-2024-045',
    category: 'Electronics › Accessories',
    icon: 'mobile',
    status: { label: 'Lost BB', color: 'red' },
    yourPrice: '$24.99',
    yourPriceNum: 24.99,
    marketPosition: '4th',
    marketPositionSub: 'Out of 18 sellers',
    priceDelta: '+8.7%',
    priceDeltaSub: 'Above market avg',
    bsr: '#3,892',
    bsrSub: 'In category',
    actionCard: {
      tone: 'red',
      title: 'Action Required',
      body: 'You lost the Buy Box 2 hours ago. TechMaster Pro is now winning at $22.99.',
      cta: 'Lower Price to Compete',
    },
    competitorPricing: [
      { dot: 'red', label: 'TechMaster Pro', price: '$22.99', emphasis: 'bb' },
      { dot: 'slate', label: 'ValueMart Direct', price: '$23.49', emphasis: 'none' },
      { dot: 'slate', label: 'SmartBuy Co', price: '$23.99', emphasis: 'none' },
      { dot: 'orange', label: 'Your Brand', price: '$24.99', emphasis: 'none' },
    ],
    ctas: [
      { label: 'Quick Reprice', tone: 'danger', icon: 'fa-bolt' },
      { label: 'Analytics', tone: 'secondary', icon: 'fa-chart-line' },
    ],
  },
  {
    id: 3,
    name: 'Mechanical Gaming Keyboard',
    sku: 'MGK-2024-078',
    category: 'Electronics › Gaming',
    icon: 'keyboard',
    status: { label: 'Buy Box', color: 'green' },
    yourPrice: '$89.99',
    yourPriceNum: 89.99,
    marketPosition: '1st',
    marketPositionSub: 'Out of 8 sellers',
    priceDelta: '-3.4%',
    priceDeltaSub: 'Below market avg',
    bsr: '#542',
    bsrSub: 'In category',
    competitorPricing: [
      { dot: 'green', label: 'Your Brand', price: '$89.99', emphasis: 'bb' },
      { dot: 'slate', label: 'EliteGadgets', price: '$94.99', emphasis: 'none' },
      { dot: 'slate', label: 'SmartBuy Co', price: '$99.99', emphasis: 'none' },
    ],
    ctas: [
      { label: 'Adjust Price', tone: 'primary', icon: 'fa-edit' },
      { label: 'Analytics', tone: 'secondary', icon: 'fa-chart-line' },
    ],
  },
  {
    id: 4,
    name: '4K Action Camera',
    sku: 'CAM-2024-112',
    category: 'Electronics › Cameras',
    icon: 'camera',
    status: { label: 'Price Alert', color: 'orange' },
    yourPrice: '$149.99',
    yourPriceNum: 149.99,
    marketPosition: '3rd',
    marketPositionSub: 'Out of 15 sellers',
    priceDelta: '+2.1%',
    priceDeltaSub: 'Above market avg',
    bsr: '#2,156',
    bsrSub: 'In category',
    actionCard: {
      tone: 'orange',
      title: 'Price Alert Triggered',
      body: 'TechMaster Pro dropped price to $139.99 (6.7% decrease). Consider repricing to maintain competitiveness.',
    },
    competitorPricing: [
      { dot: 'blue', label: 'EliteGadgets', price: '$134.99', emphasis: 'bb' },
      { dot: 'red', label: 'TechMaster Pro', price: '$139.99', emphasis: 'downPct', pct: '↓ -6.7%' },
      { dot: 'orange', label: 'Your Brand', price: '$149.99', emphasis: 'none' },
      { dot: 'slate', label: 'SmartBuy Co', price: '$154.99', emphasis: 'none' },
    ],
    ctas: [
      { label: 'Quick Reprice', tone: 'warning', icon: 'fa-bolt' },
      { label: 'Analytics', tone: 'secondary', icon: 'fa-chart-line' },
    ],
  },
];

const Dot = ({ color }) => {
  const cls =
    color === 'green'
      ? 'bg-green-500'
      : color === 'red'
        ? 'bg-red-500'
        : color === 'orange'
          ? 'bg-orange-500'
          : color === 'blue'
            ? 'bg-blue-500'
            : 'bg-gray-400';
  return <span className={`w-2 h-2 rounded-full ${cls}`}></span>;
};

const Button = ({ tone, icon, children, full = false }) => {
  const base = `px-6 py-3 rounded-xl transition shadow-sm font-medium ${full ? 'flex-1' : ''}`;
  if (tone === 'primary') return <button className={`${base} bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500`}><i className={`fa-solid ${icon} mr-2`}></i>{children}</button>;
  if (tone === 'danger') return <button className={`${base} bg-red-600 text-white hover:bg-red-700`}><i className={`fa-solid ${icon} mr-2`}></i>{children}</button>;
  if (tone === 'warning') return <button className={`${base} bg-orange-600 text-white hover:bg-orange-700`}><i className={`fa-solid ${icon} mr-2`}></i>{children}</button>;
  return <button className={`${base} bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700`}><i className={`fa-solid ${icon} mr-2`}></i>{children}</button>;
};

const MetricCard = ({ tone, label, value, sub }) => {
  const map = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100 text-blue-700 dark:text-blue-300',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100 text-green-700 dark:text-green-300',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 text-purple-900 dark:text-purple-100 text-purple-700 dark:text-purple-300',
    orange: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800 text-orange-900 dark:text-orange-100 text-orange-700 dark:text-orange-300',
    red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100 text-red-700 dark:text-red-300',
  };
  const classes = map[tone] || map.blue;
  return (
    <div className={`border rounded-xl p-4 ${classes.split(' ')[0]} ${classes.split(' ')[2]}`}>
      <p className={`text-xs font-medium mb-1 ${classes.split(' ')[5]}`}>{label}</p>
      <p className={`text-2xl font-bold ${classes.split(' ')[3]}`}>{value}</p>
      {sub && <p className={`text-xs mt-1 ${classes.split(' ')[6]}`}>{sub}</p>}
    </div>
  );
};

const PriceMonitoringSection = ({ listings = defaultListings }) => {
  const [activeId, setActiveId] = useState(listings[0]?.id || 1);
  const active = useMemo(() => listings.find((l) => l.id === activeId) || listings[0], [activeId, listings]);

  const headerBadge = useMemo(() => {
    if (!active) return null;
    if (active.status.color === 'green') {
      return { text: 'Buy Box Winner', tone: 'green', icon: 'fa-trophy' };
    }
    if (active.status.color === 'red') {
      return { text: 'Lost Buy Box', tone: 'red', icon: 'fa-exclamation-triangle' };
    }
    return { text: active.status.label, tone: 'orange', icon: 'fa-bell' };
  }, [active]);

  return (
    <section className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-gray-200 dark:border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Price Monitoring</h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">Track competitor pricing and buy box status</p>
          </div>
          <div className="flex items-center gap-2">
            <button className="px-4 py-2 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800 rounded-xl text-sm border border-gray-200 dark:border-slate-700 transition shadow-sm text-gray-700 dark:text-slate-200">
              <i className="fa-solid fa-filter mr-2 text-gray-600 dark:text-slate-300"></i>
              <span className="font-medium">Filter</span>
            </button>
            <button className="px-4 py-2 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 rounded-xl transition shadow-sm text-sm font-medium">
              <i className="fa-solid fa-download mr-2"></i>Export
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Listings sidebar */}
        <div className="lg:col-span-4 border-r border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-800/30 overflow-y-auto" style={{ maxHeight: 600 }}>
          <div className="p-4 border-b border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 sticky top-0 z-10">
            <div className="relative">
              <i className="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
              <input
                type="text"
                placeholder="Search products..."
                className="w-full px-4 py-2 pl-10 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 focus:border-transparent text-gray-900 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="divide-y divide-gray-200 dark:divide-slate-800">
            {listings.map((l) => {
              const activeRow = l.id === activeId;
              const left = l.status.color === 'green' ? listingLeftBorder.blue : l.status.color === 'red' ? listingLeftBorder.red : listingLeftBorder.orange;
              return (
                <div
                  key={l.id}
                  className={[
                    'p-4 bg-white dark:bg-slate-900 cursor-pointer transition',
                    'border-l-4',
                    activeRow ? (l.status.color === 'green' ? listingLeftBorder.blue : left) : 'border-l-transparent hover:bg-gray-50 dark:hover:bg-slate-800/40',
                    activeRow ? 'bg-blue-50 dark:bg-blue-900/20' : '',
                  ].join(' ')}
                  onClick={() => setActiveId(l.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 bg-gray-100 dark:bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                      <ListingIcon kind={l.icon} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 dark:text-slate-100 text-sm truncate">{l.name}</p>
                      <p className="text-xs text-gray-500 dark:text-slate-400">SKU: {l.sku}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${statusPill[l.status.color] || statusPill.orange}`}>
                          {l.status.label}
                        </span>
                        <span className="text-xs text-gray-600 dark:text-slate-400">{l.yourPrice}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Details */}
        <div className="lg:col-span-8 p-6 overflow-y-auto bg-white dark:bg-slate-900" style={{ maxHeight: 600 }}>
          <AnimatePresence mode="wait">
            {active && (
              <motion.div key={active.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h4 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">{active.name}</h4>
                    <p className="text-sm text-gray-600 dark:text-slate-400 mb-3">SKU: {active.sku} • {active.category}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={[
                          'px-3 py-1 rounded-lg text-sm font-bold border',
                          headerBadge?.tone === 'green'
                            ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800'
                            : headerBadge?.tone === 'red'
                              ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800'
                              : 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800',
                        ].join(' ')}
                      >
                        <i className={`fa-solid ${headerBadge?.icon || 'fa-tag'} mr-1`}></i>
                        {headerBadge?.text}
                      </span>
                      <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800">
                        In Stock
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">Your Price</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-slate-100">{active.yourPrice}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                  <MetricCard
                    tone={active.status.color === 'red' ? 'orange' : 'blue'}
                    label="Market Position"
                    value={active.marketPosition}
                    sub={active.marketPositionSub}
                  />
                  <MetricCard
                    tone={active.priceDelta.startsWith('-') ? 'green' : active.status.color === 'red' ? 'red' : 'orange'}
                    label="Price Delta"
                    value={active.priceDelta}
                    sub={active.priceDeltaSub}
                  />
                  <MetricCard tone="purple" label="BSR" value={active.bsr} sub={active.bsrSub} />
                </div>

                {active.actionCard && (
                  <div
                    className={[
                      'border-2 rounded-xl p-4 mb-6',
                      active.actionCard.tone === 'red'
                        ? 'bg-red-50 border-red-300 dark:bg-red-900/10 dark:border-red-800'
                        : 'bg-orange-50 border-orange-300 dark:bg-orange-900/10 dark:border-orange-800',
                    ].join(' ')}
                  >
                    <div className="flex items-start gap-3">
                      <i
                        className={[
                          'fa-solid text-xl',
                          active.actionCard.tone === 'red' ? 'fa-exclamation-circle text-red-600' : 'fa-bell text-orange-600',
                        ].join(' ')}
                      ></i>
                      <div>
                        <h5
                          className={[
                            'font-bold mb-1',
                            active.actionCard.tone === 'red' ? 'text-red-900 dark:text-red-200' : 'text-orange-900 dark:text-orange-200',
                          ].join(' ')}
                        >
                          {active.actionCard.title}
                        </h5>
                        <p
                          className={[
                            'text-sm mb-2',
                            active.actionCard.tone === 'red' ? 'text-red-800 dark:text-red-200' : 'text-orange-800 dark:text-orange-200',
                          ].join(' ')}
                        >
                          {active.actionCard.body}
                        </p>
                        {active.actionCard.cta && (
                          <button className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg text-sm font-medium">
                            {active.actionCard.cta}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="bg-gray-50 dark:bg-slate-800/30 border border-gray-200 dark:border-slate-700 rounded-xl p-4 mb-6">
                  <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-3">Competitor Pricing</h5>
                  <div className="space-y-2">
                    {active.competitorPricing.map((c, i) => {
                      const bbWinner = c.emphasis === 'bb';
                      const downPct = c.emphasis === 'downPct';
                      const highlight = bbWinner ? 'border-2 border-blue-300 dark:border-blue-700' : '';
                      return (
                        <div key={`${c.label}-${i}`} className={`flex items-center justify-between p-2 bg-white dark:bg-slate-900 rounded-lg ${highlight}`}>
                          <div className="flex items-center gap-2">
                            <Dot color={c.dot} />
                            <span className={`text-sm ${bbWinner ? 'font-medium text-gray-900 dark:text-slate-100' : 'text-gray-700 dark:text-slate-300'}`}>{c.label}</span>
                            {bbWinner && (
                              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-bold border border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800">
                                BB Winner
                              </span>
                            )}
                            {downPct && (
                              <span className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs font-bold dark:bg-red-900/20 dark:text-red-300">
                                {c.pct}
                              </span>
                            )}
                          </div>
                          <span className={`text-sm font-bold ${c.dot === 'red' ? 'text-red-700 dark:text-red-300' : 'text-gray-900 dark:text-slate-100'}`}>{c.price}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex gap-3">
                  {(active.ctas || []).map((cta) => (
                    <Button
                      key={cta.label}
                      tone={cta.tone}
                      icon={cta.icon}
                      full={cta.tone !== 'secondary'}
                    >
                      {cta.label}
                    </Button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};

export default PriceMonitoringSection;

