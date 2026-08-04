import React from 'react';
import {
  PERMISSION_LEVELS,
  providerName,
} from '@/features/integrations/data/connectorDetailData';

/**
 * The rail beside Scopes & Permissions.
 *
 * Deliberately not the standard rail: on this tab the useful context is what the
 * access levels mean and how to revoke them, not where setup has got to.
 */
const ScopesRail = ({ connector, onDisconnect }) => {
  const provider = providerName(connector);

  return (
    <div className="space-y-4">

      {/* ── Permission levels ── */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-3">
          Permission levels
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {PERMISSION_LEVELS.map((level) => (
            <div key={level.key} className="min-w-0">
              <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold whitespace-nowrap ${level.tone}`}>
                {level.label}
              </span>
              <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-snug mt-1.5">
                {level.body}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── About scopes ── */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <i className="fa-solid fa-circle-info text-[12px] text-indigo-500 dark:text-indigo-400" />
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">About scopes</h3>
        </div>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed">
          Scopes define the data and actions Realify can perform in your {provider} account.
        </p>
        <button className="text-[12px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-2.5 flex items-center gap-1.5">
          Learn more about scopes <i className="fa-solid fa-arrow-up-right-from-square text-[9px]" />
        </button>
      </div>

      {/* ── Disconnect ── */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <i className="fa-solid fa-triangle-exclamation text-[12px] text-rose-500 dark:text-rose-400" />
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Need to disconnect?</h3>
        </div>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed">
          Revoke access and remove Realify from your {provider} account.
        </p>
        <button
          onClick={onDisconnect}
          className="mt-3 px-3.5 py-2 rounded-xl border border-rose-200 dark:border-rose-900/60 text-[12.5px] font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/25 transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
};

export default ScopesRail;
