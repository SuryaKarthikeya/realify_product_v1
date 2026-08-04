import React from 'react';
import { DASHBOARD_VIEW_TABS } from '@/features/workspace/modules/dashboard-view/data/dashboardViewData';

// Renders the sales/margin/inventory/ads/cash tab strip. Used both as the
// full-size tab row and (compact=true) as the condensed sticky-header nav.
const DashboardViewTabNav = ({ _intelType, _onTabClick, _compact = false }) => (
  <div className="flex items-center gap-0.5 overflow-x-auto scrollbar-hide">
    {/* {DASHBOARD_VIEW_TABS.map(tab => (
      <button
        key={tab.key}
        onClick={() => onTabClick(tab.key)}
        className={`flex-shrink-0 ${compact ? 'px-3 py-1 text-xs gap-1' : 'px-4 py-1.5 text-base gap-1.5'} font-medium transition-colors whitespace-nowrap flex items-center border-b-2 -mb-px ${domain === tab.key
          ? 'border-gray-900 dark:border-slate-300 text-gray-900 dark:text-slate-100 font-bold'
          : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200'
          }`}
      >
        <i className={`fa-solid ${tab.icon} ${compact ? 'text-[11px]' : 'text-xs'}`} />
        {tab.label}
      </button>
    ))} */}
  </div>
);

export default DashboardViewTabNav;
