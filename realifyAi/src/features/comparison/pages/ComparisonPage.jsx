import React, { useMemo, useState } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import ToggleSwitch from '@/components/ui/ToggleSwitch';
import { ATTRIBUTE_CATEGORIES, ATTRIBUTES, findProductBySku } from '@/features/comparison/data/comparisonData';

const MIN_SLOTS = 1;
const MAX_SLOTS = 6;
const DEFAULT_SLOTS = ['', '', ''];

const inventoryBadgeClass = (value) => {
  const v = (value || '').toLowerCase();
  if (v.includes('in stock')) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
  if (v.includes('low')) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
  if (v.includes('out')) return 'bg-gray-200 text-gray-600 dark:bg-slate-700 dark:text-slate-300';
  return 'bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-300';
};

const ComparisonPage = () => {
  const [skuSlots, setSkuSlots] = useState(DEFAULT_SLOTS);
  const [showDiffOnly, setShowDiffOnly] = useState(false);
  const [collapsedCategories, setCollapsedCategories] = useState({});

  const slotResults = useMemo(
    () =>
      skuSlots.map((raw) => {
        const trimmed = raw.trim();
        if (!trimmed) return { raw, status: 'empty', product: null };
        const product = findProductBySku(trimmed);
        return product ? { raw, status: 'found', product } : { raw, status: 'not-found', product: null };
      }),
    [skuSlots]
  );

  const activeColumns = slotResults.filter((r) => r.status === 'found');
  const hasProducts = activeColumns.length > 0;

  const handleSkuChange = (idx, value) => {
    setSkuSlots((prev) => prev.map((v, i) => (i === idx ? value : v)));
  };

  const handleRemoveSlot = (idx) => {
    setSkuSlots((prev) =>
      prev.length <= MIN_SLOTS ? prev.map((v, i) => (i === idx ? '' : v)) : prev.filter((_, i) => i !== idx)
    );
  };

  const handleAddCompetitor = () => {
    setSkuSlots((prev) => (prev.length >= MAX_SLOTS ? prev : [...prev, '']));
  };

  const handleClearAll = () => {
    setSkuSlots(DEFAULT_SLOTS);
    setShowDiffOnly(false);
    setCollapsedCategories({});
  };

  const toggleCategory = (key) => setCollapsedCategories((prev) => ({ ...prev, [key]: !prev[key] }));
  const expandAll = () => setCollapsedCategories({});
  const collapseAll = () => {
    const all = {};
    ATTRIBUTE_CATEGORIES.forEach((c) => { all[c.key] = true; });
    setCollapsedCategories(all);
  };

  const rows = useMemo(() => {
    return ATTRIBUTES.map((attr) => {
      const values = activeColumns.map((c) => c.product.values[attr.key] ?? '—');
      const isDiff = values.length > 1 && values.some((v) => v !== values[0]);
      return { ...attr, values, isDiff };
    });
  }, [activeColumns]);

  const visibleRows = showDiffOnly ? rows.filter((r) => r.isDiff) : rows;

  const rowsByCategory = ATTRIBUTE_CATEGORIES
    .map((cat) => ({ ...cat, rows: visibleRows.filter((r) => r.category === cat.key) }))
    .filter((cat) => cat.rows.length > 0);

  const avgLeadTime = hasProducts
    ? (activeColumns.reduce((sum, c) => sum + c.product.leadTimeDays, 0) / activeColumns.length).toFixed(1)
    : null;

  const bestValue = hasProducts
    ? activeColumns.reduce((best, c) => (c.product.valueScore > best.product.valueScore ? c : best))
    : null;

  const topScored = bestValue;

  return (
    <DashboardLayout showTabs={false}>
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-5">
        <div>
          <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">
            Simulation Events
          </p>
          <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">High-Density Comparison</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">
            {hasProducts
              ? `Comparing ${activeColumns.length} item${activeColumns.length === 1 ? '' : 's'} across ${ATTRIBUTES.length} technical data points`
              : 'Paste SKUs below to start comparing products'}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            disabled={!hasProducts}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-semibold text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <i className="fa-solid fa-arrow-up-from-bracket text-[11px]" /> Export Specs
          </button>
          <button
            disabled={!hasProducts}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-semibold text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <i className="fa-solid fa-share-nodes text-[11px]" /> Share
          </button>
        </div>
      </div>

      {/* SKU input row */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 mb-4">
        <div className="flex flex-wrap items-stretch gap-2">
          {skuSlots.map((raw, idx) => {
            const result = slotResults[idx];
            return (
              <div key={idx} className="flex-1 min-w-[180px]">
                <div
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border transition-colors ${
                    result.status === 'not-found'
                      ? 'border-red-300 dark:border-red-800 bg-red-50/40 dark:bg-red-900/10'
                      : result.status === 'found'
                      ? 'border-gray-300 dark:border-slate-600 bg-gray-50 dark:bg-slate-800/60'
                      : 'border-dashed border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900'
                  }`}
                >
                  <span className="text-[11px] font-bold text-gray-400 dark:text-slate-500 flex-shrink-0">#{idx + 1}</span>
                  <input
                    type="text"
                    value={raw}
                    onChange={(e) => handleSkuChange(idx, e.target.value)}
                    placeholder="Paste SKU..."
                    className="flex-1 min-w-0 bg-transparent text-xs font-semibold text-gray-800 dark:text-slate-200 placeholder-gray-300 dark:placeholder-slate-600 focus:outline-none"
                  />
                  {raw && (
                    <button
                      onClick={() => handleRemoveSlot(idx)}
                      className="flex-shrink-0 text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 transition"
                    >
                      <i className="fa-solid fa-xmark text-[11px]" />
                    </button>
                  )}
                </div>
                {result.status === 'not-found' && (
                  <p className="text-[10px] text-red-500 dark:text-red-400 mt-1 ml-1">SKU not found</p>
                )}
              </div>
            );
          })}
          <button
            onClick={handleAddCompetitor}
            disabled={skuSlots.length >= MAX_SLOTS}
            className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          >
            <i className="fa-solid fa-plus text-[10px]" /> Add Competitor
          </button>
        </div>
      </div>

      {!hasProducts ? (
        /* Empty state */
        <div className="bg-white dark:bg-slate-900 border border-dashed border-gray-300 dark:border-slate-700 rounded-2xl py-10 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-3">
            <i className="fa-solid fa-table-cells text-gray-400 dark:text-slate-500" />
          </div>
          <p className="text-sm font-semibold text-gray-700 dark:text-slate-200">No products to compare yet</p>
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-1 max-w-xs">
            Paste a SKU into any of the fields above to pull in its technical data points.
          </p>
        </div>
      ) : (
        <>
          {/* Toolbar row */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <ToggleSwitch isOn={showDiffOnly} onToggle={() => setShowDiffOnly((v) => !v)} />
                <span className="text-xs font-medium text-gray-600 dark:text-slate-300">Diff Only</span>
              </label>
              <span className="text-xs text-gray-400 dark:text-slate-500">
                Showing {visibleRows.length} attribute{visibleRows.length === 1 ? '' : 's'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={collapseAll} className="text-xs font-semibold text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition">
                Collapse All
              </button>
              <span className="text-gray-300 dark:text-slate-700">|</span>
              <button onClick={expandAll} className="text-xs font-semibold text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition">
                Expand All
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden mb-4">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 dark:border-slate-800">
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider w-48">
                      Attribute
                    </th>
                    {activeColumns.map((col, idx) => (
                      <th key={idx} className="px-4 py-3 text-center min-w-[160px]">
                        <div className="flex flex-col items-center gap-1.5">
                          <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-slate-800 flex items-center justify-center">
                            <i className={`fa-solid ${col.product.icon} text-gray-500 dark:text-slate-400 text-sm`} />
                          </div>
                          <span className="text-xs font-bold text-gray-900 dark:text-slate-100">{col.product.name}</span>
                          <span className="text-[10px] text-gray-400 dark:text-slate-500 font-sans">{col.raw.trim().toUpperCase()}</span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rowsByCategory.map((cat) => {
                    const isCollapsed = !!collapsedCategories[cat.key];
                    return (
                      <React.Fragment key={cat.key}>
                        <tr className="bg-gray-50 dark:bg-slate-800/60 border-b border-gray-100 dark:border-slate-800">
                          <td colSpan={activeColumns.length + 1} className="px-4 py-2">
                            <button
                              onClick={() => toggleCategory(cat.key)}
                              className="flex items-center gap-2 text-[11px] font-bold text-gray-600 dark:text-slate-300 uppercase tracking-wider"
                            >
                              <i className={`fa-solid fa-chevron-down text-[9px] transition-transform ${isCollapsed ? '-rotate-90' : ''}`} />
                              {cat.label}
                            </button>
                          </td>
                        </tr>
                        {!isCollapsed &&
                          cat.rows.map((row) => (
                            <tr key={row.key} className="border-b border-gray-50 dark:border-slate-800/50">
                              <td className="px-4 py-2.5 text-xs font-medium text-gray-600 dark:text-slate-300">{row.label}</td>
                              {row.values.map((val, i) => (
                                <td key={i} className="px-4 py-2.5 text-center">
                                  {row.type === 'badge' ? (
                                    <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${inventoryBadgeClass(val)}`}>
                                      {val}
                                    </span>
                                  ) : (
                                    <span
                                      className={`text-xs ${
                                        i === 0 && row.isDiff
                                          ? 'font-bold text-blue-600 dark:text-blue-400'
                                          : 'font-medium text-gray-700 dark:text-slate-300'
                                      }`}
                                    >
                                      {val}
                                    </span>
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer summary */}
          <div className="flex flex-wrap items-center justify-between gap-4 px-1">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 uppercase tracking-wider font-semibold">Average Lead Time</p>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mt-0.5">{avgLeadTime} Days</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 uppercase tracking-wider font-semibold">Competitive Score</p>
                <p className="text-sm font-bold text-green-600 dark:text-green-400 mt-0.5">
                  {topScored?.product.competitiveGrade} {topScored?.product.competitiveLabel}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 dark:text-slate-500 uppercase tracking-wider font-semibold">Best Value Index</p>
                <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mt-0.5">{bestValue?.product.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleClearAll}
                className="px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition"
              >
                Clear All
              </button>
              <button
                disabled={activeColumns.length < 2}
                className="px-4 py-2 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Generate Report
              </button>
            </div>
          </div>
        </>
      )}
    </DashboardLayout>
  );
};

export default ComparisonPage;
