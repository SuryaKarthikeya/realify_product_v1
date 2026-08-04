import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { screenerAlertsByPath } from '@/features/screener/data/screenerAlerts';

const borderColor = {
  red: 'border-l-red-500',
  amber: 'border-l-amber-500',
  blue: 'border-l-blue-500',
  emerald: 'border-l-emerald-500',
  orange: 'border-l-orange-500',
  purple: 'border-l-purple-500',
  slate: 'border-l-slate-500',
};

const badgeColor = {
  red: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
  amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
  blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
  emerald: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400',
  orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
  slate: 'bg-slate-50 dark:bg-slate-900/20 text-slate-600 dark:text-slate-400',
};

const iconBg = {
  red: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
  amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
  blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
  emerald: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400',
  orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
  slate: 'bg-slate-50 dark:bg-slate-900/20 text-slate-600 dark:text-slate-400',
};

const typeIcon = {
  critical: 'fa-triangle-exclamation',
  warning: 'fa-circle-exclamation',
  info: 'fa-circle-info',
  positive: 'fa-circle-check',
};

/* List-style card */
const ListCard = ({ item, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="w-full text-left flex items-center gap-4 p-4 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl hover:border-gray-200 dark:hover:border-slate-700 hover:shadow-sm transition-all group"
  >
    {/* Icon */}
    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg[item.color] || iconBg.slate}`}>
      <i className={`fa-solid ${typeIcon[item.type] || 'fa-circle-info'} text-sm`}></i>
    </div>

    {/* Content */}
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2 mb-1 flex-wrap">
        <span className={`text-[9px] font-bold tracking-widest uppercase px-1.5 py-0.5 rounded ${badgeColor[item.color] || badgeColor.slate}`}>
          {item.badge}
        </span>
        {item.actionId && (
          <>
            <span className="text-[10px] text-gray-400 dark:text-slate-500 font-medium">{item.actionId}</span>
            <span className="text-gray-300 dark:text-slate-700">·</span>
            <span className="text-[10px] text-gray-400 dark:text-slate-500">{item.time}</span>
          </>
        )}
      </div>
      <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-0.5 leading-tight">{item.title}</p>
      <p className="text-xs text-gray-500 dark:text-slate-400 leading-snug truncate">{item.body}</p>
    </div>

    {/* Metric */}
    {item.metricValue && (
      <div className="text-right flex-shrink-0">
        <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{item.metricValue}</p>
        <p className="text-[10px] text-gray-500 dark:text-slate-500">{item.metricLabel}</p>
      </div>
    )}

    <i className="fa-solid fa-chevron-right text-gray-300 dark:text-slate-600 text-xs flex-shrink-0 group-hover:text-gray-500 dark:group-hover:text-slate-400 transition-colors"></i>
  </button>
);

/* Grid-style card (SS2 / original style) */
const GridCard = ({ item, onClick, compact }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full text-left bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-sm border-l-4 transition-all hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md ${borderColor[item.color] || borderColor.slate} ${compact ? 'p-3' : 'p-4'}`}
  >
    <span className={`text-[9px] font-bold tracking-widest uppercase px-1.5 py-0.5 rounded inline-block mb-1.5 ${badgeColor[item.color] || badgeColor.slate}`}>
      {item.badge}
    </span>
    <div className={`font-bold text-gray-900 dark:text-slate-100 mb-0.5 ${compact ? 'text-xs leading-tight' : 'text-sm'}`}>
      {item.title}
    </div>
    <p className={`text-gray-500 dark:text-slate-400 leading-snug ${compact ? 'text-[11px] line-clamp-2' : 'text-xs'}`}>
      {item.body}
    </p>
    <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 mt-2 inline-flex items-center gap-1">
      {item.action} <i className="fa-solid fa-arrow-right text-[8px]" />
    </span>
  </button>
);

/* Compact card (stacked single-column) */
const CompactCard = ({ item, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full text-left flex items-center gap-3 px-3 py-2.5 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-lg hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-all border-l-4 ${borderColor[item.color] || borderColor.slate}`}
  >
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2 mb-0.5">
        <span className={`text-[9px] font-bold tracking-widest uppercase ${badgeColor[item.color] || badgeColor.slate} px-1 py-0.5 rounded`}>
          {item.badge}
        </span>
      </div>
      <p className="text-xs font-bold text-gray-900 dark:text-slate-100 leading-tight">{item.title}</p>
      <p className="text-[11px] text-gray-500 dark:text-slate-400 truncate mt-0.5">{item.body}</p>
    </div>
    <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 whitespace-nowrap flex-shrink-0">
      {item.action} →
    </span>
  </button>
);

const ScreenerAlertsPanel = ({ compact = false, className = '' }) => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('list');

  const items = screenerAlertsByPath[pathname] || screenerAlertsByPath['/screener'];
  const isMainScreener = pathname === '/screener';

  const handleClick = (item) => {
    if (item.id) {
      navigate(`/screener/actions/${item.id}`);
    }
  };

  return (
    <div className={className}>
      {/* Header row with title + view toggle */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-xs font-bold text-gray-800 dark:text-slate-500 uppercase tracking-wider">Actions</h3>
          {isMainScreener && (
            <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">Click to view deep-dive</p>
          )}
        </div>
        <div className="flex items-center gap-1 p-0.5 bg-gray-100 dark:bg-slate-800 rounded-lg">
          <button
            onClick={() => setViewMode('list')}
            className={`w-7 h-7 flex items-center justify-center rounded-md transition-all ${
              viewMode === 'list'
                ? 'bg-white dark:bg-slate-700 shadow-sm text-gray-700 dark:text-slate-200'
                : 'text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300'
            }`}
            title="List view"
          >
            <i className="fa-solid fa-bars text-xs"></i>
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`w-7 h-7 flex items-center justify-center rounded-md transition-all ${
              viewMode === 'grid'
                ? 'bg-white dark:bg-slate-700 shadow-sm text-gray-700 dark:text-slate-200'
                : 'text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300'
            }`}
            title="Grid view"
          >
            <i className="fa-solid fa-grip text-xs"></i>
          </button>
          <button
            onClick={() => setViewMode('compact')}
            className={`w-7 h-7 flex items-center justify-center rounded-md transition-all ${
              viewMode === 'compact'
                ? 'bg-white dark:bg-slate-700 shadow-sm text-gray-700 dark:text-slate-200'
                : 'text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300'
            }`}
            title="Compact view"
          >
            <i className="fa-solid fa-layer-group text-xs"></i>
          </button>
        </div>
      </div>

      {/* Cards */}
      {viewMode === 'list' && (
        <div className="flex flex-col gap-2">
          {items.map((item, idx) => (
            <ListCard
              key={`${item.title}-${idx}`}
              item={item}
              onClick={() => handleClick(item)}
            />
          ))}
        </div>
      )}

      {viewMode === 'grid' && (
        <div className="grid grid-cols-2 gap-3">
          {items.map((item, idx) => (
            <GridCard
              key={`${item.title}-${idx}`}
              item={item}
              compact={compact}
              onClick={() => handleClick(item)}
            />
          ))}
        </div>
      )}

      {viewMode === 'compact' && (
        <div className="flex flex-col gap-1.5">
          {items.map((item, idx) => (
            <CompactCard
              key={`${item.title}-${idx}`}
              item={item}
              onClick={() => handleClick(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ScreenerAlertsPanel;
