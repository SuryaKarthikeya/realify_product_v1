import React, { useState } from 'react';
import MiniCalendar from '@/components/data-display/MiniCalendar';
import { V2_CAT_GRID } from '@/constants/filterOptions';
import { quickToRange, formatCalDate, v2CatLabel } from '@/utils/filterUtils';
import { PRODUCT_CATALOG } from '@/constants/productCatalog';
import { PRODUCT_CATEGORIES } from '@/constants/filterOptions';

// The Workspace (AI View) filter dropdown — vertical section nav (date/channel/
// category) plus the matching editor. Mirrors the Dashboard View filter bar's look,
// but keeps its own state/handlers since this page's "Clear Filters" footer button
// and always-reopen (non-toggle) filter button behave differently from Detailed View.
const WorkspaceFilterPanel = ({ filters, style }) => {
  const {
    v2Section, setV2Section,
    pendingDate, setPendingDate, pendingCats, pendingChans,
    pendingProducts, setPendingProducts, togglePendingProduct,
    pendingRangeStart, pendingRangeEnd, hoverDay, setHoverDay,
    setPendingRangeStart, setPendingRangeEnd, setPendingCats, setPendingChans,
    calViewYear, calViewMonth, calRightM, calRightY,
    prevCalMonth, nextCalMonth, handleDateClick,
    togglePendingCat, togglePendingChan,
    v2ChanGrid, v2ChanLabel,
    setAppliedDate, setAppliedCats, setAppliedChans, setAppliedProducts,
    setDateRange, setCategory, setChannel, setProducts,
    setV2FilterOpen, handleApplyV2Filter,
  } = filters;

  const [productSearch, setProductSearch] = useState('');
  const [channelSearch, setChannelSearch] = useState('');

  const onDateHover = (date) => { if (pendingRangeStart && !pendingRangeEnd) setHoverDay(date); };

  const filteredProducts = PRODUCT_CATALOG.filter(p =>
    p.name.toLowerCase().includes(productSearch.toLowerCase())
  );
  const productLabel = pendingProducts.length
    ? `${pendingProducts.length} Product${pendingProducts.length > 1 ? 's' : ''}`
    : 'All Products';
  const mobileChanList = v2ChanGrid
    .filter(([v]) => v !== 'all-chans')
    .filter(([, lbl]) => lbl.toLowerCase().includes(channelSearch.toLowerCase()));
  const activeFilterTypeCount = [pendingDate !== null, pendingCats.length > 0, pendingChans.length > 0, pendingProducts.length > 0].filter(Boolean).length;
  const CATEGORY_ICONS = {
    ...Object.fromEntries(PRODUCT_CATEGORIES.map((c) => [c.value, c.icon])),
    all: 'fa-table-cells',
  };

  return (
    <div
      className="fixed bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl shadow-xl z-[9999] sm:w-[580px] overflow-hidden flex flex-col"
      style={style}
    >
      {/* MOBILE-only header — title + active-filter count badge + close */}
      <div className="sm:hidden flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-900 dark:text-slate-100">Filters</span>
          {activeFilterTypeCount > 0 && (
            <span className="w-5 h-5 flex items-center justify-center bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-[10px] font-bold rounded-full">
              {activeFilterTypeCount}
            </span>
          )}
        </div>
        <button
          onClick={() => setV2FilterOpen(false)}
          className="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
        >
          <i className="fa-solid fa-xmark text-sm" />
        </button>
      </div>

      <div className="flex flex-col sm:flex-row flex-1 min-h-0 sm:flex-none sm:max-h-[300px] sm:min-h-[300px] overflow-y-auto sm:overflow-hidden">

        {/* LEFT: Vertical nav — becomes a horizontal scrollable pill row on mobile */}
        <div className="flex flex-row sm:flex-col gap-1 overflow-x-auto scrollbar-hide sm:overflow-visible border-b sm:border-b-0 sm:border-r border-gray-100 dark:border-slate-800 p-4 sm:w-[155px] sm:flex-shrink-0">
          {[
            { key: 'date', label: 'Select Date' },
            { key: 'channel', label: 'All Channels' },
            { key: 'category', label: 'All Categories' },
            { key: 'product', label: productLabel },
          ].map(sec => (
            <button
              key={sec.key}
              onClick={() => setV2Section(sec.key)}
              className={`flex items-center gap-2 flex-shrink-0 sm:w-full text-left px-2.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                v2Section === sec.key
                  ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
              }`}
            >
              <span className={`w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-all ${
                v2Section === sec.key ? 'border-white dark:border-gray-900' : 'border-gray-300 dark:border-slate-600'
              }`}>
                {v2Section === sec.key && <span className="w-1.5 h-1.5 rounded-full bg-white dark:bg-gray-900" />}
              </span>
              {sec.label}
            </button>
          ))}
        </div>

        {/* RIGHT: Section content */}
        <div className="flex-1 flex flex-col min-w-0 sm:overflow-hidden">

          {/* ── Date section ── */}
          {v2Section === 'date' && (
            <div className="flex-1 flex flex-col p-4 gap-2">
              {/* Quick filter pills */}
              <div className="flex items-center gap-2 flex-wrap pb-3 border-b border-gray-100 dark:border-slate-800">
                <span className="text-xs font-semibold text-gray-400 dark:text-slate-500">Quick Filters</span>
                {[['last-7-days','Last 7 Days'],['last-30-days','Last 30 Days'],['last-90-days','Last 90 Days']].map(([val, lbl]) => (
                  <button key={val}
                    onClick={() => { const r = quickToRange(val); setPendingRangeStart(r.start); setPendingRangeEnd(r.end); setPendingDate(val); }}
                    className={`px-3 py-1 rounded-full border text-xs font-medium transition-all ${
                      pendingDate === val
                        ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100'
                        : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:border-gray-300 dark:hover:border-slate-600'
                    }`}>
                    {lbl}
                  </button>
                ))}
              </div>

              {/* MOBILE: Custom Range — Start/End info boxes + both calendars visible at once */}
              <div className="sm:hidden flex flex-col gap-3">
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-1.5">Custom Range</p>
                  <div className="flex items-center justify-between px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-600 dark:text-slate-300">
                    Custom Range
                    <i className="fa-solid fa-chevron-down text-[10px] text-gray-400 dark:text-slate-500" />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0 px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700">
                    <p className="text-[9px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">Start Date</p>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-gray-800 dark:text-slate-200 truncate">
                        {pendingRangeStart ? formatCalDate(pendingRangeStart) : 'Select date'}
                      </span>
                      <i className="fa-regular fa-calendar text-[11px] text-gray-400 dark:text-slate-500 flex-shrink-0" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0 px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700">
                    <p className="text-[9px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">End Date</p>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-gray-800 dark:text-slate-200 truncate">
                        {pendingRangeEnd ? formatCalDate(pendingRangeEnd) : 'Select date'}
                      </span>
                      <i className="fa-regular fa-calendar text-[11px] text-gray-400 dark:text-slate-500 flex-shrink-0" />
                    </div>
                  </div>
                </div>
                <div className="flex flex-row gap-2">
                  <MiniCalendar
                    year={calViewYear} month={calViewMonth} showPrev showNext={false}
                    onPrev={prevCalMonth} onNext={nextCalMonth}
                    rangeStart={pendingRangeStart} rangeEnd={pendingRangeEnd} hoverDay={hoverDay}
                    onDateClick={handleDateClick} onDateHover={onDateHover} onDateLeave={() => setHoverDay(null)}
                  />
                  <div className="w-px bg-gray-100 dark:bg-slate-800 self-stretch flex-shrink-0" />
                  <MiniCalendar
                    year={calRightY} month={calRightM} showPrev={false} showNext
                    onPrev={prevCalMonth} onNext={nextCalMonth}
                    rangeStart={pendingRangeStart} rangeEnd={pendingRangeEnd} hoverDay={hoverDay}
                    onDateClick={handleDateClick} onDateHover={onDateHover} onDateLeave={() => setHoverDay(null)}
                  />
                </div>
              </div>

              {/* DESKTOP: dual side-by-side calendar, unchanged */}
              <div className="hidden sm:flex gap-3 flex-1">
                <MiniCalendar
                  year={calViewYear} month={calViewMonth} showPrev showNext={false}
                  onPrev={prevCalMonth} onNext={nextCalMonth}
                  rangeStart={pendingRangeStart} rangeEnd={pendingRangeEnd} hoverDay={hoverDay}
                  onDateClick={handleDateClick} onDateHover={onDateHover} onDateLeave={() => setHoverDay(null)}
                />
                <div className="w-px bg-gray-100 dark:bg-slate-800 self-stretch flex-shrink-0" />
                <MiniCalendar
                  year={calRightY} month={calRightM} showPrev={false} showNext
                  onPrev={prevCalMonth} onNext={nextCalMonth}
                  rangeStart={pendingRangeStart} rangeEnd={pendingRangeEnd} hoverDay={hoverDay}
                  onDateClick={handleDateClick} onDateHover={onDateHover} onDateLeave={() => setHoverDay(null)}
                />
              </div>

              {/* Bottom: date range display — desktop only, mobile shows it in the Start/End fields */}
              <div className="hidden sm:flex items-center gap-3 pt-2 border-t border-gray-100 dark:border-slate-800">
                {pendingRangeStart && (
                  <span className="text-[11px] text-gray-600 dark:text-slate-400">
                    {formatCalDate(pendingRangeStart)}{pendingRangeEnd ? ` — ${formatCalDate(pendingRangeEnd)}` : ''}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* ── Category section ── */}
          {v2Section === 'category' && (
            <>
              {/* MOBILE: icon-card grid */}
              <div className="sm:hidden flex-1 flex flex-col p-4 gap-4 min-h-0">
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3">All Categories</p>
                  <div className="grid grid-cols-2 gap-2.5">
                    {V2_CAT_GRID.map(([val, lbl]) => {
                      const isSel = val === 'all' ? pendingCats.length === 0 : pendingCats.includes(val);
                      return (
                        <button
                          key={val}
                          onClick={() => togglePendingCat(val)}
                          className={`relative flex items-center gap-2.5 px-3 py-3 rounded-xl border-2 text-left transition-all ${val === 'all' ? 'col-span-2' : ''} ${
                            isSel ? 'border-gray-900 bg-gray-50 dark:border-slate-100 dark:bg-slate-800' : 'border-gray-200 dark:border-slate-700'
                          }`}
                        >
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            isSel ? 'bg-gray-900 text-white dark:bg-slate-100 dark:text-gray-900' : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
                          }`}>
                            <i className={`fa-solid ${CATEGORY_ICONS[val] || 'fa-tag'} text-sm`} />
                          </div>
                          <span className="text-xs font-semibold text-gray-800 dark:text-slate-200">{lbl}</span>
                          {isSel && (
                            <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-gray-900 dark:bg-slate-100 rounded-full flex items-center justify-center border-2 border-white dark:border-slate-900">
                              <i className="fa-solid fa-check text-[7px] text-white dark:text-gray-900" />
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
                {pendingCats.length > 0 && (
                  <div className="pt-3 border-t border-gray-100 dark:border-slate-800 mt-auto">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-gray-700 dark:text-slate-300">Selected ({pendingCats.length})</span>
                      <button onClick={() => setPendingCats([])} className="text-[11px] font-semibold text-gray-500 dark:text-slate-400 hover:underline">Clear All</button>
                    </div>
                    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
                      {pendingCats.map(cat => (
                        <span key={cat} className="flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-medium text-gray-700 dark:text-slate-300 whitespace-nowrap">
                          {v2CatLabel(cat)}
                          <button onClick={() => togglePendingCat(cat)} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition">
                            <i className="fa-solid fa-xmark text-[9px]" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* DESKTOP: pill-wrap grid, unchanged */}
              <div className="hidden sm:flex flex-1 flex-col p-4 gap-5">
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-2">All Categories</p>
                  <div className="flex flex-wrap gap-1.5">
                    {V2_CAT_GRID.map(([val, lbl]) => {
                      const isSel = val === 'all' ? pendingCats.length === 0 : pendingCats.includes(val);
                      return (
                        <button key={val} onClick={() => togglePendingCat(val)}
                          className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                            isSel ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100' : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:border-gray-300 dark:hover:border-slate-600'
                          }`}>{lbl}</button>
                      );
                    })}
                  </div>
                </div>
                {pendingCats.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100 dark:border-slate-800 mt-auto">
                    {pendingCats.map(cat => (
                      <span key={cat} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-medium text-gray-700 dark:text-slate-300">
                        {v2CatLabel(cat)}
                        <button onClick={() => togglePendingCat(cat)} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition">
                          <i className="fa-solid fa-xmark text-[9px]" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── Channel section ── */}
          {v2Section === 'channel' && (
            <>
              {/* MOBILE: search + checkbox list */}
              <div className="sm:hidden flex-1 flex flex-col p-4 gap-3 min-h-0">
                <div className="relative flex-shrink-0">
                  <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-xs" />
                  <input
                    type="text"
                    value={channelSearch}
                    onChange={(e) => setChannelSearch(e.target.value)}
                    placeholder="Search channels..."
                    className="w-full pl-8 pr-3 py-2 text-xs bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg outline-none focus:border-gray-300 dark:focus:border-slate-600 text-gray-700 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 transition-colors"
                  />
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5">
                  {!channelSearch && (
                    <button
                      onClick={() => setPendingChans([])}
                      className="flex items-center gap-3 px-2 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800/40 text-left transition-colors"
                    >
                      <div className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border-2 transition-colors ${
                        pendingChans.length === 0 ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-100' : 'border-gray-300 dark:border-slate-600'
                      }`}>
                        {pendingChans.length === 0 && <i className="fa-solid fa-check text-[8px] text-white dark:text-gray-900" />}
                      </div>
                      <span className="text-sm text-gray-700 dark:text-slate-300">All Channels</span>
                    </button>
                  )}
                  {mobileChanList.map(([val, lbl]) => {
                    const checked = pendingChans.includes(val);
                    return (
                      <button
                        key={val}
                        onClick={() => togglePendingChan(val)}
                        className="flex items-center gap-3 px-2 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800/40 text-left transition-colors"
                      >
                        <div className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border-2 transition-colors ${
                          checked ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-100' : 'border-gray-300 dark:border-slate-600'
                        }`}>
                          {checked && <i className="fa-solid fa-check text-[8px] text-white dark:text-gray-900" />}
                        </div>
                        <span className="text-sm text-gray-700 dark:text-slate-300">{lbl}</span>
                      </button>
                    );
                  })}
                  {mobileChanList.length === 0 && (
                    <p className="text-xs text-gray-400 dark:text-slate-500 text-center py-6">No channels found</p>
                  )}
                </div>
                {pendingChans.length > 0 && (
                  <div className="flex-shrink-0 pt-3 border-t border-gray-100 dark:border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-gray-700 dark:text-slate-300">Selected ({pendingChans.length})</span>
                      <button onClick={() => setPendingChans([])} className="text-[11px] font-semibold text-gray-500 dark:text-slate-400 hover:underline">Clear All</button>
                    </div>
                    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
                      {pendingChans.map(ch => (
                        <span key={ch} className="flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-medium text-gray-700 dark:text-slate-300 whitespace-nowrap">
                          {v2ChanLabel(ch)}
                          <button onClick={() => togglePendingChan(ch)} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition">
                            <i className="fa-solid fa-xmark text-[9px]" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* DESKTOP: pill-wrap grid, unchanged */}
              <div className="hidden sm:flex flex-1 flex-col p-4 gap-5">
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-2">All Channels</p>
                  <div className="flex flex-wrap gap-1.5">
                    {v2ChanGrid.map(([val, lbl]) => {
                      const isSel = val === 'all-chans' ? pendingChans.length === 0 : pendingChans.includes(val);
                      return (
                        <button key={val}
                          onClick={() => val === 'all-chans' ? setPendingChans([]) : togglePendingChan(val)}
                          className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                            isSel ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100' : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:border-gray-300 dark:hover:border-slate-600'
                          }`}>{lbl}</button>
                      );
                    })}
                  </div>
                </div>
                {pendingChans.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100 dark:border-slate-800 mt-auto">
                    {pendingChans.map(ch => (
                      <span key={ch} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-xs font-medium text-gray-700 dark:text-slate-300">
                        {v2ChanLabel(ch)}
                        <button onClick={() => togglePendingChan(ch)} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition">
                          <i className="fa-solid fa-xmark text-[9px]" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── Product section ── */}
          {v2Section === 'product' && (
            <div className="flex-1 flex flex-col p-4 gap-3 min-h-0">
              <div className="relative">
                <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 text-xs" />
                <input
                  type="text"
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  placeholder="Search products..."
                  className="w-full pl-8 pr-3 py-2 text-xs bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg outline-none focus:border-gray-300 dark:focus:border-slate-600 text-gray-700 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 transition-colors"
                />
              </div>

              <div className="flex items-center justify-between px-0.5">
                <span className="text-[11px] font-medium text-gray-400 dark:text-slate-500">
                  {pendingProducts.length} selected
                </span>
                <button
                  onClick={() => setPendingProducts(
                    pendingProducts.length === filteredProducts.length ? [] : filteredProducts.map(p => p.id)
                  )}
                  className="text-[11px] font-semibold text-gray-600 dark:text-slate-300 hover:underline"
                >
                  {pendingProducts.length === filteredProducts.length && filteredProducts.length > 0 ? 'Clear all' : 'Select all'}
                </button>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
                  {filteredProducts.map(p => {
                    const checked = pendingProducts.includes(p.id);
                    return (
                      <button
                        key={p.id}
                        onClick={() => togglePendingProduct(p.id)}
                        className="flex items-start gap-2.5 w-full px-2.5 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800/40 text-left transition-colors min-w-0"
                      >
                        <div className={`w-4 h-4 mt-0.5 rounded flex items-center justify-center flex-shrink-0 border-2 transition-colors ${
                          checked ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-100' : 'border-gray-300 dark:border-slate-600'
                        }`}>
                          {checked && <i className="fa-solid fa-check text-[8px] text-white dark:text-gray-900" />}
                        </div>
                        <span className={`text-sm leading-snug break-words min-w-0 ${checked ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-slate-300'}`}>
                          {p.name}
                        </span>
                      </button>
                    );
                  })}
                </div>
                {filteredProducts.length === 0 && (
                  <p className="text-xs text-gray-400 dark:text-slate-500 text-center py-6">No products found</p>
                )}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 px-4 pb-4 pt-3 flex items-center justify-between gap-2 border-t border-gray-100 dark:border-slate-800">
        <button
          onClick={() => {
            setPendingDate('last-7-days');
            setPendingCats([]);
            setPendingChans([]);
            setPendingProducts([]);
            setAppliedDate(null);
            setAppliedCats([]);
            setAppliedChans([]);
            setAppliedProducts([]);
            setDateRange(null);
            setCategory('all');
            setChannel('all');
            setProducts([]);
            setV2FilterOpen(false);
          }}
          className="px-5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-red-500 dark:hover:text-red-400 transition"
        >
          Clear Filters
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setV2FilterOpen(false)}
            className="px-5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleApplyV2Filter}
            className="px-5 py-2 rounded-xl bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition"
          >
            Update
          </button>
        </div>
      </div>

    </div>
  );
};

export default WorkspaceFilterPanel;
