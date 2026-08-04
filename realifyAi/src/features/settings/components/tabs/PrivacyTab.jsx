import React from 'react';

const PrivacyTab = () => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
      <div className="p-6 border-b border-gray-100 dark:border-slate-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Privacy & Data</h3>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Manage your data exports and account status</p>
      </div>

      <div className="p-6 space-y-6">
        <div className="p-5 border border-gray-100 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 shadow-sm flex items-center justify-between group hover:border-blue-200 dark:hover:border-blue-900 transition-all">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
              <i className="fa-solid fa-download text-xl"></i>
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Export Store Data</p>
              <p className="text-xs text-gray-500 dark:text-slate-500">Download all your synced store data in JSON/CSV format (GDPR Art. 20)</p>
            </div>
          </div>
          <button className="px-5 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all shadow-md active:scale-95">
            Export
          </button>
        </div>

        <div className="p-5 border border-gray-100 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 shadow-sm flex items-center justify-between group hover:border-gray-300 dark:hover:border-slate-700 transition-all">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gray-50 dark:bg-slate-800 rounded-xl flex items-center justify-center text-gray-600 dark:text-slate-400 group-hover:scale-110 transition-transform">
              <i className="fa-solid fa-list-check text-xl"></i>
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Access Audit Log</p>
              <p className="text-xs text-gray-500 dark:text-slate-500">Review all account actions and login history</p>
            </div>
          </div>
          <button className="px-5 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all">
            View Log
          </button>
        </div>

        <div className="mt-6 pt-5 border-t border-gray-100 dark:border-slate-800">
          <h4 className="text-sm font-bold text-red-600 dark:text-red-500 mb-4 tracking-wider">Danger Zone</h4>
          <div className="p-5 border border-red-100 dark:border-red-900/30 rounded-2xl bg-red-50/30 dark:bg-red-900/10 flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-red-700 dark:text-red-400">Delete Workspace</p>
              <p className="text-xs text-red-600/70 dark:text-red-400/50">This will permanently delete all your data and configurations. This action is irreversible.</p>
            </div>
            <button className="px-6 py-2 bg-red-600 text-white rounded-xl text-sm font-bold hover:bg-red-700 transition-all shadow-lg shadow-red-500/20 active:scale-95">
              Delete Forever
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyTab;
