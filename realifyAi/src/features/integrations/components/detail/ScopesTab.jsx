import React, { useMemo, useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import {
  ACCESS_FILTERS,
  ACCESS_LEVEL_BY_KEY,
  connectorScopes,
  scopeSummary,
} from '@/features/integrations/data/connectorDetailData';
import { providerName } from '@/features/integrations/data/connectorDetailData';

/**
 * Scopes & Permissions.
 *
 * Toggling a scope is local state: it flips the card and moves the counters, so
 * the numbers above the grid always describe the grid below them.
 */
const ScopesTab = ({ connector }) => {
  const allScopes = useMemo(() => connectorScopes(connector), [connector]);
  const provider = providerName(connector);

  /* Which scopes are currently on. Seeded from whatever the connector was
     granted, then owned here so the toggles are live. */
  const [enabled, setEnabled] = useState(() =>
    connectorScopes(connector).filter((s) => s.state === 'granted').map((s) => s.key)
  );
  const [access, setAccess] = useState('all');
  const [query, setQuery] = useState('');

  /* State follows the toggle, so the counters react to what the user just did
     rather than to how the connector was first provisioned. */
  const scopes = useMemo(
    () =>
      allScopes.map((s) => ({
        ...s,
        state: enabled.includes(s.key) ? 'granted' : s.state === 'denied' ? 'denied' : 'pending',
      })),
    [allScopes, enabled]
  );

  const summary = useMemo(() => scopeSummary(scopes), [scopes]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return scopes.filter(
      (s) =>
        (access === 'all' || s.access === access) &&
        (!q || s.label.toLowerCase().includes(q) || s.description.toLowerCase().includes(q))
    );
  }, [scopes, access, query]);

  const activeCount = scopes.filter((s) => s.state === 'granted').length;

  const toggle = (key) =>
    setEnabled((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-[16px] font-bold text-gray-900 dark:text-white">Scopes &amp; Permissions</h2>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5">
            Control what Realify can access and do in your {provider} account.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <button className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors whitespace-nowrap">
            View raw scopes
          </button>
          <button className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-[12.5px] font-bold transition-colors whitespace-nowrap">
            Edit scopes
          </button>
        </div>
      </div>

      {/* ── Counters ── */}
      <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/25 grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 divide-x divide-gray-200 dark:divide-slate-800">
        {summary.map((tile) => (
          <div key={tile.key} className="px-5 py-4">
            <p className="text-[24px] font-bold text-gray-900 dark:text-white leading-none">
              {tile.value}
            </p>
            <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1.5">{tile.label}</p>
            <p className="text-[11.5px] font-semibold text-gray-700 dark:text-slate-300 mt-3">
              {tile.foot}
            </p>
            <div className="mt-1.5 h-[3px] rounded-full bg-gray-200 dark:bg-slate-700 overflow-hidden">
              <div
                className={`h-full rounded-full ${tile.bar} transition-[width] duration-300`}
                style={{ width: `${tile.barPct}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* ── Filters ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
          {activeCount} active scope{activeCount === 1 ? '' : 's'}
        </p>

        <div className="flex items-center gap-2.5 flex-shrink-0">
          <div className="flex items-center gap-1.5 text-[12px] text-gray-500 dark:text-slate-400">
            Access type:
            <SelectMenu
              value={access}
              options={ACCESS_FILTERS.map((f) => ({ id: f.key, label: f.label }))}
              onChange={setAccess}
              size="sm"
              ariaLabel="Access type"
              className="w-[132px] flex-shrink-0"
            />
          </div>

          <div className="relative">
            <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-[11px] text-gray-400 dark:text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search scopes..."
              className="w-[200px] pl-8 pr-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12px] text-gray-700 dark:text-slate-200 placeholder-gray-400 dark:placeholder-slate-500 outline-none focus:border-indigo-400 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* ── Scope cards ── */}
      {visible.length === 0 ? (
        <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-10 flex flex-col items-center text-center px-5">
          <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3 text-gray-400 dark:text-slate-500">
            <i className="fa-solid fa-key text-[14px]" />
          </div>
          <p className="text-[13px] font-bold text-gray-800 dark:text-slate-200 mb-1">
            No scopes match
          </p>
          <p className="text-[12px] text-gray-500 dark:text-slate-400">
            Clear the search or switch the access type back to All.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
          {visible.map((scope) => {
            const level = ACCESS_LEVEL_BY_KEY[scope.access];
            const on = scope.state === 'granted';
            return (
              <div
                key={scope.key}
                className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex flex-col"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-[13.5px] font-bold text-gray-900 dark:text-white leading-snug min-w-0">
                    {scope.label}
                  </p>

                  <button
                    onClick={() => toggle(scope.key)}
                    role="switch"
                    aria-checked={on}
                    aria-label={`${on ? 'Revoke' : 'Grant'} ${scope.label}`}
                    className={`relative w-9 h-5 rounded-full flex-shrink-0 transition-colors ${
                      on ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-slate-700'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-[left] ${
                        on ? 'left-[18px]' : 'left-0.5'
                      }`}
                    />
                  </button>
                </div>

                <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed mt-1.5">
                  {scope.description}
                </p>

                <div className="flex items-center gap-2 mt-3.5">
                  <span className="text-[11.5px] text-gray-500 dark:text-slate-400">Access</span>
                  <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${level.tone}`}>
                    {level.label}
                  </span>
                </div>

                <div className="mt-3.5 pt-3 border-t border-gray-100 dark:border-slate-800 flex items-end justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[10.5px] text-gray-400 dark:text-slate-500">Last authorized</p>
                    <p className="text-[11.5px] font-semibold text-gray-700 dark:text-slate-300 mt-0.5">
                      {on ? scope.authorized : 'Not granted'}
                    </p>
                  </div>
                  <button
                    aria-label={`Open ${scope.label} details`}
                    className="text-gray-300 dark:text-slate-600 hover:text-gray-500 dark:hover:text-slate-400 transition-colors flex-shrink-0"
                  >
                    <i className="fa-solid fa-chevron-right text-[11px]" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Footnote ── */}
      <div className="rounded-2xl bg-blue-50/70 dark:bg-blue-950/25 border border-blue-100 dark:border-blue-900/40 p-4 flex items-start gap-3">
        <i className="fa-solid fa-circle-info text-[13px] text-blue-500 dark:text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="min-w-0">
          <p className="text-[12.5px] text-gray-800 dark:text-slate-200 leading-relaxed">
            Scopes define what data Realify can access and what actions it can perform.
          </p>
          <p className="text-[12.5px] text-gray-600 dark:text-slate-400 leading-relaxed">
            You can update permissions anytime.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScopesTab;
