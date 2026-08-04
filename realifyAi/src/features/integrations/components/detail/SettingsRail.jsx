import React, { useMemo } from 'react';
import { settingsRail } from '@/features/integrations/data/connectorDetailData';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

const Heading = ({ icon, children }) => (
  <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white flex items-center gap-2">
    <i className={`fa-regular ${icon} text-[12px] text-gray-400 dark:text-slate-500`} />
    {children}
  </h3>
);

/**
 * The rail beside Settings.
 *
 * Where the other rails answer "what am I looking at", this one answers "where did
 * this connection come from and who do I ask" — provenance and help, which is what
 * a settings screen sends people looking for.
 */
const SettingsRail = ({ connector, onViewActivity }) => {
  const rail = useMemo(() => settingsRail(connector), [connector]);
  const healthy = rail.quality.tone === 'emerald';

  return (
    <div className="space-y-4">

      {/* ── About this integration ── */}
      <Card className="p-4">
        <Heading icon="fa-circle-question">About this integration</Heading>

        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed">
            {rail.about.body}
          </p>

          <div className="space-y-3">
            {rail.about.facts.map((fact) => (
              <div key={fact.key} className="flex items-start gap-2.5 min-w-0">
                <i className={`${fact.icon} text-[12px] text-gray-400 dark:text-slate-500 mt-[3px] flex-shrink-0`} />
                <div className="min-w-0">
                  <p className="text-[11px] text-gray-400 dark:text-slate-500">{fact.label}</p>
                  <p className="text-[12.5px] font-semibold text-gray-900 dark:text-white leading-snug">
                    {fact.value}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* ── Need help? ── */}
      <Card className="p-4">
        <Heading icon="fa-circle-question">Need help?</Heading>

        <div className="mt-2.5 -mx-1">
          {rail.help.map((link) => (
            <button
              key={link.key}
              className="w-full px-1 py-2 flex items-center gap-2.5 text-[12.5px] font-medium text-gray-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors group"
            >
              <i className={`fa-solid ${link.icon} text-[11px] text-gray-400 dark:text-slate-500 w-4 text-center flex-shrink-0`} />
              <span className="truncate">{link.label}</span>
              <i className="fa-solid fa-arrow-up-right-from-square text-[9px] ml-auto text-gray-300 dark:text-slate-600 group-hover:text-indigo-500 flex-shrink-0" />
            </button>
          ))}
        </div>
      </Card>

      {/* ── Data quality ── */}
      <Card className="p-4">
        <Heading icon="fa-shield">Data quality</Heading>

        <p
          className={`text-[12.5px] font-semibold mt-2.5 flex items-center gap-2 ${
            healthy ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${healthy ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          {rail.quality.label}
        </p>

        <div className="mt-1.5 flex items-end justify-between gap-3 flex-wrap">
          <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed min-w-0 flex-1">
            {rail.quality.body}
          </p>
          <button
            onClick={onViewActivity}
            className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-[12px] font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5 whitespace-nowrap flex-shrink-0"
          >
            View activity <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>
      </Card>
    </div>
  );
};

export default SettingsRail;
