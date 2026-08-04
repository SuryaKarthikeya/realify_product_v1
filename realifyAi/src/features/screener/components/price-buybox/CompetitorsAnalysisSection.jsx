import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const cx = (...parts) => parts.filter(Boolean).join(' ');

const badgeStyleByType = {
  baseline: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800',
  aggressive: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800',
  premium: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-300 dark:border-purple-800',
  balanced: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800',
  direct: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800',
};

const iconBgByType = {
  baseline: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300',
  aggressive: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-300',
  premium: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300',
  balanced: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-300',
  direct: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-300',
};

const threatStyleByThreat = {
  high: 'text-red-700 dark:text-red-300',
  medium: 'text-yellow-700 dark:text-yellow-300',
  low: 'text-slate-700 dark:text-slate-300',
};

const defaultCompetitors = [
  {
    id: 'your-brand',
    name: 'Your Brand',
    tag: 'Baseline',
    tagType: 'baseline',
    icon: 'fa-building',
    ctaLabel: 'Dashboard',
    ctaTone: 'secondary',
    avgPrice: '$62.30',
    buyBoxRate: '72%',
    products: '370',
    promoRate: '24%',
    strategyTitle: 'Value Leader',
    strategyBody: 'Competitive pricing with strong buy box presence',
    recentTitle: '+5% Buy Box Rate',
    recentBody: 'Improved over last 7 days',
    threatTitle: 'Low',
    threatBody: 'Stable position relative to peers',
    threatLevel: 'low',
  },
  {
    id: 'techmaster-pro',
    name: 'TechMaster Pro',
    tag: 'Aggressive Pricer',
    tagType: 'aggressive',
    icon: 'fa-building',
    ctaLabel: 'Monitor',
    ctaTone: 'primary',
    avgPrice: '$58.90',
    buyBoxRate: '68%',
    products: '542',
    promoRate: '42%',
    strategyTitle: 'Aggressive Discounter',
    strategyBody: 'High promotion rate, undercutting market average by 5.5%',
    recentTitle: '-8% Price Drop',
    recentBody: 'Major price reduction last week',
    threatTitle: 'High',
    threatBody: 'Direct competitor with aggressive tactics',
    threatLevel: 'high',
  },
  {
    id: 'elitegadgets',
    name: 'EliteGadgets',
    tag: 'Premium Brand',
    tagType: 'premium',
    icon: 'fa-building',
    ctaLabel: 'Monitor',
    ctaTone: 'primary',
    avgPrice: '$78.40',
    buyBoxRate: '45%',
    products: '289',
    promoRate: '12%',
    strategyTitle: 'Premium Positioning',
    strategyBody: '25.8% price premium, focuses on quality over volume',
    recentTitle: 'Stable Pricing',
    recentBody: 'Minimal price fluctuations',
    threatTitle: 'Medium',
    threatBody: 'Different segment, limited overlap',
    threatLevel: 'medium',
  },
  {
    id: 'valuemart-direct',
    name: 'ValueMart Direct',
    tag: 'Balanced',
    tagType: 'balanced',
    icon: 'fa-building',
    ctaLabel: 'Monitor',
    ctaTone: 'primary',
    avgPrice: '$64.20',
    buyBoxRate: '58%',
    products: '623',
    promoRate: '31%',
    strategyTitle: 'Balanced Approach',
    strategyBody: 'Moderate pricing with consistent promotion strategy',
    recentTitle: '+3.1% vs You',
    recentBody: 'Slightly above your pricing',
    threatTitle: 'Medium',
    threatBody: 'Similar strategy, watch closely',
    threatLevel: 'medium',
  },
  {
    id: 'smartbuy-co',
    name: 'SmartBuy Co',
    tag: 'Direct Competitor',
    tagType: 'direct',
    icon: 'fa-building',
    ctaLabel: 'Monitor',
    ctaTone: 'primary',
    avgPrice: '$61.80',
    buyBoxRate: '62%',
    products: '412',
    promoRate: '28%',
    strategyTitle: 'Direct Threat',
    strategyBody: 'Very similar pricing and promotion strategy to yours',
    recentTitle: '-0.8% vs You',
    recentBody: 'Slightly undercutting your prices',
    threatTitle: 'High',
    threatBody: 'Close competitor, monitor actively',
    threatLevel: 'high',
  },
];

const CtaButton = ({ tone = 'primary', children }) => (
  <button
    className={cx(
      'px-3 py-1 rounded-lg text-xs font-medium transition border',
      tone === 'primary'
        ? 'bg-brand text-white border-brand hover:bg-brand-hover dark:bg-gray-600 dark:border-gray-500 dark:hover:bg-gray-500'
        : 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200 border-gray-200 dark:border-slate-700 hover:bg-gray-200 dark:hover:bg-slate-700'
    )}
  >
    {children}
  </button>
);

const CompetitorsAnalysisSection = ({ competitors = defaultCompetitors }) => {
  const [expandedIds, setExpandedIds] = useState([]);

  const ids = useMemo(() => competitors.map((c) => c.id), [competitors]);

  const toggle = (id) => {
    setExpandedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const expandAll = () => setExpandedIds(ids);
  const collapseAll = () => setExpandedIds([]);

  return (
    <section className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Competitors Analysis</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400">Detailed comparison of pricing strategies and market positioning</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="px-3 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-medium text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition"
          >
            Expand all
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-medium text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition"
          >
            Collapse
          </button>
          <button className="px-4 py-2 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 rounded-xl transition shadow-sm text-sm font-medium">
            <i className="fa-solid fa-plus mr-2"></i>Add Competitor
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {competitors.map((c) => {
          const expanded = expandedIds.includes(c.id);
          return (
            <div key={c.id} className="border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden">
              <button
                type="button"
                onClick={() => toggle(c.id)}
                className="w-full text-left p-4 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800/40 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className={cx('w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0', iconBgByType[c.tagType])}>
                      <i className={cx('fa-solid', c.icon)}></i>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="font-bold text-gray-900 dark:text-slate-100 truncate">{c.name}</p>
                        <span className={cx('px-2 py-1 rounded-lg text-xs font-medium border', badgeStyleByType[c.tagType])}>{c.tag}</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500 dark:text-slate-400">Avg Price</p>
                          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{c.avgPrice}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-slate-400">Buy Box Rate</p>
                          <p className={cx('text-sm font-bold', c.tagType === 'baseline' || c.tagType === 'direct' ? 'text-green-700 dark:text-green-400' : 'text-orange-700 dark:text-orange-400')}>
                            {c.buyBoxRate}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-slate-400">Products</p>
                          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{c.products}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-slate-400">Promotion Rate</p>
                          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{c.promoRate}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 ml-4">
                    <CtaButton tone={c.ctaTone}>{c.ctaLabel}</CtaButton>
                    <i className={cx('fa-solid fa-chevron-down text-gray-400 transition-transform', expanded && 'rotate-180')}></i>
                  </div>
                </div>
              </button>

              <AnimatePresence initial={false}>
                {expanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="bg-gray-50 dark:bg-slate-800/30 border-t border-gray-200 dark:border-slate-800 overflow-hidden"
                  >
                    <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-white dark:bg-slate-900 rounded-lg p-3 border border-gray-100 dark:border-slate-800">
                        <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">Strategy Profile</p>
                        <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 mb-1">{c.strategyTitle}</p>
                        <p className="text-xs text-gray-600 dark:text-slate-400">{c.strategyBody}</p>
                      </div>
                      <div className="bg-white dark:bg-slate-900 rounded-lg p-3 border border-gray-100 dark:border-slate-800">
                        <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">Recent Changes</p>
                        <p className={cx('text-sm font-semibold mb-1', c.recentTitle.startsWith('+') ? 'text-green-700 dark:text-green-400' : c.recentTitle.startsWith('-') ? 'text-red-700 dark:text-red-400' : 'text-gray-900 dark:text-slate-100')}>
                          {c.recentTitle}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-slate-400">{c.recentBody}</p>
                      </div>
                      <div className="bg-white dark:bg-slate-900 rounded-lg p-3 border border-gray-100 dark:border-slate-800">
                        <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">Threat Level</p>
                        <p className={cx('text-sm font-semibold mb-1', threatStyleByThreat[c.threatLevel])}>{c.threatTitle}</p>
                        <p className="text-xs text-gray-600 dark:text-slate-400">{c.threatBody}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default CompetitorsAnalysisSection;

