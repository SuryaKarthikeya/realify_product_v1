import React from 'react';
import { useThemeStore } from '@/store/useThemeStore';

/**
 * Theme picker. Applies immediately and persists itself — no Save step.
 *
 * This used to keep its own `useState` copy of the theme and write the `dark`
 * class straight onto html/body, which left DashboardLayout's React-driven copy
 * of that class stale and broke Dark → Light. It now reads and writes the single
 * store that owns the theme, so both directions run one identical path.
 */
const AppearanceTab = () => {
  const currentTheme = useThemeStore((s) => s.theme);
  const handleThemeChange = useThemeStore((s) => s.setTheme);

  return (
    <>
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Appearance Settings</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Customize the interface theme and visual preferences</p>
      </div>

      <div className="p-6 space-y-6">
        {/* Theme Selection */}
        <section>
          <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-4">Interface Theme</h4>
          <div className="grid grid-cols-3 gap-4 sm:gap-6">
            {/* Dark Theme */}
            <div
              onClick={() => handleThemeChange('dark')}
              className={`cursor-pointer p-4 border-2 rounded-2xl transition-all ${
                currentTheme === 'dark'
                  ? 'border-blue-600 bg-blue-50/20 dark:border-blue-500 dark:bg-blue-900/20 shadow-sm'
                  : 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700'
              }`}
            >
              <div className="aspect-[16/7] bg-[#0c101a] rounded-xl mb-3 relative overflow-hidden border border-slate-800 p-2 flex flex-col justify-between">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-slate-700"></div>
                  <div className="w-10 h-1.5 rounded-full bg-slate-800"></div>
                </div>
                <div className="w-full h-3 rounded bg-blue-500/20 border border-blue-500/40"></div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Dark</p>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400">Sleek dark interface</p>
                </div>
                {currentTheme === 'dark' && (
                  <i className="fa-solid fa-circle-check text-blue-600 dark:text-blue-400 text-sm"></i>
                )}
              </div>
            </div>

            {/* Light Theme */}
            <div
              onClick={() => handleThemeChange('light')}
              className={`cursor-pointer p-4 border-2 rounded-2xl transition-all ${
                currentTheme === 'light'
                  ? 'border-blue-600 bg-blue-50/20 dark:border-blue-500 dark:bg-blue-900/20 shadow-sm'
                  : 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700'
              }`}
            >
              <div className="aspect-[16/7] bg-white rounded-xl mb-3 relative overflow-hidden border border-gray-200 p-2 flex flex-col justify-between">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-gray-200"></div>
                  <div className="w-10 h-1.5 rounded-full bg-gray-100"></div>
                </div>
                <div className="w-full h-3 rounded bg-blue-100 border border-blue-200"></div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Light</p>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400">Clean light interface</p>
                </div>
                {currentTheme === 'light' && (
                  <i className="fa-solid fa-circle-check text-blue-600 dark:text-blue-400 text-sm"></i>
                )}
              </div>
            </div>

            {/* Custom Theme */}
            <div
              onClick={() => handleThemeChange('custom')}
              className={`cursor-pointer p-4 border-2 rounded-2xl transition-all ${
                currentTheme === 'custom'
                  ? 'border-blue-600 bg-blue-50/20 dark:border-blue-500 dark:bg-blue-900/20 shadow-sm'
                  : 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700'
              }`}
            >
              <div className="aspect-[16/7] bg-gradient-to-r from-[#0c101a] to-white rounded-xl mb-3 relative overflow-hidden border border-gray-200 dark:border-slate-700 p-2 flex flex-col justify-between">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <div className="w-10 h-1.5 rounded-full bg-blue-400/50"></div>
                </div>
                <div className="w-full h-3 rounded bg-indigo-500/20 border border-indigo-400/40"></div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Custom Theme</p>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400">Adapts to system preferences</p>
                </div>
                {currentTheme === 'custom' && (
                  <i className="fa-solid fa-circle-check text-blue-600 dark:text-blue-400 text-sm"></i>
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default AppearanceTab;
