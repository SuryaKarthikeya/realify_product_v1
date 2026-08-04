import React from 'react';
import {
  WORKSPACES,
  TEAMS,
  ONBOARDING_TASKS,
  ONBOARDING_PROGRESS,
  coveragePath,
  autonomyLabel,
} from '@/features/agents/data/hireWizardData';

/** One labelled fact in the left-hand summary column. */
const FactRow = ({ icon, label, children }) => (
  <div className="flex items-start gap-3">
    <span className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0">
      <i className={`fa-solid ${icon} text-[10px]`} />
    </span>
    <div className="min-w-0">
      <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">
        {label}
      </p>
      <div className="mt-0.5">{children}</div>
    </div>
  </div>
);

/**
 * The post-launch screen.
 *
 * `startedAt` is passed in rather than read from the clock here, so the time
 * shown is the moment the user actually launched and does not drift on re-render.
 */
const LaunchSuccessStep = ({ agent, draft, startedAt, onBackToAgents, onOpenSpecialist, onReturn }) => {
  const specialistName = agent?.name || 'Pricing & Margin';
  const workspace = WORKSPACES.find((w) => w.id === draft.workspace) || WORKSPACES[0];
  const team = TEAMS.find((t) => t.id === draft.team) || TEAMS[0];
  const path = coveragePath(draft.coverage);
  const mode = `Shadow (${autonomyLabel(draft.autonomy)})`;

  return (
    <div className="max-w-[1100px] mx-auto px-3 sm:px-4 py-3 font-sans">
      <button
        onClick={onBackToAgents}
        className="text-[12.5px] font-semibold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2"
      >
        <i className="fa-solid fa-arrow-left text-[11px]" /> Back to agents
      </button>

      {/* ── Confirmation ── */}
      <div className="flex flex-col items-center text-center mt-5 animate-in fade-in zoom-in-95 duration-300">
        <div className="relative w-20 h-20 flex items-center justify-center mb-4">
          <span className="absolute inset-0 rounded-full bg-emerald-50 dark:bg-emerald-950/30" />
          <span className="absolute top-1 right-3 w-1.5 h-1.5 rounded-full bg-violet-400" />
          <span className="absolute top-3 left-1 w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="absolute bottom-2 right-1 w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span className="absolute bottom-0 left-4 w-1.5 h-1.5 rounded-full bg-blue-300" />
          <span className="relative w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center">
            <i className="fa-solid fa-check text-[18px]" />
          </span>
        </div>

        <h1 className="text-[22px] font-bold text-gray-900 dark:text-white tracking-tight">
          {specialistName} Specialist is now live!
        </h1>
        <p className="text-[13px] text-gray-500 dark:text-slate-400 mt-2">
          Your specialist has been hired and is starting to learn your business.
        </p>

        <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-[10px] font-bold uppercase tracking-wider mt-4">
          <i className="fa-solid fa-shield-halved text-[10px]" /> Shadow mode ({autonomyLabel(draft.autonomy)})
        </span>
      </div>

      {/* ── Facts + onboarding ── */}
      <div className="mt-5 rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 dark:divide-slate-800">

        <div className="p-5 space-y-4">
          <FactRow icon="fa-user-tie" label="Specialist">
            <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
              {specialistName} Specialist
            </p>
          </FactRow>

          <FactRow icon="fa-shield-halved" label="Mode">
            <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">{mode}</p>
          </FactRow>

          <FactRow icon="fa-house" label="Coverage">
            <div className="flex items-center gap-1.5 flex-wrap">
              {path.map((node, idx) => (
                <React.Fragment key={node.id}>
                  {idx > 0 && (
                    <i className="fa-solid fa-chevron-right text-[7px] text-gray-300 dark:text-slate-600" />
                  )}
                  <span className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                    {node.label}
                  </span>
                </React.Fragment>
              ))}
            </div>
          </FactRow>

          <FactRow icon="fa-globe" label="Workspace">
            <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">{workspace.label}</p>
          </FactRow>

          <FactRow icon="fa-users" label="Team">
            <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">{team.label}</p>
          </FactRow>

          <FactRow icon="fa-clock" label="Started">
            <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">{startedAt}</p>
          </FactRow>
        </div>

        <div className="p-5">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">
            Onboarding in progress
          </h3>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1 leading-relaxed">
            The specialist is reading your data, playbook, and signals.
          </p>

          <div className="flex items-center gap-4 mt-4">
            <div className="flex-1 h-2 rounded-full bg-gray-100 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-600 transition-[width] duration-700"
                style={{ width: `${ONBOARDING_PROGRESS}%` }}
              />
            </div>
            <span className="text-[15px] font-bold text-gray-900 dark:text-white whitespace-nowrap">
              {ONBOARDING_PROGRESS}%
            </span>
          </div>

          <ul className="mt-4 space-y-3">
            {ONBOARDING_TASKS.map((task) => (
              <li key={task.label} className="flex items-center gap-3">
                {task.done ? (
                  <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0">
                    <i className="fa-solid fa-check text-[9px]" />
                  </span>
                ) : (
                  /* Spinner, not an empty circle — this step is actively running */
                  <span className="w-5 h-5 rounded-full border-2 border-indigo-200 dark:border-indigo-900 border-t-indigo-500 animate-spin flex-shrink-0" />
                )}
                <span
                  className={`text-[12px] ${
                    task.done
                      ? 'font-medium text-gray-700 dark:text-slate-300'
                      : 'text-gray-400 dark:text-slate-500'
                  }`}
                >
                  {task.label}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── Reassurance ── */}
      <div className="mt-4 rounded-2xl bg-gray-50/80 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 px-5 py-4 flex items-start gap-3.5">
        <span className="w-8 h-8 rounded-lg bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 flex items-center justify-center flex-shrink-0 text-blue-600 dark:text-blue-400">
          <i className="fa-regular fa-bell text-[12px]" />
        </span>
        <div className="min-w-0">
          <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
            No action is required.
          </p>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed mt-0.5">
            We'll notify you when the first set of recommendations is ready for review.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-5">
        <button
          onClick={onOpenSpecialist}
          className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
        >
          Open Specialist <i className="fa-solid fa-arrow-up-right-from-square text-[10px]" />
        </button>
        <button
          onClick={onReturn}
          className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};

export default LaunchSuccessStep;
