import React, { useState, useRef } from 'react';
import useClickOutside from '@/hooks/useClickOutside';
import DashboardLayout from '@/layouts/DashboardLayout';
import { REALIFY_BRIEF } from '@/data/briefData';
import { PROFIT_ADS_SUMMARY, SKU_LEDGER_DATA } from '@/features/profit-ads/data/profitAdsData';
import ProfitAdsModal from '@/features/profit-ads/components/ProfitAdsModal';
import ExplanationPanel from '@/features/profit-ads/components/ExplanationPanel';
import { downloadProfitAdsReport } from '@/services/exportService';
import { useExplainStore } from '@/store/useExplainStore';

export const ProfitAdsContent = () => {
  const briefData = REALIFY_BRIEF;
  const summary = PROFIT_ADS_SUMMARY;
  const { explainMode, setExplainMode: _setExplainMode } = useExplainStore();
  const [selectedCategory, setSelectedCategory] = useState('FIX ADS');
  const [activePanel, setActivePanel] = useState(null);
  const [selectedSku, setSelectedSku] = useState(null);
  const [activeDropdown, setActiveDropdown] = useState(null); // 'categories' | 'prices' | null
  const [isExporting, setIsExporting] = useState(false);

  // The wrapper's onClick only caught clicks inside the page body; this closes
  // the dropdowns for clicks anywhere in the app (sidebar, header, elsewhere).
  const filtersRef = useRef(null);
  useClickOutside(filtersRef, Boolean(activeDropdown), () => setActiveDropdown(null));

  // If the category is not "FIX ADS", we show empty data (like ss2)
  const currentSkus = selectedCategory === 'FIX ADS' ? SKU_LEDGER_DATA : [];

  const handleSkuClick = (sku) => {
    setSelectedSku(sku);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await downloadProfitAdsReport({ category: selectedCategory });
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <>
      <div className="flex flex-col h-full relative" onClick={() => setActiveDropdown(null)}>
        <div className="flex-1 overflow-y-auto px-1 sm:px-3 pt-0 pb-6">

          {/* Filters Row */}
          <div className="flex items-center justify-end gap-2 mt-4 mb-6" ref={filtersRef}>
            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setActiveDropdown(activeDropdown === 'categories' ? null : 'categories'); }}
                className={`px-3 py-1.5 border rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${activeDropdown === 'categories' ? 'border-blue-500 bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100' : 'border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-700 dark:text-slate-300'}`}
              >
                All categories <i className="fa-solid fa-caret-down text-[10px] text-gray-400"></i>
              </button>
              {activeDropdown === 'categories' && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-slate-700 rounded-lg shadow-lg border border-slate-600 overflow-hidden z-50 py-1">
                  <div className="px-3 py-2 bg-blue-600 text-white text-xs font-bold flex items-center gap-2 cursor-pointer">
                    <i className="fa-solid fa-check text-[10px]"></i> All categories
                  </div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Bike Accessories</div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Car Accessories</div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Car Electronics</div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Other Accessories</div>
                </div>
              )}
            </div>

            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setActiveDropdown(activeDropdown === 'prices' ? null : 'prices'); }}
                className={`px-3 py-1.5 border rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${activeDropdown === 'prices' ? 'border-blue-500 bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100' : 'border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-700 dark:text-slate-300'}`}
              >
                All price bands <i className="fa-solid fa-caret-down text-[10px] text-gray-400"></i>
              </button>
              {activeDropdown === 'prices' && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-slate-700 rounded-lg shadow-lg border border-slate-600 overflow-hidden z-50 py-1">
                  <div className="px-3 py-2 bg-blue-600 text-white text-xs font-bold flex items-center gap-2 cursor-pointer">
                    <i className="fa-solid fa-check text-[10px]"></i> All price bands
                  </div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Value ({"<"} $1,000)</div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Mid ($1,000-2,500)</div>
                  <div className="px-3 py-2 text-slate-200 hover:bg-slate-600 text-xs font-medium cursor-pointer pl-8">Premium ({">"} $2,500)</div>
                </div>
              )}
            </div>

            <button className="px-3 py-1.5 border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-md text-xs font-semibold text-gray-500 dark:text-slate-400 font-sans">
              2026-03-01 to 2026-06-30
            </button>
          </div>

          {/* Top Cards Block */}
          <div className="border border-gray-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 overflow-hidden shadow-sm mb-6 transition-all">
            <div className="p-6 pb-5 border-b border-gray-100 dark:border-slate-800 flex flex-col md:flex-row md:items-start justify-between gap-6">
              <div className="max-w-md">
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">RECOVERABLE NOW</p>
                <div className="flex items-center gap-3 mb-2">
                  <p className="text-[40px] font-extrabold text-[#be4141] dark:text-[#ff5252] leading-none tracking-tight">{summary.recoverableNow.value}</p>
                  {explainMode && (
                    <button
                      onClick={() => setActivePanel(activePanel === 'main' ? null : 'main')}
                      className={`w-5 h-5 rounded-full border border-[#627a8e] text-[#627a8e] dark:border-blue-400 dark:text-blue-400 flex items-center justify-center transition-colors ${activePanel === 'main' ? 'bg-[#627a8e] text-white' : 'hover:bg-[#627a8e]/10'}`}
                      title="Show explanation"
                    >
                      <i className="fa-solid fa-info text-[10px]" />
                    </button>
                  )}
                </div>
                {/* Custom styling for the subtitle based on SS1/SS2 */}
                <div className="text-[13px] text-gray-500 dark:text-slate-400 whitespace-pre-line leading-relaxed">
                  <span className="font-bold text-gray-600 dark:text-slate-300">recoverable now — overspending above break-even</span>
                  <br />
                  across 41 FIX ADS SKUs · <span className="font-semibold text-gray-600 dark:text-slate-300">$310,259</span> certain, $735 rests on estimated inputs
                  <br /><br />
                  Start with the <span className="font-semibold text-gray-800 dark:text-slate-200">top 4</span> of 41 — they hold <span className="font-semibold text-gray-800 dark:text-slate-200">74%</span> of the recoverable.
                </div>
              </div>
              <div className="flex flex-col items-end gap-2 text-right">
                {summary.recoverableNow.stats.map((stat, idx) => (
                  <p key={idx} className="text-[14px] text-gray-500 dark:text-slate-400 flex items-center gap-1.5 justify-end">
                    {stat.parts.map((part, pIdx) => (
                      <React.Fragment key={pIdx}>
                        <span className={part.bold ? 'font-bold text-gray-900 dark:text-slate-100' : ''}>
                          {part.text}
                        </span>
                        {part.iconId && explainMode && (
                          <button
                            onClick={() => setActivePanel(activePanel === part.iconId ? null : part.iconId)}
                            className={`ml-1 w-5 h-5 rounded-full border border-[#627a8e] text-[#627a8e] dark:border-blue-400 dark:text-blue-400 flex items-center justify-center transition-colors ${activePanel === part.iconId ? 'bg-[#627a8e] text-white' : 'hover:bg-[#627a8e]/10'}`}
                            title="Show explanation"
                          >
                            <i className="fa-solid fa-info text-[10px]" />
                          </button>
                        )}
                      </React.Fragment>
                    ))}
                  </p>
                ))}
              </div>
            </div>

            {activePanel && (
              <div className="px-6 pb-6 bg-[#fcfbf9] dark:bg-slate-900/50">
                <ExplanationPanel data={
                  activePanel === 'main' ? {
                    provenanceBadge: 'L1',
                    title: 'DETERMINISTIC — HOW THIS NUMBER IS DERIVED',
                    formula: 'Σ of 41 SKUs · per-SKU: max(ad spend - ad sales × break-even ACoS, 0)',
                    contributors: [
                      { sku: 'VKAMCOVER0074', value: '$80,212' },
                      { sku: 'VKAMCOVER0072', value: '$76,798' },
                      { sku: 'AFWPUMP0006', value: '$38,220' },
                    ],
                    result: '$310,995',
                    timeframe: '2026-04-01 → 2026-06-01 · 3 periods',
                    provenanceText: 'sum of per-SKU L1 figures'
                  } : activePanel === 'ad_spend' ? {
                    provenanceBadge: 'L1',
                    title: 'DETERMINISTIC — HOW THIS NUMBER IS DERIVED',
                    formula: 'Σ of 49 SKUs · per-SKU: max(ad spend - ad sales × break-even ACoS, 0)',
                    contributors: [
                      { sku: 'VKAMCOVER0074', value: '$80,212' },
                      { sku: 'VKAMCOVER0072', value: '$76,798' },
                      { sku: 'AFWPUMP0006', value: '$38,220' },
                    ],
                    result: '$345,770',
                    timeframe: '2026-04-01 → 2026-06-01 · 3 periods',
                    provenanceText: 'derived from per-SKU figures'
                  } : activePanel === 'bleed' ? {
                    provenanceBadge: 'L1',
                    title: 'DETERMINISTIC — HOW THIS NUMBER IS DERIVED',
                    formula: 'Σ of 8 SKUs · per-SKU: ad spend on CUT/DIVEST SKUs (losing on margin and ads)',
                    contributors: [
                      { sku: 'CACOVER1435', value: '$23,293' },
                      { sku: 'BAHOLDER0023', value: '$1,949' },
                      { sku: 'AGBRUSH0001', value: '$1,060' },
                    ],
                    result: '$27,055',
                    timeframe: '2026-04-01 → 2026-06-01 · 3 periods',
                    provenanceText: 'derived from per-SKU figures'
                  } : activePanel === 'scale' ? {
                    provenanceBadge: 'L1',
                    title: 'DETERMINISTIC — HOW THIS NUMBER IS DERIVED',
                    formula: 'Σ of 47 SKUs · per-SKU: ad spend increase potential before break-even',
                    contributors: [
                      { sku: 'SCALE0074', value: '$450,000' },
                      { sku: 'SCALE0072', value: '$320,000' },
                      { sku: 'SCALE0006', value: '$180,000' },
                    ],
                    result: '$1,600,190',
                    timeframe: '2026-04-01 → 2026-06-01 · 3 periods',
                    provenanceText: 'derived from per-SKU figures'
                  } : null
                } />
              </div>
            )}

            <div className="flex items-stretch h-24 divide-x divide-gray-100 dark:divide-slate-800">
              {summary.categories.map((cat, idx) => (
                <div
                  key={idx}
                  className={`flex-1 flex flex-col justify-center px-6 cursor-pointer relative ${cat.label === selectedCategory ? 'bg-red-50/40 dark:bg-red-900/10' : 'hover:bg-gray-50 dark:hover:bg-slate-800/30'}`}
                  onClick={() => setSelectedCategory(cat.label)}
                >
                  {cat.label === selectedCategory && (
                    <div className="absolute top-0 left-0 w-full h-0.5 bg-red-500"></div>
                  )}
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-0.5">{cat.value}</p>
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">{cat.label}</p>
                  <p className="text-xs font-medium text-gray-500 dark:text-slate-400">{cat.subtext}</p>
                </div>
              ))}
            </div>
          </div>

          {/* SKU Ledger Header */}
          <div className="flex items-end justify-between mb-2">
            <h3 className="text-sm font-bold text-gray-500 dark:text-slate-400 tracking-widest uppercase">
              SKU LEDGER · {selectedCategory === 'FIX ADS' ? 'FOR ADS (15)' : 'CUTNEEDED'}
            </h3>
          </div>

          <p className="text-xs font-medium text-gray-400 dark:text-slate-500 mb-6">
            ACOS, break-even and recoverable value, one row per SKU, one source of truth.
            Click a row to open the Signal.
          </p>

          {/* Table */}
          <div className="border border-gray-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 shadow-sm overflow-hidden mb-6">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-100 dark:border-slate-800">
                  <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest w-[40%]">SKU</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest w-[25%]">ACOS VS BREAK-EVEN</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">CMAA</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest text-right">RECOVERABLE</th>
                  <th className="w-8"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-800/50">
                {currentSkus.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-12 text-center text-sm font-semibold text-gray-400 dark:text-slate-500">
                      No SKUs in this bucket right now.
                    </td>
                  </tr>
                ) : (
                  currentSkus.map(sku => {
                    const isHigh = sku.acos > sku.be;
                    const acosColor = isHigh ? 'text-red-600 dark:text-red-500' : 'text-emerald-600 dark:text-emerald-500';
                    const barColor = isHigh ? 'bg-red-500' : 'bg-emerald-500';
                    const maxVal = Math.max(sku.acos, sku.be, 50);
                    const acosWidth = `${(sku.acos / maxVal) * 100}%`;
                    const beWidth = `${(sku.be / maxVal) * 100}%`;

                    return (
                      <tr
                        key={sku.id}
                        onClick={() => handleSkuClick(sku)}
                        className="hover:bg-gray-50/80 dark:hover:bg-slate-800/30 cursor-pointer transition-colors group"
                      >
                        <td className="px-6 py-5">
                          <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-1 tracking-tight truncate pr-4" title={sku.title}>{sku.title}</p>
                          <p className="text-[10px] font-sans text-gray-400 dark:text-slate-500 tracking-wider">
                            {sku.sku} · {sku.campaignCount} campaign{sku.campaignCount !== 1 ? 's' : ''} · {sku.category}
                          </p>
                        </td>
                        <td className="px-6 py-5">
                          <div className="w-full max-w-[140px] mb-1 relative h-1.5 bg-gray-100 dark:bg-slate-800 rounded-full overflow-visible flex items-center">
                            {/* BE marker line */}
                            <div className="absolute top-1/2 -translate-y-1/2 h-3 w-0.5 bg-gray-300 dark:bg-slate-500 z-10" style={{ left: beWidth }}></div>
                            {/* ACOS bar */}
                            <div className={`h-full rounded-full ${barColor}`} style={{ width: acosWidth }}></div>
                          </div>
                          <p className="text-[11px] font-bold mt-1.5">
                            <span className={acosColor}>{sku.acos}% ACOS</span>
                            <span className="text-gray-400 dark:text-slate-500 font-medium"> vs {sku.be}% BE</span>
                          </p>
                        </td>
                        <td className="px-6 py-5">
                          <span className="text-[13px] font-bold text-gray-900 dark:text-slate-100">{sku.cmaa}</span>
                        </td>
                        <td className="px-6 py-5 text-right">
                          <span className="text-[13px] font-bold text-gray-900 dark:text-slate-100">{sku.recoverable}</span>
                        </td>
                        <td className="px-4 py-5 text-gray-300 dark:text-slate-600 group-hover:text-blue-500 transition-colors">
                          <i className="fa-solid fa-chevron-right text-[10px]"></i>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

        </div>

        {/* Sticky Footer */}
        <div className="absolute bottom-0 left-0 w-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 px-8 flex items-center justify-between shadow-[0_-4px_12px_rgba(0,0,0,0.02)] z-10">
          <p className="text-[13px] font-medium text-gray-600 dark:text-slate-400">
            {selectedCategory === 'FIX ADS' ? (
              <>Pull ACoS to break-even on all 11 For Ads SKUs in view. Projected <span className="font-bold text-emerald-600 dark:text-emerald-500">{summary.footerProjected}</span></>
            ) : (
              <>Pull ACoS to break-even on all 0 For Ads SKUs in view. Projected <span className="font-bold text-emerald-600 dark:text-emerald-500">$203,012</span></>
            )}
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="px-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-70 flex items-center gap-2"
            >
              {isExporting && <i className="fa-solid fa-spinner fa-spin"></i>}
              Export change set
            </button>
            <button className="px-5 py-2 bg-gray-900 hover:bg-gray-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-gray-900 rounded-lg text-[13px] font-bold transition-colors shadow-sm">
              Apply to all {selectedCategory === 'FIX ADS' ? '11' : '0'}
            </button>
          </div>
        </div>
      </div>

      <ProfitAdsModal
        isOpen={!!selectedSku}
        onClose={() => setSelectedSku(null)}
        skuData={selectedSku}
      />
    </>
  );
};

const ProfitAdsPage = () => (
  <DashboardLayout title="Profit & Ads" subtitle="" showTabs={false} showAIPrompt={false}>
    <ProfitAdsContent />
  </DashboardLayout>
);

export default ProfitAdsPage;
