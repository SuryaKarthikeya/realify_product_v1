import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';
import { historyItems } from '@/features/history';
import useClickOutside from '@/hooks/useClickOutside';
import { usePinnedChatsStore } from '@/store/usePinnedChatsStore';
import { truncateAtWordBoundary } from '@/utils/formatters';

/** The seven most recent chats, surfaced directly in the sidebar. */
const RECENT_HISTORY = [
  ...historyItems.today.map(h => ({ id: h.id, label: h.title })),
  ...historyItems.yesterday.map(h => ({ id: h.id, label: h.title })),
].slice(0, 7);

const HistorySectionContent = () => {
  const [groupBy, setGroupBy] = useState('none');
  const [groupByOpen, setGroupByOpen] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(true);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [fixedTooltip, setFixedTooltip] = useState(null);
  const groupByRef = useRef(null);
  const pinnedIds = usePinnedChatsStore(s => s.pinnedIds);
  const togglePinned = usePinnedChatsStore(s => s.togglePinned);

  useClickOutside(groupByRef, groupByOpen, () => setGroupByOpen(false));

  useEffect(() => {
    const handler = () => setActiveMenuId(null);
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const visibleHistory = RECENT_HISTORY;
  const pinnedItems = visibleHistory.filter(h => pinnedIds.includes(h.id));
  const recentItems = visibleHistory.filter(h => !pinnedIds.includes(h.id));

  const renderHistoryRow = (h) => {
    const pinned = pinnedIds.includes(h.id);
    return (
      <div
        key={h.id}
        className="relative group/hist flex items-center rounded hover:bg-gray-50 dark:hover:bg-slate-800/30 transition-colors"
        onMouseEnter={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setFixedTooltip({ label: h.label, top: rect.top + rect.height / 2, left: rect.right + 8 });
        }}
        onMouseLeave={() => setFixedTooltip(null)}
      >
        <Link
          to={ROUTES.HISTORY_DETAIL}
          state={{ chatId: h.id }}
          className="flex-1 block px-2 py-1.5 text-xs text-gray-900 dark:text-slate-200 hover:text-gray-700 dark:hover:text-slate-300 overflow-hidden whitespace-nowrap min-w-0 font-normal"
        >
          {truncateAtWordBoundary(h.label, 20)}
        </Link>
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); togglePinned(h.id); }}
          title={pinned ? 'Unpin chat' : 'Pin chat'}
          className={`w-5 h-5 flex-shrink-0 flex items-center justify-center rounded transition-colors ${pinned
            ? 'text-brand opacity-100'
            : 'text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 opacity-0 group-hover/hist:opacity-100'
            } ${activeMenuId === h.id ? 'opacity-100' : ''}`}
        >
          <i className="fa-solid fa-thumbtack text-[9px]" />
        </button>
        <div className={`relative flex-shrink-0 transition-opacity pr-1 ${activeMenuId === h.id ? 'opacity-100' : 'opacity-0 group-hover/hist:opacity-100'}`}>
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); setActiveMenuId(activeMenuId === h.id ? null : h.id); }}
            className="w-5 h-5 flex items-center justify-center rounded text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
          >
            <i className="fa-solid fa-ellipsis text-[9px]" />
          </button>
          {activeMenuId === h.id && (
            <div onMouseDown={e => e.stopPropagation()} className="absolute right-0 top-full mt-0.5 w-28 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg z-[9999] overflow-hidden py-1">
              {[
                { icon: 'fa-star', label: 'Star' },
                { icon: 'fa-pen', label: 'Rename' },
                { icon: 'fa-trash', label: 'Delete', danger: true },
              ].map(action => (
                <button
                  key={action.label}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 text-[11px] font-medium hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors ${action.danger ? 'text-red-500 dark:text-red-400' : 'text-gray-700 dark:text-slate-300'}`}
                >
                  <i className={`fa-solid ${action.icon} text-[9px]`} />
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="w-full mt-2 mb-1 px-1">
        {/* Pinned list */}
        {pinnedItems.length > 0 && (
          <div className="mb-2">
            <p className="px-1.5 mb-1 text-xs font-medium text-gray-400 dark:text-slate-500">Pinned</p>
            {pinnedItems.map(renderHistoryRow)}
          </div>
        )}

        {/* Header: Recents toggle + Group by icon */}
        <div className="group/recents flex items-center justify-between px-1.5 mb-1.5">
          <button
            onClick={() => setHistoryVisible(v => !v)}
            className="flex items-center gap-1 text-xs text-gray-400 dark:text-slate-500 hover:text-gray-500 dark:hover:text-slate-400 transition-colors"
          >
            <span className="font-medium">Recent</span>
            <i className={`fa-solid fa-chevron-${historyVisible ? 'down' : 'right'} text-[8px] opacity-0 group-hover/recents:opacity-100 transition-opacity`} />
          </button>
          <div className="relative" ref={groupByRef}>
            <button
              onClick={() => setGroupByOpen(o => !o)}
              className="group relative w-5 h-5 flex items-center justify-center rounded text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800/50 transition-colors"
            >
              <i className="fa-solid fa-sliders text-[9px]" />
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-1.5 py-0.5 bg-slate-900 text-white text-[9px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                Group by
              </span>
            </button>
            {groupByOpen && (
              <div className="absolute right-0 top-full mt-1 w-24 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg z-[9999] overflow-hidden py-1">
                {[['none', 'None'], ['date', 'Date'], ['project', 'Project']].map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => { setGroupBy(val); setGroupByOpen(false); }}
                    className="w-full flex items-center justify-between px-3 py-1.5 text-[11px] font-medium hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-slate-300 transition-colors"
                  >
                    <span>{label}</span>
                    {groupBy === val && <i className="fa-solid fa-check text-[9px] text-blue-500 dark:text-blue-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* History list */}
        {historyVisible && recentItems.map(renderHistoryRow)}

        {/* View All History */}
        <div className="mt-3 px-1">
          <Link
            to={ROUTES.HISTORY}
            className="w-full flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800/30 transition-colors"
          >
            <i className="fa-solid fa-clock-rotate-left text-[9px]" />
            <span>View All History</span>
          </Link>
        </div>
      </div>

      {/* Fixed-position tooltip — escapes overflow clipping */}
      {fixedTooltip && (
        <div
          style={{ position: 'fixed', top: fixedTooltip.top, left: fixedTooltip.left, transform: 'translateY(-50%)', zIndex: 99999 }}
          className="hidden md:block px-2.5 py-2 bg-white dark:bg-slate-900 text-gray-800 dark:text-slate-200 text-[10px] rounded-lg shadow-xl border border-gray-200 dark:border-slate-700 whitespace-normal w-52 leading-relaxed pointer-events-none"
        >
          {fixedTooltip.label}
          <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-white dark:border-r-slate-900" />
        </div>
      )}
    </>
  );
};

export default HistorySectionContent;
