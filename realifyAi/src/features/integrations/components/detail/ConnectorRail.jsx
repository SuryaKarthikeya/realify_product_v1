import React from 'react';
import {
  RAIL_QUICK_ACTIONS,
  journeyProgress,
  railActivity,
} from '@/features/integrations/data/connectorDetailData';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

/**
 * The right rail on the connector detail page.
 *
 * Quick actions, help and activity are persistent across every tab. The journey
 * card is not: while the wizard is mid-flow it would restate the step rail the
 * user is already looking at, so the page suppresses it until the last step —
 * see `showJourney`.
 */
const ConnectorRail = ({
  connector,
  wizardStep = 0,
  setupComplete = false,
  showJourney = true,
  onQuickAction,
  onViewAllActivity,
}) => {
  const journey = journeyProgress(connector, wizardStep, setupComplete);
  const activity = railActivity(connector);

  return (
    <div className="space-y-4">

      {/* ── Onboarding journey ── */}
      {showJourney && (
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Onboarding journey</h3>
        <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">
          {journey.completed} of {journey.total} completed
        </p>

        <div className="mt-2.5 h-1.5 rounded-full bg-gray-100 dark:bg-slate-800 overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-500 transition-[width] duration-500"
            style={{ width: `${journey.pct}%` }}
          />
        </div>

        <div className="mt-3.5 space-y-2.5">
          {journey.steps.map((step) => {
            /* The step that just landed gets a tinted row, so the change the user
               caused is visible without re-reading the whole list. */
            const justDone = step.done && step.key === 'golive';
            return (
              <div
                key={step.key}
                className={`flex items-start gap-2.5 ${
                  justDone
                    ? 'rounded-xl bg-emerald-50/70 dark:bg-emerald-950/25 border border-emerald-100 dark:border-emerald-900/40 px-2.5 py-2 -mx-0.5'
                    : ''
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-[1px] ${
                    step.done
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'bg-rose-100 dark:bg-rose-950/50'
                  }`}
                >
                  {step.done ? (
                    <i className="fa-solid fa-check text-[10px]" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-rose-300 dark:bg-rose-800" />
                  )}
                </span>

                <div className="min-w-0 flex-1">
                  <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                    {justDone && <span className="text-gray-400 dark:text-slate-500 mr-1">{step.idx + 1}</span>}
                    {step.label}
                  </p>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-snug mt-0.5">
                    {step.hint}
                  </p>
                </div>

                {!justDone && (
                  <span
                    className={`text-[11px] font-semibold whitespace-nowrap flex-shrink-0 ${
                      step.done
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-amber-600 dark:text-amber-400'
                    }`}
                  >
                    {step.status}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </Card>
      )}

      {/* ── Quick actions ── */}
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-3">Quick actions</h3>
        <div className="grid grid-cols-2 gap-2">
          {RAIL_QUICK_ACTIONS.map((action) => (
            <button
              key={action.key}
              onClick={() => onQuickAction?.(action, connector)}
              className={`px-3 py-2 rounded-lg flex items-center gap-2 text-[12px] font-medium transition-colors ${
                action.danger
                  ? 'bg-rose-50/70 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-950/40'
                  : 'bg-gray-50 dark:bg-slate-800/60 text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
              }`}
            >
              <i className={`fa-solid ${action.icon} text-[11px] flex-shrink-0`} />
              <span className="truncate">{action.label}</span>
              <i className="fa-solid fa-chevron-right text-[8px] ml-auto opacity-50 flex-shrink-0" />
            </button>
          ))}
        </div>
      </Card>

      {/* ── Need help? ── */}
      <div className="rounded-2xl bg-gray-50/80 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 p-4 flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-1">Need help?</p>
          <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed">
            Learn how Realify connects, reads and secures your data.
          </p>
          <button className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-1.5 flex items-center gap-1.5">
            View documentation <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>
        <span className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
          <i className="fa-solid fa-book-open text-[13px]" />
        </span>
      </div>

      {/* ── Recent activity ── */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Recent activity</h3>
          <button
            onClick={onViewAllActivity}
            className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
          >
            View all
          </button>
        </div>

        <div className="space-y-2.5">
          {activity.map((item) => (
            <div key={item.label} className="flex items-start gap-2.5">
              <i
                className={`fa-solid ${item.done ? 'fa-check text-emerald-500' : 'fa-minus text-gray-300 dark:text-slate-600'} text-[10px] mt-[3px] flex-shrink-0`}
              />
              <p className="text-[12px] text-gray-800 dark:text-slate-200 leading-snug min-w-0 flex-1">
                {item.label}
              </p>
              <span className="text-[10.5px] text-gray-400 dark:text-slate-500 text-right flex-shrink-0 max-w-[72px] leading-snug">
                {item.when}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default ConnectorRail;
