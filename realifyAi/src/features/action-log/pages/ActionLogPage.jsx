import React, { useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import useClickOutside from '@/hooks/useClickOutside';
import {
  INSIGHTS_DATA,
  MARGIN_INSIGHTS_DATA,
  INVENTORY_INSIGHTS_DATA,
  ADS_INSIGHTS_DATA,
  CASH_INSIGHTS_DATA,
} from '@/data/workspaceData';
import { useActionStore } from '@/store/useActionStore';
import { ROUTES } from '@/constants/routes';

const ALL_STATUSES = ['CRITICAL', 'OPPORTUNITY', 'ALERT', 'REVIEW', 'MARKET', 'INSIGHT'];
const ALL_MODULES = ['Sales', 'Margin', 'Inventory', 'Ads', 'Cash'];
const SORT_OPTIONS = [
  { key: 'date-desc', label: 'Newest first' },
  { key: 'date-asc', label: 'Oldest first' },
  { key: 'title-asc', label: 'Title A–Z' },
];

const MODULE_META = {
  sales: { icon: 'fa-dollar-sign', label: 'Sales' },
  margin: { icon: 'fa-chart-line', label: 'Margin' },
  inventory: { icon: 'fa-boxes-stacked', label: 'Inventory' },
  ads: { icon: 'fa-bullhorn', label: 'Ads' },
  cash: { icon: 'fa-money-bill-wave', label: 'Cash' },
};

const ALL_MODULE_DATA = {
  sales: INSIGHTS_DATA,
  margin: MARGIN_INSIGHTS_DATA,
  inventory: INVENTORY_INSIGHTS_DATA,
  ads: ADS_INSIGHTS_DATA,
  cash: CASH_INSIGHTS_DATA,
};

const TYPE_ACTION = {
  CRITICAL: 'EXECUTE',
  OPPORTUNITY: 'SIMULATE',
  ALERT: 'RESOLVE',
  REVIEW: 'REVIEW',
  MARKET: 'VIEW',
  INSIGHT: 'VIEW',
};

function relToTime(str = '') {
  const base = 14 * 60 + 22;
  const m = str.match(/^(\d+(?:\.\d+)?)\s*(min|h|hour)/);
  if (!m) return '14:22:00';
  const mins = m[2] === 'min' ? parseFloat(m[1]) : parseFloat(m[1]) * 60;
  const t = Math.max(0, base - Math.round(mins));
  return `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}:00`;
}

function extractItemInfo(ins) {
  const heading = ins.heading || '';
  const dashIdx = heading.indexOf(' — ');
  const itemName = dashIdx > 0 ? heading.slice(0, dashIdx) : heading;
  const skuMatch = (ins.body || '').match(/\bSKU-\d+\b/);
  const sku = skuMatch ? skuMatch[0] : null;
  return { itemName, sku };
}

const ACTION_LOG_DATA = (() => {
  const rows = [];
  Object.entries(ALL_MODULE_DATA).forEach(([tab, moduleData]) => {
    const arr = moduleData.item;
    if (!arr || arr.length === 0) return;
    arr.forEach((ins, idx) => {
      const { itemName, sku } = extractItemInfo(ins);
      rows.push({
        id: `${tab}-item-${idx}`,
        date: 'Jun 26, 2026',
        time: relToTime(ins.time),
        timeAgo: ins.time || '',
        title: ins.heading,
        description: ins.steps?.[0]?.title ?? (ins.body?.slice(0, 72) + '…'),
        icon: MODULE_META[tab].icon,
        module: MODULE_META[tab].label,
        tab,
        subTabKey: 'item',
        insightTabLabel: 'Item',
        insightArray: arr,
        idx,
        status: ins.type,
        action: TYPE_ACTION[ins.type] ?? 'VIEW',
        itemName,
        sku,
      });
    });
  });
  return rows;
})();

const STATUS_STYLE = {
  CRITICAL: { dot: 'bg-red-500', badge: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400' },
  OPPORTUNITY: { dot: 'bg-green-500', badge: 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400' },
  ALERT: { dot: 'bg-amber-500', badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400' },
  REVIEW: { dot: 'bg-purple-500', badge: 'bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-400' },
  MARKET: { dot: 'bg-blue-500', badge: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400' },
  INSIGHT: { dot: 'bg-gray-400', badge: 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-400' },
};

const ActionLogPage = () => {
  const navigate = useNavigate();
  const { executedMap } = useActionStore();
  const [search, setSearch] = useState('');

  /* ── Filter panel state ── */
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterTab, setFilterTab] = useState('filters');
  const [pendingStatus, setPendingStatus] = useState([]);
  const [pendingModule, setPendingModule] = useState([]);
  const [pendingSort, setPendingSort] = useState('date-desc');
  const [appliedStatus, setAppliedStatus] = useState([]);
  const [appliedModule, setAppliedModule] = useState([]);
  const [appliedSort, setAppliedSort] = useState('date-desc');
  const filterRef = useRef(null);

  useClickOutside(filterRef, filterOpen, () => setFilterOpen(false));

  const openFilter = () => {
    setPendingStatus([...appliedStatus]);
    setPendingModule([...appliedModule]);
    setPendingSort(appliedSort);
    setFilterTab('filters');
    setFilterOpen(true);
  };
  const applyFilter = () => {
    setAppliedStatus([...pendingStatus]);
    setAppliedModule([...pendingModule]);
    setAppliedSort(pendingSort);
    setFilterOpen(false);
  };
  const resetFilter = () => {
    setPendingStatus([]);
    setPendingModule([]);
    setPendingSort('date-desc');
  };
  const toggleStatus = (s) =>
    setPendingStatus(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
  const toggleModule = (m) =>
    setPendingModule(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m]);

  const activeFilterCount = appliedStatus.length + appliedModule.length + (appliedSort !== 'date-desc' ? 1 : 0);

  const filtered = useMemo(() => {
    let list = ACTION_LOG_DATA.filter(item => {
      if (search && !item.title.toLowerCase().includes(search.toLowerCase()) &&
        !item.description.toLowerCase().includes(search.toLowerCase())) return false;
      if (appliedStatus.length > 0) {
        const displayStatus = executedMap[item.id] ? 'EXECUTED' : item.status;
        if (!appliedStatus.includes(displayStatus)) return false;
      }
      if (appliedModule.length > 0 && !appliedModule.includes(item.module)) return false;
      return true;
    });
    if (appliedSort === 'date-asc') list = [...list].reverse();
    if (appliedSort === 'title-asc') list = [...list].sort((a, b) => a.title.localeCompare(b.title));
    return list;
  }, [search, appliedStatus, appliedModule, appliedSort, executedMap]);

  return (
    <DashboardLayout
      title="Action Log"
      subtitle="Track all simulation events and outcomes"
      showTabs={false}
      filters={null}
      showAIPrompt={false}
    >
      <div className="flex items-center justify-between mb-4">
        <p className="text-[11px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">
          {/* Simulation Events */}
        </p>
        <div className="flex items-center gap-2">
          <div className="relative">
            <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-xs pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search"
              className="pl-8 pr-3 py-1.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-xs text-gray-700 dark:text-slate-300 placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:border-gray-300 dark:focus:border-slate-600 transition-colors w-54"
            />
          </div>
          <div className="relative" ref={filterRef}>
            <button
              onClick={openFilter}
              className={`flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-xs font-medium transition-colors ${activeFilterCount > 0
                  ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100'
                  : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700'
                }`}
            >
              <i className="fa-solid fa-sliders text-[10px]" />
              Filter
              {activeFilterCount > 0 && (
                <span className="ml-0.5 w-4 h-4 rounded-full bg-white/20 dark:bg-gray-900/20 text-[10px] font-bold flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>

            {filterOpen && (
              <div className="absolute top-full mt-2 right-0 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl shadow-xl z-[9999] w-[300px] overflow-hidden flex flex-col">
                <div className="flex" style={{ minHeight: 180 }}>
                  {/* Left tabs */}
                  <div className="w-[100px] flex-shrink-0 border-r border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800/40 p-2 flex flex-col gap-0.5">
                    {[
                      { key: 'filters', label: 'Filters', badge: pendingStatus.length > 0 },
                      { key: 'module', label: 'Module', badge: pendingModule.length > 0 },
                      { key: 'sort', label: 'Sort', badge: pendingSort !== 'date-desc' },
                    ].map(tab => (
                      <button key={tab.key} onClick={() => setFilterTab(tab.key)}
                        className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs text-left transition-colors ${filterTab === tab.key
                            ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 font-semibold shadow-sm'
                            : 'text-gray-500 dark:text-slate-400 hover:bg-white/70 dark:hover:bg-slate-900/50 font-medium'
                          }`}>
                        <span className={`w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${filterTab === tab.key ? 'border-gray-900 dark:border-slate-100' : 'border-gray-300 dark:border-slate-600'
                          }`}>
                          {filterTab === tab.key && <span className="w-1.5 h-1.5 rounded-full bg-gray-900 dark:bg-slate-100" />}
                        </span>
                        <span className="truncate">{tab.label}</span>
                        {tab.badge && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />}
                      </button>
                    ))}
                  </div>

                  {/* Right content */}
                  <div className="flex-1 p-3.5">
                    {filterTab === 'filters' && (
                      <div>
                        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5">Status</p>
                        <div className="flex flex-col gap-1.5">
                          {['EXECUTED', ...ALL_STATUSES].map(s => (
                            <button key={s} onClick={() => toggleStatus(s)}
                              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${pendingStatus.includes(s)
                                  ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100'
                                  : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:border-gray-300'
                                }`}>
                              {s}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {filterTab === 'module' && (
                      <div>
                        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5">Module</p>
                        <div className="flex flex-col gap-1.5">
                          {ALL_MODULES.map(m => (
                            <button key={m} onClick={() => toggleModule(m)}
                              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${pendingModule.includes(m)
                                  ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100'
                                  : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:border-gray-300'
                                }`}>
                              {m}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {filterTab === 'sort' && (
                      <div>
                        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5">Sort by</p>
                        <div className="flex flex-col gap-0.5">
                          {SORT_OPTIONS.map(opt => (
                            <button key={opt.key} onClick={() => setPendingSort(opt.key)}
                              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${pendingSort === opt.key
                                  ? 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-slate-100 font-semibold'
                                  : 'text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium'
                                }`}>
                              <span className={`w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${pendingSort === opt.key ? 'border-gray-900 dark:border-slate-100' : 'border-gray-300 dark:border-slate-600'
                                }`}>
                                {pendingSort === opt.key && <span className="w-1.5 h-1.5 rounded-full bg-gray-900 dark:bg-slate-100" />}
                              </span>
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-800 flex items-center justify-between gap-2">
                  <button onClick={resetFilter}
                    className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors">
                    Reset
                  </button>
                  <button onClick={applyFilter}
                    className="px-5 py-2 rounded-xl bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition-colors">
                    Apply
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 dark:border-slate-800">
                <th className="px-3 py-3 text-center text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide w-10">#</th>
                <th className="px-5 py-3 text-left text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide whitespace-nowrap">Timestamp</th>
                <th className="px-5 py-3 text-left text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide">Event Title</th>
                <th className="px-5 py-3 text-left text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide whitespace-nowrap">Item</th>
                <th className="px-5 py-3 text-left text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide whitespace-nowrap">Module</th>
                <th className="px-5 py-3 text-left text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide">Status</th>
                <th className="px-5 py-3 text-right text-[11px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800/60">
              {filtered.map((item, filteredIndex) => {
                const isExecuted = !!executedMap[item.id];
                const executedAt = executedMap[item.id];
                const st = isExecuted
                  ? { dot: 'bg-green-500', badge: 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400' }
                  : STATUS_STYLE[item.status];
                const isPrimary = item.action === 'EXECUTE' || item.action === 'RESOLVE';
                const goToInsight = () => navigate(
                  `${ROUTES.WORKSPACE}/insight/${item.tab}/${item.idx}`,
                  { state: { insights: item.insightArray, currentIndex: item.idx, domain: item.tab, insightTab: item.insightTabLabel, sourceRoute: '/action-log', executed: isExecuted, executedAt: executedAt || null } }
                );
                return (
                  <tr
                    key={item.id}
                    onClick={goToInsight}
                    className="hover:bg-gray-50 dark:hover:bg-slate-800/30 transition-colors cursor-pointer"
                  >
                    {/* # */}
                    <td className="px-3 py-4 text-center whitespace-nowrap">
                      <span className="text-xs text-gray-400 dark:text-slate-500 font-semibold">{filteredIndex + 1}</span>
                    </td>
                    {/* Timestamp */}
                    <td className="px-5 py-4 whitespace-nowrap">
                      <div className="text-xs text-gray-700 dark:text-slate-300 font-medium">{item.date}</div>
                      <div className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">{item.time}</div>
                      {isExecuted && (
                        <div className="group relative flex items-center gap-1 mt-1 w-fit">
                          <i className="fa-solid fa-circle-check text-green-500 text-[9px]" />
                          <span className="text-[10px] text-green-600 dark:text-green-400 font-medium">{executedAt}</span>
                          <div className="pointer-events-none absolute bottom-full left-0 mb-1.5 whitespace-nowrap rounded-lg bg-gray-900 dark:bg-slate-700 px-2 py-1 text-[10px] text-white opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            Executed on
                          </div>
                        </div>
                      )}
                    </td>
                    {/* Event Title */}
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isExecuted ? 'bg-green-600 dark:bg-green-700' : 'bg-gray-900 dark:bg-slate-700'}`}>
                          <i className={`fa-solid ${isExecuted ? 'fa-circle-check' : item.icon} text-white dark:text-slate-200 text-[11px]`} />
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-gray-900 dark:text-slate-100">{item.title}</div>
                          <div className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">{item.description}</div>
                        </div>
                      </div>
                    </td>
                    {/* Item */}
                    <td className="px-5 py-4 max-w-[160px]">
                      <div className="text-xs font-semibold text-gray-700 dark:text-slate-300 truncate">{item.itemName}</div>
                      {item.sku && (
                        <span className="text-[10px] font-sans bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 px-1.5 py-0.5 rounded mt-0.5 inline-block">{item.sku}</span>
                      )}
                    </td>
                    {/* Module */}
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-slate-800 text-xs font-semibold text-gray-600 dark:text-slate-400">
                        <i className={`fa-solid ${item.icon} text-[10px]`} />
                        {item.module}
                      </span>
                    </td>
                    {/* Status */}
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold ${st?.badge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${st?.dot}`} />
                        {isExecuted ? 'EXECUTED' : item.status}
                      </span>
                    </td>
                    {/* Actions */}
                    <td className="px-5 py-4 whitespace-nowrap text-right" onClick={e => e.stopPropagation()}>
                      {isExecuted ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(ROUTES.WORKSPACE_ROLLBACK, {
                              state: {
                                insight: item.insightArray[item.idx],
                                domain: item.tab,
                                executedAt: executedAt || null,
                                backState: null,
                              },
                            });
                          }}
                          className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold rounded-lg active:scale-[0.98] transition-all"
                        >
                          ROLL BACK
                        </button>
                      ) : isPrimary ? (
                        <button
                          onClick={goToInsight}
                          className="px-3 py-1.5 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-semibold rounded-lg hover:bg-gray-700 dark:hover:bg-slate-200 active:scale-[0.98] transition-all"
                        >
                          {item.action}
                        </button>
                      ) : (
                        <button
                          onClick={goToInsight}
                          className="px-3 py-1.5 bg-white dark:bg-transparent border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 text-xs font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 active:scale-[0.98] transition-all"
                        >
                          {item.action}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 dark:border-slate-800">
          <span className="text-xs text-gray-400 dark:text-slate-500">
            Showing {filtered.length} of {ACTION_LOG_DATA.length} insights
          </span>
          <div className="flex items-center gap-1">
            <button className="px-3 py-1.5 text-xs text-gray-600 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 font-medium transition-colors">
              Previous
            </button>
            <button className="px-3 py-1.5 text-xs text-gray-900 dark:text-slate-100 hover:text-gray-700 dark:hover:text-slate-300 font-semibold transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ActionLogPage;
