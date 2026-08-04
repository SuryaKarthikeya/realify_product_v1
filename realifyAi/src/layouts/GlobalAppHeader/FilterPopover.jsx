import React, { useRef, useState, useEffect } from 'react';
import useClickOutside from '@/hooks/useClickOutside';
import { CHANNEL_OPTS, CATEGORY_OPTS, QUICK_DATE_OPTS } from '@/layouts/GlobalAppHeader/constants';
import { CAL_MONTHS, CAL_WEEKDAYS } from '@/constants/filterOptions';

/**
 * The header's filter dropdown: a sliders button that opens a panel with
 * date / channel / category sections. Selections are staged locally and only
 * pushed to the filter store when Update is pressed.
 */
const FilterPopover = ({ dateRange, setDateRange, category, setCategory, channel, setChannel, onPendingCountChange }) => {
  const now = new Date();

  const [open, setOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('date');

  const [pendingDate, setPendingDate] = useState(dateRange);
  const [pendingCategory, setPendingCategory] = useState(category);
  const [pendingChannel, setPendingChannel] = useState(channel);

  // Left calendar month (right = +1)
  const [calYear, setCalYear] = useState(now.getFullYear());
  const [calMonth, setCalMonth] = useState(now.getMonth() > 0 ? now.getMonth() - 1 : 0);
  const [rangeStart, setRangeStart] = useState(null);
  const [rangeEnd, setRangeEnd] = useState(null);
  const [hoverDate, setHoverDate] = useState(null);

  const btnRef = useRef(null);
  const panelRef = useRef(null);

  const rightYear = calMonth === 11 ? calYear + 1 : calYear;
  const rightMonth = calMonth === 11 ? 0 : calMonth + 1;

  // Report pending count to parent (for bell badge)
  useEffect(() => {
    if (!open) {
      onPendingCountChange?.(0);
      return;
    }
    const count = [pendingDate, pendingCategory, pendingChannel].filter(v => v !== 'all').length;
    onPendingCountChange?.(count);
  }, [open, pendingDate, pendingCategory, pendingChannel, onPendingCountChange]);

  // Click-outside to close
  useClickOutside(panelRef, open, () => setOpen(false), btnRef);

  const toggleOpen = () => {
    if (!open) {
      setPendingDate(dateRange);
      setPendingCategory(category);
      setPendingChannel(channel);
      setRangeStart(null);
      setRangeEnd(null);
    }
    setOpen(v => !v);
  };

  const handleUpdate = () => {
    setDateRange(pendingDate);
    setCategory(pendingCategory);
    setChannel(pendingChannel);
    setOpen(false);
  };

  const prevMonth = () => {
    if (calMonth === 0) { setCalMonth(11); setCalYear(y => y - 1); }
    else setCalMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (calMonth === 11) { setCalMonth(0); setCalYear(y => y + 1); }
    else setCalMonth(m => m + 1);
  };

  const handleDateClick = (year, month, day) => {
    const clicked = new Date(year, month, day);
    if (!rangeStart || rangeEnd) {
      setRangeStart(clicked);
      setRangeEnd(null);
      setPendingDate('custom');
    } else {
      if (clicked < rangeStart) { setRangeEnd(rangeStart); setRangeStart(clicked); }
      else { setRangeEnd(clicked); }
      setPendingDate('custom');
    }
    setHoverDate(null);
  };

  const sameDay = (a, b) => a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  const isInRange = (year, month, day) => {
    const d = new Date(year, month, day);
    const end = rangeEnd || hoverDate;
    if (!rangeStart || !end) return false;
    const [s, e] = rangeStart <= end ? [rangeStart, end] : [end, rangeStart];
    return d > s && d < e;
  };

  const renderCal = (year, month, showPrev, showNext) => {
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(year, month, 1).getDay();
    const cells = Array(firstDay).fill(null);
    for (let i = 1; i <= daysInMonth; i++) cells.push(i);
    return (
      <div className="flex-1 min-w-[185px]">
        <div className="flex items-center justify-between mb-3">
          {showPrev
            ? <button onClick={prevMonth} className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors"><i className="fa-solid fa-chevron-left text-[9px]" /></button>
            : <div className="w-6" />}
          <span className="text-[13px] font-semibold text-gray-800 dark:text-slate-200">
            {CAL_MONTHS[month]} <span className="font-normal text-gray-500 dark:text-slate-400">{year}</span>
          </span>
          {showNext
            ? <button onClick={nextMonth} className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors"><i className="fa-solid fa-chevron-right text-[9px]" /></button>
            : <div className="w-6" />}
        </div>
        <div className="grid grid-cols-7 mb-1">
          {CAL_WEEKDAYS.map(d => <div key={d} className="text-center text-[10px] font-medium text-gray-400 dark:text-slate-500 py-0.5">{d}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-y-0.5">
          {cells.map((day, idx) => {
            if (!day) return <div key={`e-${idx}`} />;
            const d = new Date(year, month, day);
            const isStart = sameDay(rangeStart, d);
            const isEnd = sameDay(rangeEnd, d);
            const inRange = isInRange(year, month, day);
            const isToday = sameDay(now, d);
            return (
              <button
                key={day}
                onClick={() => handleDateClick(year, month, day)}
                onMouseEnter={() => rangeStart && !rangeEnd && setHoverDate(d)}
                onMouseLeave={() => setHoverDate(null)}
                className={`relative h-7 w-full flex items-center justify-center text-[12px] rounded transition-colors
                  ${isStart || isEnd ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 font-semibold' : ''}
                  ${inRange ? 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300' : ''}
                  ${!isStart && !isEnd && !inRange ? 'hover:bg-gray-100 dark:hover:bg-slate-800/60 text-gray-700 dark:text-slate-300' : ''}
                `}
              >
                {day}
                {isToday && !isStart && !isEnd && (
                  <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-gray-400 dark:bg-slate-500" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  const renderRadioList = (opts, val, setVal) => (
    <div className="space-y-0.5 pt-1">
      {opts.map(([v, label]) => {
        const selected = val === v;
        return (
          <button key={v} onClick={() => setVal(v)}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800/40 text-left transition-colors"
          >
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${selected ? 'border-gray-900 dark:border-slate-200 bg-gray-900 dark:bg-slate-200' : 'border-gray-300 dark:border-slate-600'}`}>
              {selected && <div className="w-1.5 h-1.5 bg-white dark:bg-gray-900 rounded-full" />}
            </div>
            <span className={`text-sm ${selected ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-slate-300'}`}>{label}</span>
          </button>
        );
      })}
    </div>
  );

  const channelLabel = CHANNEL_OPTS.find(([v]) => v === pendingChannel)?.[1] || 'All Channels';
  const categoryLabel = CATEGORY_OPTS.find(([v]) => v === pendingCategory)?.[1] || 'All Categories';
  const navItems = [
    { id: 'date', label: 'Select Date' },
    { id: 'channel', label: channelLabel },
    { id: 'category', label: categoryLabel },
  ];

  return (
    <div className="relative">
      <button
        ref={btnRef}
        onClick={toggleOpen}
        title="Filters"
        className={`relative w-8 h-8 flex items-center justify-center rounded-xl border shadow-sm transition-all active:scale-95 ${open
          ? 'bg-gray-900 dark:bg-slate-100 border-gray-900 dark:border-slate-200 text-white dark:text-gray-900'
          : 'bg-gray-50 dark:bg-slate-800/60 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700'
          }`}
      >
        <i className="fa-solid fa-sliders text-xs" />
      </button>

      {open && (
        <div
          ref={panelRef}
          className="absolute right-0 top-full mt-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-xl z-[9999] overflow-hidden flex flex-col"
          style={{ width: 572 }}
        >
          <div className="flex" style={{ minHeight: 260 }}>
            {/* Left nav */}
            <div className="flex flex-col py-3 gap-1 px-2 flex-shrink-0 border-r border-gray-100 dark:border-slate-800" style={{ width: 148 }}>
              {navItems.map(nav => (
                <button
                  key={nav.id}
                  onClick={() => setActiveNav(nav.id)}
                  className={`flex items-center gap-2.5 w-full px-3 py-2.5 rounded-xl text-left transition-colors ${activeNav === nav.id
                    ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                    : 'text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800/40'
                    }`}
                >
                  <div className={`w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${activeNav === nav.id ? 'border-white dark:border-gray-900 bg-white dark:bg-gray-900' : 'border-gray-300 dark:border-slate-600'
                    }`}>
                    {activeNav === nav.id && <div className="w-1 h-1 bg-gray-900 dark:bg-slate-100 rounded-full" />}
                  </div>
                  <span className="text-[12px] font-medium truncate">{nav.label}</span>
                </button>
              ))}
            </div>

            {/* Right content */}
            <div className="flex-1 p-4 overflow-y-auto">
              {activeNav === 'date' && (
                <div>
                  <div className="flex items-center gap-2 mb-4 flex-wrap">
                    <span className="text-[11px] font-medium text-gray-400 dark:text-slate-500">Quick Filters</span>
                    {QUICK_DATE_OPTS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => { setPendingDate(opt.value); setRangeStart(null); setRangeEnd(null); }}
                        className={`px-3 py-1 rounded-full text-[11px] border transition-colors ${pendingDate === opt.value
                          ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 border-gray-900 dark:border-slate-100 font-semibold'
                          : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400 hover:border-gray-300 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/40'
                          }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    {renderCal(calYear, calMonth, true, false)}
                    <div className="w-px bg-gray-100 dark:bg-slate-800 flex-shrink-0 self-stretch" />
                    {renderCal(rightYear, rightMonth, false, true)}
                  </div>
                </div>
              )}
              {activeNav === 'channel' && renderRadioList(CHANNEL_OPTS, pendingChannel, setPendingChannel)}
              {activeNav === 'category' && renderRadioList(CATEGORY_OPTS, pendingCategory, setPendingCategory)}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-100 dark:border-slate-800 px-4 py-3 flex items-center justify-end gap-2.5">
            <button
              onClick={() => setOpen(false)}
              className="px-4 py-2 text-sm text-gray-600 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 font-medium transition-colors rounded-xl"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdate}
              className="px-5 py-2 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-sm font-semibold rounded-xl hover:bg-gray-700 dark:hover:bg-slate-200 active:scale-[0.98] transition-all"
            >
              Update
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPopover;
