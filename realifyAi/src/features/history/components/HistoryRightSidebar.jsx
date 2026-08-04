import React from 'react';

const HistoryRightSidebar = ({
  quickFilters,
  mostUsedSearches,
  activeFilter = 'all',
  onFilterChange,
  bookmarkCount,
}) => {
  return (
    <aside
      id="right-sidebar"
      className="hidden xl:flex flex-col w-72 bg-transparent self-stretch shrink-0 z-10"
    >
      {/* Quick Filters */}
      <div className="pl-6 pr-4 pt-4 pb-4 border-b border-gray-200 dark:border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium text-gray-900 dark:text-slate-100">Quick Filters</h2>
          <button title="Export History" className="w-7 h-7 flex items-center justify-center rounded-lg border border-gray-200 dark:border-slate-700 text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-gray-700 dark:hover:text-slate-200 transition-colors">
            <i className="fa-solid fa-file-arrow-down text-xs" />
          </button>
        </div>
        <div className="space-y-2">
          {quickFilters.map((filter) => {
            const isActive = filter.id === activeFilter;
            const count = filter.id === 'bookmarked' && bookmarkCount !== undefined
              ? bookmarkCount
              : filter.count;
            return (
              <button
                key={filter.id}
                onClick={() => onFilterChange && onFilterChange(filter.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all text-sm font-medium ${
                  isActive
                    ? 'bg-slate-100 dark:bg-slate-800/60 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200'
                    : 'hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-gray-200 dark:hover:border-slate-700 hover:shadow-sm text-gray-700 dark:text-slate-300'
                }`}
              >
                <span className="flex items-center gap-2">
                  <i className={`fa-solid ${filter.icon}`}></i>
                  {filter.name}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-slate-200 dark:bg-slate-700' : 'bg-gray-100 dark:bg-slate-800'}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Most Used Searches */}
      <div className="flex-1 overflow-y-auto pl-6 pr-4 py-4 hide-scroll">
        <h2 className="font-medium text-gray-900 dark:text-slate-100 mb-3">Most Used Searches</h2>
        <div className="space-y-2">
          {mostUsedSearches.map((search, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-3">
              <div className="flex items-start gap-2 mb-2">
                <span className="text-sm font-medium text-gray-900 dark:text-slate-100 line-clamp-2">{search.title}</span>
              </div>
              <div className="text-xs text-gray-500 dark:text-slate-400">Used {search.count} times</div>
            </div>
          ))}
        </div>
      </div>

    </aside>
  );
};

export default HistoryRightSidebar;
