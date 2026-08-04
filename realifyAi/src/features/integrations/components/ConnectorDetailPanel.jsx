import React, { useState } from 'react';
import { DETAIL_TABS, connectorDetail } from '@/features/integrations/data/integrationsData';
import { useSetupComplete } from '@/store/useIntegrationsStore';

const SectionLabel = ({ children }) => (
  <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5">
    {children}
  </p>
);

/** One `icon · label ......... value` row. */
const FactRow = ({ fact }) => (
  <div className="flex items-center justify-between gap-3 py-2 border-b border-gray-100 dark:border-slate-800 last:border-0">
    <span className="flex items-center gap-2.5 min-w-0 text-[12.5px] text-gray-600 dark:text-slate-400">
      <i className={`fa-solid ${fact.icon} text-[11px] text-gray-400 dark:text-slate-500 w-3.5 text-center flex-shrink-0`} />
      <span className="truncate">{fact.label}</span>
    </span>
    <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white text-right flex-shrink-0">
      {fact.value}
    </span>
  </div>
);

/**
 * Right-hand panel for one connector.
 *
 * Closed by default on the page — it only mounts once a card is picked. No
 * internal scroller: the panel grows with its content and the page scrolls, so
 * nothing is trapped behind a second scrollbar.
 */
const ConnectorDetailPanel = ({ connector, onClose, onPrimaryAction, onQuickAction }) => {
  const [tab, setTab] = useState('Overview');
  /* Read here rather than threaded down from the page: the panel is the only
     consumer, and the selector returns a boolean so it re-renders on this
     connector's completion alone. */
  const setupComplete = useSetupComplete(connector?.id);
  const detail = connectorDetail(connector, setupComplete);
  if (!detail) return null;

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-card dark:shadow-none font-sans">

      {/* ── Header ── */}
      <div className="px-4 pt-4 flex items-start justify-between gap-3">
        <span className="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-[9.5px] font-bold uppercase tracking-wider">
          Connector
        </span>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors flex-shrink-0"
          aria-label="Close connector details"
        >
          <i className="fa-solid fa-xmark text-[14px]" />
        </button>
      </div>

      <div className="px-4 pt-3">
        <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2.5">
          {detail.categoryLabel}
        </p>

        <div className="flex items-start gap-3">
          <span className={`w-10 h-10 rounded-xl flex-shrink-0 flex items-center justify-center text-[16px] ${connector.tone}`}>
            <i className={connector.icon} />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-[16px] font-bold text-gray-900 dark:text-white tracking-tight">
                {connector.name}
              </h2>
              <span
                className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider whitespace-nowrap ${
                  detail.needsAttention
                    ? 'bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400'
                    : detail.isLive
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'
                }`}
              >
                {detail.needsAttention ? 'Attention' : detail.isLive ? 'Connected' : 'Available'}
              </span>
            </div>
            <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5 truncate">
              Feeds: {detail.feeds.join(' · ')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="px-4 mt-3 border-b border-gray-100 dark:border-slate-800">
        <div className="flex items-center gap-5 overflow-x-auto scrollbar-hide">
          {DETAIL_TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-2.5 text-[12.5px] font-semibold whitespace-nowrap transition-colors relative ${
                tab === t
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200'
              }`}
            >
              {t}
              {tab === t && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-indigo-600 dark:bg-indigo-400 rounded-t-sm" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        {tab === 'Overview' && (
          <div>
            {detail.facts.map((fact) => (
              <FactRow key={fact.key} fact={fact} />
            ))}
          </div>
        )}

        {tab === 'Onboarding' && (
          <>
            <SectionLabel>Setup progress</SectionLabel>
            <ul className="space-y-2.5">
              {detail.onboardingSteps.map((step) => (
                <li key={step.label} className="flex items-start gap-2.5">
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-[1px] ${
                      step.done
                        ? 'bg-emerald-500 text-white'
                        : 'border border-gray-200 dark:border-slate-700'
                    }`}
                  >
                    {step.done && <i className="fa-solid fa-check text-[7px]" />}
                  </span>
                  <span
                    className={`text-[12px] ${
                      step.done
                        ? 'text-gray-800 dark:text-slate-200'
                        : 'text-gray-400 dark:text-slate-500'
                    }`}
                  >
                    {step.label}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}

        {tab === 'Scopes' && (
          <>
            <SectionLabel>Granted scopes</SectionLabel>
            <div className="flex flex-wrap gap-2">
              {detail.scopes.map((scope) => (
                <span
                  key={scope}
                  className="px-2.5 py-1 rounded-md bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 text-[11px] font-medium font-mono"
                >
                  {scope}
                </span>
              ))}
            </div>
          </>
        )}

        {tab === 'Activity' && (
          <>
            <SectionLabel>Recent activity</SectionLabel>
            <div className="space-y-3">
              {detail.activity.map((item) => (
                <div key={item.label} className="flex items-start gap-2.5">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-[1px] ${
                      item.tone === 'ok'
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                        : 'bg-gray-100 dark:bg-slate-800 text-gray-400 dark:text-slate-500'
                    }`}
                  >
                    <i className={`fa-solid ${item.tone === 'ok' ? 'fa-check' : 'fa-minus'} text-[8px]`} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[11.5px] font-medium text-gray-800 dark:text-slate-200 leading-snug">
                      {item.label}
                    </p>
                    <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-0.5">{item.when}</p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* ── Quick actions ── */}
      <div className="px-4 pb-4">
        <SectionLabel>Quick actions</SectionLabel>
        <div className="rounded-xl border border-gray-100 dark:border-slate-800 divide-y divide-gray-100 dark:divide-slate-800 overflow-hidden">
          {detail.quickActions.map((action) => (
            <button
              key={action.key}
              onClick={() => onQuickAction?.(action, connector)}
              className={`w-full px-3.5 py-2.5 flex items-center gap-2.5 text-[12.5px] font-medium transition-colors ${
                action.danger
                  ? 'text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20'
                  : 'text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
              }`}
            >
              <i className={`fa-solid ${action.icon} text-[11px] w-3.5 text-center flex-shrink-0`} />
              <span className="truncate">{action.label}</span>
              <i className="fa-solid fa-chevron-right text-[9px] ml-auto opacity-50 flex-shrink-0" />
            </button>
          ))}
        </div>
      </div>

      {/* ── Help ── */}
      <div className="px-4 pb-4">
        <div className="rounded-xl bg-gray-50/80 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 p-3.5 flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-bold text-gray-900 dark:text-white mb-1">Need help?</p>
            <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed">
              Learn how Realify reads, writes and secures your data.
            </p>
            <button className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-1.5 flex items-center gap-1.5">
              View docs <i className="fa-solid fa-arrow-right text-[9px]" />
            </button>
          </div>
          <span className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
            <i className="fa-solid fa-book-open text-[12px]" />
          </span>
        </div>
      </div>

      {/* ── Primary action ──
          Green once setup is done. It stays clickable because this button is the
          only way into the connector's own page — turning it into dead text would
          strand the user's finished integration behind nothing. */}
      <div className="px-4 pb-4">
        <button
          onClick={() => onPrimaryAction?.(connector)}
          className={`w-full py-2.5 rounded-xl text-white text-[13px] font-bold transition-colors flex items-center justify-center gap-2 ${
            detail.setupComplete
              ? 'bg-emerald-600 hover:bg-emerald-700'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {detail.setupComplete && <i className="fa-solid fa-circle-check text-[12px]" />}
          {detail.primaryAction}
        </button>
      </div>
    </div>
  );
};

export default ConnectorDetailPanel;
