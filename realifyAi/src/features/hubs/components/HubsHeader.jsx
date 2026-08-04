import { memo } from 'react';

const TABS = [
  { id: 'discover', label: 'Discover' },
  { id: 'installed', label: 'Installed (2)' },
  { id: 'updates', label: 'Updates', badge: '1' },
];

const HubsHeader = memo(({ activeTab, onTabChange }) => (
  <header className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 sticky top-0 z-40 shadow-sm">
    <div className="px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Hubs</h2>
          <p className="text-sm text-gray-600 dark:text-slate-400">
            Discover and install powerful plugins to enhance your platform
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <i className="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search plugins..."
              className="pl-9 pr-4 py-2 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 w-64 dark:text-white dark:placeholder-slate-400"
            />
          </div>

          <button className="p-2 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl border border-gray-200 dark:border-slate-700 transition relative">
            <i className="fa-solid fa-bell text-gray-600 dark:text-slate-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>

          <button className="p-2 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl border border-gray-200 dark:border-slate-700 transition">
            <div className="w-8 h-8 rounded-lg bg-slate-800 dark:bg-slate-600 flex items-center justify-center text-white text-sm font-bold">
              R
            </div>
          </button>
        </div>
      </div>

      <div className="flex items-center gap-6 border-b border-gray-100 dark:border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`pb-3 text-sm transition-colors ${
              activeTab === tab.id
                ? 'font-semibold text-blue-600 border-b-2 border-brand dark:border-gray-500 -mb-px'
                : 'font-medium text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {tab.label}
            {tab.badge && (
              <span className="ml-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 py-0.5 px-1.5 rounded-md text-xs">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  </header>
));

HubsHeader.displayName = 'HubsHeader';

export default HubsHeader;
