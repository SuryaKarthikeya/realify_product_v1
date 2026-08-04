import React, { useState, useRef } from 'react';
import { formatCompactCurrency } from '@/utils/formatters';
import { useLocation, useNavigate } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import DashboardLayout from '@/layouts/DashboardLayout';
import MarketplaceSyncBanner from '@/components/feedback/MarketplaceSyncBanner';
import useClickOutside from '@/hooks/useClickOutside';
import { salesWatchlistItems } from '@/data/watchlistData';
import { ITEM_SKU_DATA } from '@/data/workspaceData';
import { PERF_STATS, TREND_DATA, ACTION_BADGE, defaultDescription } from '@/features/product-view/data/productViewData';
import { CAL_MONTHS, CAL_WEEKDAYS } from '@/constants/filterOptions';
import CompactWatchlistCard from '@/features/product-view/components/CompactWatchlistCard';
import ProductFilterPanel from '@/features/product-view/components/ProductFilterPanel';
import { ROUTES } from '@/constants/routes';


// ─── Product View Page ────────────────────────────────────────────────────────

const ProductViewPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();

  const activePlatforms = JSON.parse(localStorage.getItem('active_platforms') || '["shopify"]');
  const [, setActiveTime] = useState('30d');
  const [activeTab, setActiveTab] = useState(
    ['Amazon', 'Shopify', 'Walmart'].find(t => activePlatforms.includes(t.toLowerCase())) || 'Amazon'
  );
  const [insightCategory, setInsightCategory] = useState('All');
  const [activeWatchlistIdx, setActiveWatchlistIdx] = useState(null);
  const [prevWatchlistIdx, setPrevWatchlistIdx] = useState(activeWatchlistIdx);
  if (activeWatchlistIdx !== prevWatchlistIdx) {
    setPrevWatchlistIdx(activeWatchlistIdx);
    setInsightCategory('All');
  }
  const [actionsViewMode, setActionsViewMode] = useState('list');
  const [activePerfStat, setActivePerfStat] = useState('revenue');
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editPrice, setEditPrice] = useState('');
  const [savedName, setSavedName] = useState(null);
  const [savedDesc, setSavedDesc] = useState(null);
  const [savedPrice, setSavedPrice] = useState(null);

  // Filter panel state
  const [filterOpen, setFilterOpen] = useState(false);
  const [pendingDate, setPendingDate] = useState('30d');
  const [customRange, setCustomRange] = useState({ start: null, end: null });
  const [hoverDate, setHoverDate] = useState(null);
  const [calViewMonth, setCalViewMonth] = useState(() => {
    const d = new Date();
    return { year: d.getFullYear(), month: d.getMonth() };
  });
  const filterRef = useRef(null);

  useClickOutside(filterRef, filterOpen, () => setFilterOpen(false));

  const initialProduct = state?.product;
  const from = state?.from || -1;
  const fromState = state?.fromState || null;

  if (!initialProduct) {
    navigate(-1);
    return null;
  }

  const watchlistItems = salesWatchlistItems;

  const buildProductFromWatchlist = (item) => ({
    name: item.title,
    image: item.image || null,
    sku: item.sku,
    description: defaultDescription(item.title),
    sellingPrice: '$149.99',
    unitCost: '$62.59',
    margin: '58.2%',
    stock: item.stock || '—',
    kpiGroups: initialProduct.kpiGroups,
    watchlistItem: item,
    insights: initialProduct.insights,
  });

  const activeProduct = activeWatchlistIdx !== null
    ? buildProductFromWatchlist(watchlistItems[activeWatchlistIdx])
    : initialProduct;

  const displayPrice = savedPrice || activeProduct.price || activeProduct.sellingPrice || '$149.99';
  const displayDescription = savedDesc || activeProduct.description || defaultDescription(activeProduct.name);
  const fieldLabelClass = 'text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1 block';

  const initialActiveIdx = watchlistItems.findIndex(
    (item) => item.title?.toLowerCase() === initialProduct.name?.toLowerCase()
  );

  const productDd = ITEM_SKU_DATA.deepDive[activeProduct.sku] ||
    Object.values(ITEM_SKU_DATA.deepDive)
      .filter(d => typeof d.name === 'string')
      .find(d => d.name?.toLowerCase() === activeProduct.name?.toLowerCase()) || null;

  const productActions = productDd ? productDd.actions.map((a, i) => ({ ...a, id: i + 1 })) : [];
  const actionTypes = ['All', ...new Set(productActions.map(a => a.type))];
  const filteredActions = insightCategory === 'All'
    ? productActions
    : productActions.filter(a => a.type === insightCategory);

  const handleActionSelect = (action) => {
    if (!productDd) return;
    const allSteps = productDd.actions.map((a, i) => ({
      id: i + 1,
      title: a.title,
      sub: a.sub,
      type: a.type,
    }));
    const clickedIdx = productDd.actions.findIndex(a => a.title === action.title);
    const insight = {
      heading: productDd.name,
      body: productDd.keyInsight || `${productDd.name} has specific actions requiring your attention. Review the recommended actions below.`,
      type: 'INSIGHT',
      time: '2 min ago',
      steps: allSteps,
    };
    navigate(`${ROUTES.WORKSPACE}/insight/revenue/0`, {
      state: {
        insights: [insight],
        currentIndex: 0,
        domain: 'sales',
        insightTab: 'Item',
        sourceRoute: '/product-view',
        productViewState: { product: activeProduct, from },
        initialStepId: clickedIdx >= 0 ? clickedIdx + 1 : 1,
      },
    });
  };

  const channelTabs = ['Amazon', 'Shopify', 'Walmart'].filter(t => activePlatforms.includes(t.toLowerCase()));

  const activeDateLabel = pendingDate === '7d' ? 'Last 7 Days'
    : pendingDate === '90d' ? 'Last 90 Days'
      : pendingDate === '30d' ? null
        : (customRange.start && customRange.end)
          ? `${customRange.start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${customRange.end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
          : null;

  return (
    <DashboardLayout
      title={activeProduct.name}
      subtitle="Product Analysis"
      showTabs={false}
    >
      {/* 70 / 30 split on desktop — main content left, watchlist right. Mobile: single column, no watchlist. */}
      <div className="flex flex-col sm:grid sm:grid-cols-10 gap-5 items-start">

        {/* Left 70% — product info + actions */}
        <div className="sm:col-span-7 flex flex-col gap-5">

          {/* Channel tabs + back button (left) + filter (right) */}
          <div className="flex items-center gap-1 border-b border-gray-200 dark:border-slate-800 -mt-1">
            <button
              onClick={() => navigate(from, fromState ? { state: fromState } : undefined)}
              className="flex items-center justify-center text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-200 transition-colors flex-shrink-0 mr-2 mb-px"
            >
              <i className="fa-solid fa-arrow-left text-sm" />
            </button>
            {channelTabs.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2.5 text-xs font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${activeTab === tab
                    ? 'text-gray-900 dark:text-slate-100 border-gray-900 dark:border-slate-200 font-semibold'
                    : 'text-gray-400 dark:text-slate-500 border-transparent hover:text-gray-700 dark:hover:text-slate-300'
                  }`}
              >
                {tab}
              </button>
            ))}
            <div className="flex-1" />
            <div className="relative flex items-center gap-2 pb-0.5" ref={filterRef}>
              {activeDateLabel && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-full text-xs font-medium text-gray-700 dark:text-slate-300 shadow-sm">
                  {activeDateLabel}
                  <button onClick={() => { setPendingDate('30d'); setCustomRange({ start: null, end: null }); setActiveTime('30d'); }} className="text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 ml-0.5 transition">
                    <i className="fa-solid fa-xmark text-[9px]" />
                  </button>
                </span>
              )}
              <button
                onClick={() => setFilterOpen(v => !v)}
                className={`flex items-center gap-1.5 px-3 h-7 rounded-xl border transition-all text-xs font-medium ${filterOpen
                    ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-100 text-white dark:text-gray-900'
                    : 'bg-white dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:border-gray-300 dark:hover:border-slate-600'
                  }`}
              >
                <i className="fa-solid fa-sliders text-[11px]" />
                Filter
              </button>
              {filterOpen && (
                <ProductFilterPanel
                  pendingDate={pendingDate}
                  setPendingDate={setPendingDate}
                  customRange={customRange}
                  setCustomRange={setCustomRange}
                  hoverDate={hoverDate}
                  setHoverDate={setHoverDate}
                  calViewMonth={calViewMonth}
                  setCalViewMonth={setCalViewMonth}
                  onClose={() => setFilterOpen(false)}
                  onUpdate={() => {
                    setActiveTime(pendingDate || 'Custom');
                    setFilterOpen(false);
                  }}
                />
              )}
            </div>
          </div>

          {/* Product info card */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row gap-5">

              {/* Product image */}
              <div className="w-full h-44 sm:w-44 sm:h-44 bg-gray-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center flex-shrink-0 border border-gray-100 dark:border-slate-700 overflow-hidden">
                {activeProduct.image ? (
                  <img src={activeProduct.image} alt={activeProduct.name} className="max-h-full max-w-full object-contain p-2" />
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <i className="fa-solid fa-box text-4xl text-gray-300 dark:text-slate-600" />
                    <span className="text-[10px] text-gray-400 dark:text-slate-500">No image</span>
                  </div>
                )}
              </div>

              {/* Product details */}
              <div className="flex-1 min-w-0">
                {/* Status tags */}
                <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                  <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-[10px] font-bold rounded-lg">Low Stock</span>
                  <span className="px-2 py-0.5 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 text-[10px] font-bold rounded-lg">Electronics</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-[10px] font-bold rounded-lg">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full" /> Active
                  </span>
                </div>

                {isEditing ? (
                  <div className="space-y-3">
                    <MarketplaceSyncBanner onGoToMarketplace={() => { }} />
                    <div>
                      <label className={fieldLabelClass}>Product Name</label>
                      <input
                        type="text"
                        value={editName}
                        onChange={e => setEditName(e.target.value)}
                        className="w-full px-3 py-2 text-sm font-bold text-gray-900 dark:text-slate-100 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-slate-600 transition"
                      />
                    </div>
                    <div>
                      <label className={fieldLabelClass}>Price</label>
                      <input
                        type="text"
                        value={editPrice}
                        onChange={e => setEditPrice(e.target.value)}
                        className="w-40 px-3 py-2 text-sm font-bold text-gray-900 dark:text-slate-100 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-slate-600 transition"
                      />
                    </div>
                    <div>
                      <label className={fieldLabelClass}>Description</label>
                      <textarea
                        value={editDesc}
                        onChange={e => setEditDesc(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 text-sm text-gray-600 dark:text-slate-400 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-slate-600 transition resize-none leading-relaxed"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { setSavedName(editName); setSavedDesc(editDesc); setSavedPrice(editPrice); setIsEditing(false); }}
                        className="px-4 py-1.5 rounded-xl bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setIsEditing(false)}
                        className="px-4 py-1.5 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2 mb-0.5">
                      <h2 className="text-lg font-bold text-gray-900 dark:text-slate-100 leading-snug">{savedName || activeProduct.name}</h2>
                      <button
                        onClick={() => {
                          setEditName(savedName || activeProduct.name);
                          setEditDesc(displayDescription);
                          setEditPrice(displayPrice);
                          setIsEditing(true);
                        }}
                        className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-lg text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                        title="Edit"
                      >
                        <i className="fa-solid fa-pen text-[10px]" />
                      </button>
                    </div>
                    <p className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">
                      {displayPrice}
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-slate-400 mb-3 font-sans">
                      SKU: {activeProduct.sku || activeProduct.watchlistItem?.sku || 'WH-PRO-2024'} · Realify Audio · Added Mar 14, 2026
                    </p>
                    <p className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed">
                      {displayDescription}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Performance Overview */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">Performance Overview</h3>
              <span className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-full text-[11px] font-medium text-gray-500 dark:text-slate-400">
                <i className="fa-regular fa-calendar text-[10px]" /> Last 7 Days
              </span>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Stat cards */}
              <div className="flex flex-col gap-2 w-full sm:w-[200px] sm:flex-shrink-0">
                {PERF_STATS.map(stat => (
                  <button
                    key={stat.key}
                    onClick={() => setActivePerfStat(stat.key)}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${activePerfStat === stat.key
                        ? 'border-gray-900 dark:border-slate-100 bg-gray-50 dark:bg-slate-800'
                        : 'border-gray-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800/60'
                      }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${activePerfStat === stat.key ? 'bg-gray-200 dark:bg-slate-700' : 'bg-gray-100 dark:bg-slate-800'}`}>
                      <i className={`fa-solid ${stat.icon} text-[10px] text-gray-600 dark:text-slate-300`} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide leading-tight">{stat.label}</p>
                      <div className="flex items-baseline gap-1.5 mt-0.5">
                        <span className="text-sm font-bold text-gray-900 dark:text-slate-100 leading-tight">{stat.value}</span>
                        <span className={`text-[10px] font-bold ${stat.isPositive ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>{stat.change}</span>
                      </div>
                      <p className="text-[9px] text-gray-400 dark:text-slate-500 mt-0.5">{stat.sub}</p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Trend chart */}
              <div className="w-full h-[260px] sm:h-auto sm:flex-1 min-w-0">
                {(() => {
                  const stat = PERF_STATS.find(s => s.key === activePerfStat);
                  const data = TREND_DATA[activePerfStat];
                  const isRevenue = activePerfStat === 'revenue';
                  return (
                    <div className="h-full flex flex-col">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold text-gray-600 dark:text-slate-300">{stat?.label} Trend</p>
                        <span className="flex items-center gap-1 text-[10px] font-medium text-gray-400 dark:text-slate-500">
                          <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: stat?.color }} />
                          Last 7 Days
                        </span>
                      </div>
                      <div className="flex-1" style={{ minHeight: 160 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
                            <defs>
                              <linearGradient id="perfGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={stat?.color} stopOpacity={0.15} />
                                <stop offset="95%" stopColor={stat?.color} stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'currentColor', fontSize: 10 }} className="text-gray-400 dark:text-slate-500" dy={6} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: 'currentColor', fontSize: 10 }} className="text-gray-400 dark:text-slate-500" tickFormatter={v => isRevenue ? formatCompactCurrency(v, { suffix: 'K' }) : v} width={40} />
                            <Tooltip
                              contentStyle={{ backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: '11px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                              formatter={v => [isRevenue ? `$${v.toLocaleString()}` : v, stat?.label]}
                            />
                            <Area type="monotone" dataKey="value" stroke={stat?.color} strokeWidth={2} fill="url(#perfGradient)" dot={false} activeDot={{ r: 4, strokeWidth: 0, fill: stat?.color }} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>

          {/* Actions section */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
            <div className="px-5 pt-4 pb-3 border-b border-gray-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-slate-100">Actions</h3>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">Click to view deep-dive</p>
                </div>
                <div className="flex items-center gap-1 bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700 rounded-xl p-1">
                  <button
                    onClick={() => setActionsViewMode('list')}
                    className={`px-2.5 py-1.5 rounded-lg text-xs transition ${actionsViewMode === 'list' ? 'bg-gray-900 text-white dark:bg-slate-100 dark:text-gray-900' : 'text-gray-500 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700'}`}
                  >
                    <i className="fa-solid fa-list" />
                  </button>
                  <button
                    onClick={() => setActionsViewMode('grid')}
                    className={`px-2.5 py-1.5 rounded-lg text-xs transition ${actionsViewMode === 'grid' ? 'bg-gray-900 text-white dark:bg-slate-100 dark:text-gray-900' : 'text-gray-500 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700'}`}
                  >
                    <i className="fa-solid fa-grip" />
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                {actionTypes.map(tab => (
                  <button
                    key={tab}
                    onClick={() => setInsightCategory(tab)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition whitespace-nowrap ${insightCategory === tab
                        ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 shadow-sm'
                        : 'bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300'
                      }`}
                  >
                    {tab === 'All' ? 'All' : tab.charAt(0) + tab.slice(1).toLowerCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className={`${actionsViewMode === 'grid' ? 'grid grid-cols-2' : 'flex flex-col'} gap-3 p-4`}>
              {filteredActions.length === 0 && (
                <p className="col-span-2 text-center text-xs text-gray-400 dark:text-slate-500 py-5">No actions available.</p>
              )}
              {filteredActions.map(action => (
                <button
                  key={action.id}
                  onClick={() => handleActionSelect(action)}
                  className="text-left p-4 border border-gray-200 dark:border-slate-800 rounded-xl hover:border-gray-300 dark:hover:border-slate-600 hover:shadow-md transition-all bg-white dark:bg-slate-900 group"
                >
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`px-1.5 py-0.5 text-[9px] font-bold uppercase rounded-md ${ACTION_BADGE[action.type] || 'bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-300'}`}>
                      {action.type}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-1 leading-snug group-hover:text-brand dark:group-hover:text-gray-200 transition-colors">
                    {action.title}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-slate-400 leading-relaxed line-clamp-2">
                    {action.sub}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right 30% — Watchlist, desktop only */}
        <div className="hidden sm:block sm:col-span-3">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden sticky top-4">
            <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-800">
              <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100">Watchlist</h3>
              <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">Click to view</p>
            </div>
            <div className="p-3 flex flex-col gap-2">
              {watchlistItems.map((item, idx) => {
                const isActive =
                  activeWatchlistIdx === idx ||
                  (activeWatchlistIdx === null && idx === initialActiveIdx);
                return (
                  <button
                    key={idx}
                    onClick={() => setActiveWatchlistIdx(idx)}
                    className="w-full text-left"
                  >
                    <div className={`rounded-xl transition-all ring-2 ${isActive ? 'ring-blue-400 dark:ring-blue-500' : 'ring-transparent'}`}>
                      <CompactWatchlistCard {...item} />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ProductViewPage;
