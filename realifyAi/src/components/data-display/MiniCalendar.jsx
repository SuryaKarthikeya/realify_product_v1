import React from 'react';
import { CAL_MONTHS, CAL_WEEKDAYS } from '@/constants/filterOptions';
import { isSameDay, isInRange } from '@/utils/filterUtils';

// Single-month grid used twice side-by-side to build the date-range picker.
const MiniCalendar = ({ year, month, showPrev, showNext, onPrev, onNext, rangeStart, rangeEnd, hoverDay, onDateClick, onDateHover, onDateLeave }) => {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d));
  const todayRef = new Date(); todayRef.setHours(0, 0, 0, 0);
  const effectiveEnd = rangeEnd || (rangeStart && !rangeEnd ? hoverDay : null);

  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-2 px-0.5">
        {showPrev ? (
          <button onClick={onPrev} className="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition">
            <i className="fa-solid fa-chevron-left text-[9px]" />
          </button>
        ) : <span className="w-6" />}
        <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">
          {CAL_MONTHS[month]} <span className="text-gray-400 dark:text-slate-500 font-normal">{year}</span>
        </span>
        {showNext ? (
          <button onClick={onNext} className="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition">
            <i className="fa-solid fa-chevron-right text-[9px]" />
          </button>
        ) : <span className="w-6" />}
      </div>
      <div className="grid grid-cols-7 mb-0.5">
        {CAL_WEEKDAYS.map(d => (
          <div key={d} className="text-center text-[10px] font-medium text-gray-400 dark:text-slate-500 py-0.5">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((date, i) => {
          if (!date) return <div key={i} className="aspect-square" />;
          const isStart = isSameDay(date, rangeStart);
          const isEnd = isSameDay(date, rangeEnd);
          const inRange = isInRange(date, rangeStart, effectiveEnd);
          const isToday = isSameDay(date, todayRef);
          return (
            <div key={i} className="aspect-square flex items-center justify-center">
              <button
                onClick={() => onDateClick(date)}
                onMouseEnter={() => onDateHover(date)}
                onMouseLeave={onDateLeave}
                className={`w-6 h-6 flex items-center justify-center text-[11px] rounded-full transition-all ${isStart || isEnd
                  ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 font-bold'
                  : inRange
                    ? 'bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300'
                    : isToday
                      ? 'ring-1 ring-gray-400 dark:ring-slate-500 text-gray-900 dark:text-slate-100 font-semibold'
                      : 'text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800'
                  }`}
              >
                {date.getDate()}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MiniCalendar;
