import React from 'react';

/**
 * Save / Discard docked to the bottom of a settings panel.
 *
 */
const SettingsSaveFooter = ({ isDirty, onSave, onDiscard }) => (
  <div className="px-6 py-4 border-t border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 flex items-center justify-between gap-3">
    <p className="text-xs text-gray-500 dark:text-slate-400">
      {isDirty ? (
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
          You have unsaved changes
        </span>
      ) : (
        'Changes apply to this workspace only.'
      )}
    </p>

    <div className="flex items-center gap-2 flex-shrink-0">
      <button
        onClick={onDiscard}
        className="px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 rounded-xl text-sm font-bold hover:bg-gray-50 dark:hover:bg-slate-800 transition-all active:scale-95"
      >
        Discard
      </button>
      <button
        onClick={onSave}
        className="px-6 py-2 bg-brand text-white rounded-xl text-sm font-bold hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-all flex items-center gap-2 active:scale-95"
      >
        <i className="fa-solid fa-check text-[11px]" />
        Save
      </button>
    </div>
  </div>
);

export default SettingsSaveFooter;
