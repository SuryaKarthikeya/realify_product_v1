import React, { useState, useRef } from 'react';
import { useWorkspaceFilterStore } from '@/store/useWorkspaceFilterStore';
import useClickOutside from '@/hooks/useClickOutside';
import { PRODUCT_CATEGORIES } from '@/constants/filterOptions';

/**
 * FilterBar — Single Row + Inline Expandable Second Row (Master Prompt v5)
 * 
 * Rules:
 * [14D 30D 60D 90D]   [Channel ▾]   [Category ▾]   [More filters ⌄]
 * 
 * Clicking More filters expands INLINE directly beneath the filter bar
 * (Priority Tier, Price Band, Brand, Performance Tier), pushing signal list down naturally.
 * ZERO popups/modals. 100% continuous flat surface.
 */
/*
 * The workspace filters are multi-select arrays; these native <select>s are
 * single-choice, so they read the first selection and write a one-item array.
 */
const FilterBar = ({ isCollapsed }) => {
  const [isInlineExpanded, setIsInlineExpanded] = useState(false);
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);

  // Clicking anywhere outside the date popover closes it.
  const datePickerRef = useRef(null);
  useClickOutside(datePickerRef, isDatePickerOpen, () => setIsDatePickerOpen(false));

  const {
    timeRange,
    marketplace,
    categoryCut,
    statusFilter,
    brand,
    priceBand,
    priority,
    performanceTier,
    subCategory,
    setTimeRange,
    setMarketplace,
    setCategoryCut,
    setStatusFilter,
    setBrand,
    setPriceBand,
    setPriority,
    setPerformanceTier,
    setSubCategory,
    resetAdvancedFilters,
  } = useWorkspaceFilterStore();

  const [tempTimeRange, setTempTimeRange] = useState(timeRange || '30D');
  const [tempStart, setTempStart] = useState('4 May 2026');
  const [tempEnd, setTempEnd] = useState('2 Jun 2026');

  const activeChips = [];
  if (brand !== 'all') activeChips.push({ label: `Brand: ${brand}`, key: 'brand', clear: () => setBrand('all') });
  if (priceBand !== 'all') activeChips.push({ label: `Price: ${priceBand}`, key: 'priceBand', clear: () => setPriceBand('all') });
  if (priority !== 'all') activeChips.push({ label: `Priority: ${priority}`, key: 'priority', clear: () => setPriority('all') });
  if (performanceTier !== 'all') activeChips.push({ label: `Tier: ${performanceTier}`, key: 'performanceTier', clear: () => setPerformanceTier('all') });
  if (subCategory !== 'all') activeChips.push({ label: `Subcat: ${subCategory}`, key: 'subCategory', clear: () => setSubCategory('all') });

  const dateRangeLabel = timeRange === '7D' ? 'Last 7 Days' : timeRange === '14D' ? 'Last 14 Days' : timeRange === '60D' ? 'Last 60 Days' : timeRange === '90D' ? 'Last 90 Days' : 'Last 30 Days';

  return (
    <div className="space-y-2">
      {/* ── 1. Single Horizontal Flex Row ── */}
      <div className={`flex items-center overflow-x-auto scrollbar-hide py-0.5 ${isCollapsed ? 'justify-between w-full gap-2' : 'gap-2'}`}>
        <div className="flex items-center gap-2 flex-shrink-0 text-xs">

          {/* 1st: Category Selector */}
          <select
            value={categoryCut[0] || 'all'}
            onChange={(e) => setCategoryCut(e.target.value === 'all' ? [] : [e.target.value])}
            className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-[11.5px] font-medium text-gray-800 dark:text-slate-200 focus:outline-none flex-shrink-0 cursor-pointer shadow-2xs hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            <option value="all">Category</option>
            {PRODUCT_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>

          {/* 2nd: Channels Selector */}
          <select
            value={marketplace[0] || 'all'}
            onChange={(e) => setMarketplace(e.target.value === 'all' ? [] : [e.target.value])}
            className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-[11.5px] font-medium text-gray-800 dark:text-slate-200 focus:outline-none flex-shrink-0 cursor-pointer shadow-2xs hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            <option value="all">Channel</option>
            <option value="amazon">Amazon</option>
            <option value="walmart">Walmart</option>
            <option value="shopify">Shopify</option>
          </select>

          {/* 3rd: Status Selector */}
          <select
            value={statusFilter[0] || 'all'}
            onChange={(e) => setStatusFilter(e.target.value === 'all' ? [] : [e.target.value])}
            className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-[11.5px] font-medium text-gray-800 dark:text-slate-200 focus:outline-none flex-shrink-0 cursor-pointer shadow-2xs hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            <option value="all">Status</option>
            <option value="executed">Executed</option>
            <option value="not_executed">Not Executed</option>
          </select>
        </div>

        {/* 4th: Date Range Popover Filter */}
        <div className="relative flex-shrink-0" ref={datePickerRef}>
          <button
            onClick={() => setIsDatePickerOpen(!isDatePickerOpen)}
            className={`px-2.5 py-1 bg-white dark:bg-slate-800 border rounded-lg text-[11.5px] font-medium transition-colors flex items-center gap-1.5 ${isDatePickerOpen || timeRange !== '30D'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50/40'
                : 'border-gray-200 dark:border-slate-700 text-gray-800 dark:text-slate-200'
              }`}
          >
            <i className="fa-regular fa-calendar text-[11px]" />
            <span>{dateRangeLabel}</span>
            <i className="fa-solid fa-chevron-down text-[9px]" />
          </button>

          {/* Date Range Popover matching exact screenshot */}
          {isDatePickerOpen && (
            <div className={`absolute top-full mt-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-2xl z-[9999] p-4 sm:p-5 w-[330px] sm:w-[540px] space-y-4 animate-fade-in text-xs font-sans ${isCollapsed ? 'right-0' : 'left-0'}`}>
                {/* Header */}
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-900 dark:text-white">Date Range</span>
                  <button onClick={() => setIsDatePickerOpen(false)} className="text-gray-400 hover:text-gray-600">
                    <i className="fa-solid fa-xmark text-sm" />
                  </button>
                </div>

                {/* 1. Quick Filters */}
                <div className="space-y-2">
                  <span className="text-[11px] font-semibold text-gray-500 dark:text-slate-400 block">Quick Filters</span>
                  <div className="flex items-center gap-2">
                    {[
                      { label: 'Last 7 Days', val: '7D' },
                      { label: 'Last 30 Days', val: '30D' },
                      { label: 'Last 60 Days', val: '60D' },
                    ].map((qf) => (
                      <button
                        key={qf.val}
                        onClick={() => { setTempTimeRange(qf.val); setTempStart('4 May 2026'); setTempEnd('2 Jun 2026'); }}
                        className={`px-3.5 py-1.5 rounded-xl border text-[11.5px] font-medium transition-all ${tempTimeRange === qf.val
                            ? 'border-gray-900 dark:border-white bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold'
                            : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:border-gray-300'
                          }`}
                      >
                        {qf.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 2. Custom Section */}
                <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-gray-500 dark:text-slate-400 block">Custom</span>

                  {/* Start Date & End Date Inputs */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="px-3 py-2 border border-gray-200 dark:border-slate-700 rounded-xl bg-gray-50/50 dark:bg-slate-800/40">
                      <span className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 block uppercase">Start Date</span>
                      <div className="flex items-center justify-between mt-0.5">
                        <span className="text-xs font-semibold text-gray-900 dark:text-white">{tempStart}</span>
                        <i className="fa-regular fa-calendar text-xs text-gray-400" />
                      </div>
                    </div>
                    <div className="px-3 py-2 border border-gray-200 dark:border-slate-700 rounded-xl bg-gray-50/50 dark:bg-slate-800/40">
                      <span className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 block uppercase">End Date</span>
                      <div className="flex items-center justify-between mt-0.5">
                        <span className="text-xs font-semibold text-gray-900 dark:text-white">{tempEnd}</span>
                        <i className="fa-regular fa-calendar text-xs text-gray-400" />
                      </div>
                    </div>
                  </div>

                  {/* Dual Calendar View */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    {/* Month 1: May 2026 */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between px-1">
                        <button className="text-gray-400 hover:text-gray-700 text-xs"><i className="fa-solid fa-chevron-left" /></button>
                        <span className="text-xs font-bold text-gray-900 dark:text-white">May 2026</span>
                        <span className="w-3" />
                      </div>
                      <div className="grid grid-cols-7 text-center gap-1 text-[10px] text-gray-400 font-semibold">
                        <span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
                      </div>
                      <div className="grid grid-cols-7 text-center gap-1 text-xs">
                        <span /><span /><span /><span /><span /><span>1</span><span>2</span>
                        <span>3</span>
                        <span className="bg-black text-white font-bold rounded-lg py-1">4</span>
                        <span>5</span><span>6</span><span>7</span><span>8</span><span>9</span>
                        <span>10</span><span>11</span><span>12</span><span>13</span><span>14</span><span>15</span><span>16</span>
                        <span>17</span><span>18</span><span>19</span><span>20</span><span>21</span><span>22</span><span>23</span>
                        <span>24</span><span>25</span><span>26</span><span>27</span><span>28</span><span>29</span><span>30</span>
                        <span>31</span>
                      </div>
                    </div>

                    {/* Month 2: Jun 2026 */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between px-1">
                        <span className="w-3" />
                        <span className="text-xs font-bold text-gray-900 dark:text-white">Jun 2026</span>
                        <button className="text-gray-400 hover:text-gray-700 text-xs"><i className="fa-solid fa-chevron-right" /></button>
                      </div>
                      <div className="grid grid-cols-7 text-center gap-1 text-[10px] text-gray-400 font-semibold">
                        <span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
                      </div>
                      <div className="grid grid-cols-7 text-center gap-1 text-xs">
                        <span />
                        <span className="bg-black text-white font-bold rounded-lg py-1">2</span>
                        <span>3</span><span>4</span><span>5</span><span>6</span>
                        <span>7</span><span>8</span><span>9</span><span>10</span><span>11</span><span>12</span><span>13</span>
                        <span>14</span><span>15</span><span>16</span><span>17</span><span>18</span><span>19</span><span>20</span>
                        <span>21</span><span>22</span><span>23</span><span>24</span><span>25</span><span>26</span><span>27</span>
                        <span>28</span><span>29</span><span>30</span>
                      </div>
                    </div>
                  </div>

                </div>

                {/* Footer Buttons */}
                <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100 dark:border-slate-800">
                  <button
                    onClick={() => setIsDatePickerOpen(false)}
                    className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      setTimeRange(tempTimeRange);
                      setIsDatePickerOpen(false);
                    }}
                    className="px-5 py-2 rounded-xl bg-black dark:bg-white text-white dark:text-black text-xs font-bold hover:bg-gray-800 transition-colors"
                  >
                    Apply
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>

      {/* ── Active Removable Chips Row ── */}
      {activeChips.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[10px] font-mono text-gray-400 dark:text-slate-500 uppercase font-semibold">Active:</span>
          {activeChips.map((chip) => (
            <span
              key={chip.key}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 rounded-full text-[10.5px] font-mono font-semibold"
            >
              <span>{chip.label}</span>
              <button
                onClick={chip.clear}
                className="hover:text-red-600 font-bold ml-0.5 text-[11px]"
                title="Remove filter"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default React.memo(FilterBar);
