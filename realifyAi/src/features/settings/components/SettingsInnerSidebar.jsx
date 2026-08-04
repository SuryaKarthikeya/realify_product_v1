import React from 'react';
import { SETTINGS_NAV_ITEMS } from '@/features/settings/data/settingsNavItems';

const SettingsInnerSidebar = ({ activeTab, setActiveTab, onTabChange }) => {
  return (
    <div className="hidden lg:block w-64 flex-shrink-0">
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden sticky sticky-below-header shadow-[0_1px_3px_0_rgba(0,0,0,0.05)]">
        <nav className="py-2">
          {SETTINGS_NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                onTabChange();
              }}
              className={`w-full px-4 py-3 flex items-center gap-3 transition-all relative ${
                activeTab === item.id
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border-l-4 border-brand dark:border-gray-500'
                  : 'text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800/50 border-l-4 border-transparent'
              }`}
            >
              <i className={`fa-solid ${item.icon} w-5 text-center ${activeTab === item.id ? 'text-blue-600' : 'text-gray-400'}`}></i>
              <span className="text-sm font-medium">{item.name}</span>
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default SettingsInnerSidebar;
