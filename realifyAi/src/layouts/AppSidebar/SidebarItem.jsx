import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { Link } from 'react-router-dom';

/* ── Sidebar nav item ── */
const SidebarItem = ({ item, isCollapsed, small = false }) => {
  const [tooltip, setTooltip] = useState(null);
  return (
    <>
      <Link
        to={item.href}
        className={`flex items-center group relative w-full rounded-lg transition-colors ${isCollapsed ? 'justify-center px-0 py-1.5' : 'justify-start px-2 py-1.5'
          } ${item.active
            ? 'text-gray-900 dark:text-slate-100 bg-gray-100 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700/50 shadow-sm'
            : (isCollapsed && small)
              ? 'text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800/30'
              : 'text-gray-900 dark:text-slate-200 hover:text-gray-900 dark:hover:text-slate-100 hover:bg-gray-100 dark:hover:bg-slate-800/30'
          }`}
        onMouseEnter={isCollapsed ? (e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setTooltip({ top: r.top + r.height / 2, left: r.right + 12 });
        } : undefined}
        onMouseLeave={isCollapsed ? () => setTooltip(null) : undefined}
      >
        <div className={`flex items-center justify-center flex-shrink-0 rounded-md ${isCollapsed ? 'w-8 h-8' : 'w-7 h-7'}`}>
          <i
            className={`${item.regular ? 'fa-regular' : 'fa-solid'} ${item.icon}`}
            style={{ fontSize: isCollapsed ? (small ? 13 : 16) : 15 }}
          />
        </div>

        {!isCollapsed && (
          <span className={`ml-2 ${small ? 'text-xs' : 'text-sm'} font-normal whitespace-nowrap`}>
            {item.name}
          </span>
        )}
      </Link>

      {/* Fixed-position tooltip for collapsed state — portaled to body to escape z-index stacking context */}
      {isCollapsed && tooltip && ReactDOM.createPortal(
        <div
          style={{ position: 'fixed', top: tooltip.top, left: tooltip.left, transform: 'translateY(-50%)', zIndex: 99999 }}
          className="px-2 py-1 bg-slate-900 text-white text-[10px] rounded shadow-xl border border-slate-800 whitespace-nowrap pointer-events-none"
        >
          {item.name}
          <div className="absolute top-1/2 -left-1 -translate-y-1/2 w-1.5 h-1.5 bg-slate-900 rotate-45" />
        </div>,
        document.body
      )}
    </>
  );
};

export default SidebarItem;
