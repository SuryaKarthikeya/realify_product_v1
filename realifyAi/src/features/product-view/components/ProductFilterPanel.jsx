import React from 'react';
import { CAL_MONTHS, CAL_WEEKDAYS } from '@/constants/filterOptions';


// ─── Product Filter Panel ─────────────────────────────────────────────────────

const ProductFilterPanel = ({ pendingDate, setPendingDate, customRange, setCustomRange, hoverDate, setHoverDate, calViewMonth, setCalViewMonth, onClose, onUpdate }) => {
  const today = new Date(); today.setHours(0, 0, 0, 0);

  const applyPreset = (preset) => {
    const t = new Date(today);
    let start, end;
    if (preset === '7d') { start = new Date(t.getTime() - 6 * 86400000); end = new Date(t); }
    if (preset === '30d') { start = new Date(t.getTime() - 29 * 86400000); end = new Date(t); }
    if (preset === '90d') { start = new Date(t.getTime() - 89 * 86400000); end = new Date(t); }
    setCustomRange({ start, end });
    setPendingDate(preset);
  };

  const isSame = (a, b) => a && b && a.toDateString() === b.toDateString();
  const inRange = (date) => {
    const s = customRange.start;
    const e = customRange.end || (customRange.start && !customRange.end ? hoverDate : null);
    if (!s) return false;
    const lo = e && s > e ? e : s;
    const hi = e && s > e ? s : e;
    return hi && date >= lo && date <= hi;
  };

  const handleDayClick = (date) => {
    if (!customRange.start || (customRange.start && customRange.end)) {
      setCustomRange({ start: date, end: null }); setPendingDate(null);
    } else {
      setCustomRange(date < customRange.start ? { start: date, end: customRange.start } : { start: customRange.start, end: date });
    }
  };

  const renderMonth = (year, month, isLeft) => {
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d));
    const goPrev = () => setCalViewMonth(p => p.month === 0 ? { year: p.year - 1, month: 11 } : { year: p.year, month: p.month - 1 });
    const goNext = () => setCalViewMonth(p => p.month === 11 ? { year: p.year + 1, month: 0 } : { year: p.year, month: p.month + 1 });
    return (
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          {isLeft ? <button onClick={goPrev} className="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 transition"><i className="fa-solid fa-chevron-left text-[9px]" /></button> : <span />}
          <p className="text-xs font-bold text-gray-800 dark:text-slate-100">{CAL_MONTHS[month]} {year}</p>
          {!isLeft ? <button onClick={goNext} className="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 transition"><i className="fa-solid fa-chevron-right text-[9px]" /></button> : <span />}
        </div>
        <div className="grid grid-cols-7 mb-1">{CAL_WEEKDAYS.map(d => <div key={d} className="text-[8px] sm:text-[9px] text-center text-gray-400 font-semibold py-1">{d}</div>)}</div>
        <div className="grid grid-cols-7">
          {cells.map((date, i) => {
            if (!date) return <div key={`e${i}`} />;
            const isStart = isSame(date, customRange.start);
            const isEnd = isSame(date, customRange.end || (customRange.start && !customRange.end ? hoverDate : null));
            const isIn = inRange(date);
            const isToday = isSame(date, today);
            return (
              <button key={date.getTime()} onClick={() => handleDayClick(date)}
                onMouseEnter={() => customRange.start && !customRange.end && setHoverDate(date)}
                onMouseLeave={() => setHoverDate(null)}
                className={`w-6 h-6 sm:w-8 sm:h-8 mx-auto flex items-center justify-center text-[10px] sm:text-[11px] font-medium rounded-lg transition-colors ${isStart || isEnd ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 font-bold'
                    : isIn ? 'bg-gray-200 dark:bg-slate-700 text-gray-800 dark:text-slate-200'
                      : isToday ? 'ring-1 ring-inset ring-gray-400 text-gray-900 dark:text-slate-100'
                        : 'text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
                  }`}>{date.getDate()}</button>
            );
          })}
        </div>
      </div>
    );
  };

  const nextCal = calViewMonth.month === 11
    ? { year: calViewMonth.year + 1, month: 0 }
    : { year: calViewMonth.year, month: calViewMonth.month + 1 };

  const getDurLabel = () => {
    if (pendingDate === '7d') return '7 days';
    if (pendingDate === '30d') return '30 days';
    if (pendingDate === '90d') return '90 days';
    if (customRange.start && customRange.end) {
      const days = Math.round((customRange.end - customRange.start) / 86400000) + 1;
      return `${days} days`;
    }
    return '—';
  };

  const fmtD = (d) => d ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
  const canUpdate = pendingDate || (customRange.start && customRange.end);

  return (
    <div className="fixed inset-x-4 top-20 bottom-4 sm:absolute sm:inset-x-auto sm:top-full sm:bottom-auto sm:mt-2 sm:right-0 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl shadow-xl z-[9999] sm:w-[460px] overflow-hidden flex flex-col">
      <div className="flex-1 min-h-0 overflow-y-auto sm:flex-none flex flex-col p-4 gap-3" style={{ minHeight: 320 }}>
        {/* Quick presets */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-gray-400 dark:text-slate-500">Quick Filters</span>
          {[['7d', 'Last 7 Days'], ['30d', 'Last 30 Days'], ['90d', 'Last 90 Days']].map(([val, lbl]) => (
            <button key={val} onClick={() => applyPreset(val)}
              className={`px-3 py-1 rounded-full border text-xs font-medium transition-all ${pendingDate === val ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900' : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:border-gray-300'}`}>
              {lbl}
            </button>
          ))}
        </div>
        {/* Dual calendar */}
        <div className="flex gap-2 sm:gap-4 flex-1">
          {renderMonth(calViewMonth.year, calViewMonth.month, true)}
          <div className="w-px bg-gray-100 dark:bg-slate-800 self-stretch flex-shrink-0" />
          {renderMonth(nextCal.year, nextCal.month, false)}
        </div>
        {/* Duration display */}
        <div className="flex items-center gap-3 pt-2 border-t border-gray-100 dark:border-slate-800">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-[11px] font-medium text-gray-700 dark:text-slate-300">
            <span className="w-2 h-2 rounded-full bg-gray-700 dark:bg-slate-300 flex-shrink-0" />
            {getDurLabel()}
          </div>
          {customRange.start && (
            <span className="text-[11px] text-gray-600 dark:text-slate-400">
              {fmtD(customRange.start)}{customRange.end ? ` — ${fmtD(customRange.end)}` : ''}
            </span>
          )}
        </div>
      </div>
      <div className="flex-shrink-0 px-4 pb-4 pt-3 flex justify-end gap-2 border-t border-gray-100 dark:border-slate-800">
        <button onClick={onClose} className="px-5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 text-xs font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition">Cancel</button>
        <button onClick={onUpdate} disabled={!canUpdate} className="px-5 py-2 rounded-xl bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold hover:bg-gray-700 dark:hover:bg-slate-200 transition disabled:opacity-40 disabled:cursor-not-allowed">Update</button>
      </div>
    </div>
  );
};

export default ProductFilterPanel;
