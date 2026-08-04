import React, { useState, useEffect } from 'react';
import { CHANNEL_MIX_DATA } from '@/features/workspace/modules/dashboard-view/data/dashboardViewData';

const ChannelMixWidget = () => {
  const C = 2 * Math.PI * 44;
  let cumulative = 0;

  // Sweep the ring in from 0 on mount, matching the load-in animation used by
  // the other detailed-view charts (e.g. the Revenue Trend area chart).
  const [animated, setAnimated] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => requestAnimationFrame(() => setAnimated(true)));
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 h-[380px] flex flex-col">
      <h3 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-4 flex-shrink-0">Channel Mix</h3>
      <div className="flex-1 flex justify-center items-center">
        <div className="relative w-44 h-44">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 112 112">
            <circle cx="56" cy="56" r="44" fill="none" stroke="currentColor" strokeWidth="18" className="text-gray-100 dark:text-slate-800" />
            {CHANNEL_MIX_DATA.map((ch) => {
              const offset = cumulative;
              // eslint-disable-next-line react-hooks/immutability
              cumulative += ch.pct;
              return (
                <circle
                  key={ch.label}
                  cx="56" cy="56" r="44"
                  fill="none"
                  stroke={ch.color}
                  strokeWidth="18"
                  strokeDasharray={animated ? `${ch.pct * C} ${(1 - ch.pct) * C}` : `0 ${C}`}
                  strokeDashoffset={`${-offset * C}`}
                  style={{ transition: 'stroke-dasharray 900ms ease-out' }}
                />
              );
            })}
          </svg>
          <div
            className="absolute inset-0 flex items-center justify-center flex-col"
            style={{ opacity: animated ? 1 : 0, transition: 'opacity 500ms ease-out 400ms' }}
          >
            <p className="text-lg font-bold text-gray-900 dark:text-slate-100">100%</p>
            <p className="text-[9px] text-gray-500 dark:text-slate-400 font-medium">Total Sales</p>
          </div>
        </div>
      </div>
      <div className="space-y-2">
        {CHANNEL_MIX_DATA.map((item, i) => (
          <div
            key={i}
            className="flex items-center justify-between py-2 px-3 rounded-xl border bg-gray-50 dark:bg-slate-800/50 border-gray-100 dark:border-slate-700/50"
            style={{ opacity: animated ? 1 : 0, transition: `opacity 400ms ease-out ${400 + i * 80}ms` }}
          >
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 ${item.dot} rounded-full flex-shrink-0`}></div>
              <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-gray-900 dark:text-slate-100">{Math.round(item.pct * 100)}%</span>
              <span className="text-[10px] text-gray-400 dark:text-slate-500 ml-1.5">{item.amount}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChannelMixWidget;
