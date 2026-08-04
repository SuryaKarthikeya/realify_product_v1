import React from 'react';
import WizardChrome from '@/features/agents/components/hire/WizardChrome';
import {
  WORKSPACES,
  TEAMS,
  WHAT_HAPPENS_NEXT,
  EXPECTED_OUTCOMES,
  coveragePath,
  selectedAutonomy,
  autonomyLabel,
} from '@/features/agents/data/hireWizardData';

/** Field heading with its Edit affordance, which jumps back to step 2. */
const ReviewField = ({ label, onEdit, children }) => (
  <div>
    <div className="flex items-center justify-between gap-2 mb-2">
      <p className="text-[12.5px] font-bold text-gray-700 dark:text-slate-300">{label}</p>
      <button
        onClick={onEdit}
        className="text-[11.5px] font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 flex items-center gap-1.5"
      >
        <i className="fa-solid fa-pencil text-[9px]" /> Edit
      </button>
    </div>
    {children}
  </div>
);

const CheckLine = ({ children }) => (
  <li className="flex items-start gap-2">
    <i className="fa-solid fa-check text-[9px] text-gray-400 dark:text-slate-500 mt-[3px] flex-shrink-0" />
    <span className="text-[11.5px] text-gray-600 dark:text-slate-400 leading-relaxed">{children}</span>
  </li>
);

/**
 * Step 3 — a read-only summary of everything chosen, then launch.
 *
 * The trust-level block lists every autonomy level granted in step 2, not just
 * the recommended one, since the grant is multi-select.
 */
const ReviewLaunchStep = ({ agent, draft, onBack, onEdit, onLaunch, onSaveDraft }) => {
  const specialistName = agent?.name || 'Pricing & Margin';
  const workspace = WORKSPACES.find((w) => w.id === draft.workspace) || WORKSPACES[0];
  const team = TEAMS.find((t) => t.id === draft.team) || TEAMS[0];
  const path = coveragePath(draft.coverage);
  const chosen = selectedAutonomy(draft.autonomy);

  return (
    <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 space-y-4 font-sans">
      <WizardChrome
        title={`Hire ${specialistName.split(' ')[0]} Specialist`}
        stepIndex={2}
        tagline="Review and launch"
        onBack={onBack}
        onSaveDraft={onSaveDraft}
        subs={{ specialist: specialistName, coverage: 'Workspace, team & trust' }}
      />

      <div className="flex flex-col xl:flex-row gap-5 items-start">

        {/* ── Summary ── */}
        <div className="flex-1 min-w-0 w-full space-y-5">
          <div>
            <h2 className="text-[15px] font-bold text-gray-900 dark:text-white">
              Review and launch your specialist
            </h2>
            <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1">
              Review the details below. You can go back to make changes.
            </p>
          </div>

          {/* Specialist */}
          <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex items-start gap-4">
            <span className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center text-[13px] font-bold flex-shrink-0">
              {specialistName.charAt(0)}
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <p className="text-[14px] font-bold text-gray-900 dark:text-white">
                  {specialistName} Specialist
                </p>
                <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-[9.5px] font-bold uppercase tracking-wider">
                  Shadow mode ({autonomyLabel(draft.autonomy)})
                </span>
              </div>
              <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mt-1">
                Runs the {specialistName} playbook to protect margins and grow profit.
              </p>
            </div>
          </div>

          <ReviewField label="Coverage" onEdit={onEdit}>
            <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 px-5 py-4 flex items-center gap-2 flex-wrap">
              {path.length === 0 ? (
                <span className="text-[12px] text-gray-400 dark:text-slate-500 italic">
                  No categories selected
                </span>
              ) : (
                path.map((node, idx) => (
                  <React.Fragment key={node.id}>
                    {idx > 0 && (
                      <i className="fa-solid fa-chevron-right text-[8px] text-gray-300 dark:text-slate-600" />
                    )}
                    <span
                      className={`text-[12.5px] ${
                        idx === path.length - 1
                          ? 'font-bold text-gray-900 dark:text-white'
                          : 'font-medium text-gray-600 dark:text-slate-400'
                      }`}
                    >
                      {node.label}
                    </span>
                  </React.Fragment>
                ))
              )}
            </div>
          </ReviewField>

          <ReviewField label="Workspace" onEdit={onEdit}>
            <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 px-5 py-4 flex items-center gap-3">
              <span className="w-7 h-7 rounded-md bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                {workspace.initials}
              </span>
              <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white">
                {workspace.label}
              </span>
            </div>
          </ReviewField>

          <ReviewField label="Team" onEdit={onEdit}>
            <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 px-5 py-4 flex items-center gap-3">
              <i className="fa-solid fa-users text-[12px] text-blue-600 dark:text-blue-400 w-7 text-center flex-shrink-0" />
              <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white">
                {team.label}
              </span>
            </div>
          </ReviewField>

          {/* Trust level — every granted rung, not only the recommended one */}
          <ReviewField label="Trust level" onEdit={onEdit}>
            <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/30 divide-y divide-gray-200/70 dark:divide-slate-800">
              {chosen.length === 0 ? (
                <p className="px-5 py-4 text-[12px] text-gray-400 dark:text-slate-500 italic">
                  No autonomy level granted
                </p>
              ) : (
                chosen.map((level) => (
                  <div
                    key={level.key}
                    className="px-5 py-4 flex flex-col lg:flex-row lg:items-start gap-4 lg:gap-5"
                  >
                    <div className="flex items-start gap-3 lg:w-[300px] lg:flex-shrink-0">
                      <span className="w-7 h-7 rounded-md bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 flex items-center justify-center flex-shrink-0 text-gray-500 dark:text-slate-400">
                        <i className={`fa-solid ${level.icon} text-[10px]`} />
                      </span>
                      <div className="min-w-0">
                        <p className="text-[12.5px] font-bold text-gray-900 dark:text-white">
                          {level.label}{level.recommended ? ' (Recommended)' : ''}
                        </p>
                        {level.lines.map((line) => (
                          <p key={line} className="text-[11.5px] text-gray-500 dark:text-slate-400 leading-relaxed">
                            {line}
                          </p>
                        ))}
                      </div>
                    </div>

                    <ul className="space-y-1.5 flex-1 min-w-0">
                      {level.benefits.map((b) => (
                        <CheckLine key={b}>{b}</CheckLine>
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </div>
          </ReviewField>

          <div className="rounded-2xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100/70 dark:border-blue-900/40 px-5 py-4 flex items-start gap-3">
            <span className="w-7 h-7 rounded-md bg-white dark:bg-slate-900 flex items-center justify-center flex-shrink-0 text-blue-600 dark:text-blue-400">
              <i className="fa-solid fa-user-plus text-[10px]" />
            </span>
            <div className="min-w-0">
              <p className="text-[12px] text-gray-700 dark:text-slate-300 leading-relaxed">
                This specialist will begin learning from your data immediately after launch.
              </p>
              <p className="text-[12px] text-blue-600 dark:text-blue-400 font-medium leading-relaxed">
                You can change trust level or coverage anytime.
              </p>
            </div>
          </div>
        </div>

        {/* ── What happens next ── */}
        <div className="w-full xl:w-[400px] xl:flex-shrink-0 space-y-4">
          <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <div className="flex items-center gap-2.5 mb-5">
              <span className="w-5 h-5 rounded-full bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 flex items-center justify-center flex-shrink-0">
                <i className="fa-solid fa-check text-[8px]" />
              </span>
              <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">
                What happens next?
              </h3>
            </div>

            <div className="space-y-4">
              {WHAT_HAPPENS_NEXT.map((item) => (
                <div key={item.title} className="flex items-start gap-3">
                  <span className="w-7 h-7 rounded-lg bg-gray-50 dark:bg-slate-800 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug">
                      {item.title}
                    </p>
                    <p className="text-[11.5px] text-gray-500 dark:text-slate-400 leading-relaxed mt-0.5">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={onLaunch}
              className="w-full mt-5 py-2.5 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-gray-900 text-[13px] font-bold hover:bg-gray-900 dark:hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
            >
              Confirm and Launch <i className="fa-solid fa-arrow-right text-[11px]" />
            </button>
          </div>

          <div className="rounded-2xl bg-gray-50/80 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 p-4">
            <h3 className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-3">
              Expected outcomes
            </h3>
            <ul className="space-y-1.5">
              {EXPECTED_OUTCOMES.map((o) => (
                <CheckLine key={o}>{o}</CheckLine>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewLaunchStep;
