import React from 'react';
import { WIZARD_STEPS } from '@/features/agents/data/hireWizardData';

/**
 * Shared chrome for the hire wizard: back arrow, title, "Step N of 3" line,
 * Save as draft, and the three-stage rail.
 *
 * `stepIndex` drives everything — steps before it read as complete, the index
 * itself as current, the rest as pending — so both steps use one component and
 * cannot disagree about progress.
 */
const WizardChrome = ({ title, stepIndex, tagline, onBack, onSaveDraft, subs = {} }) => (
  <>
    <div className="flex items-start justify-between gap-4">
      <div className="flex items-start gap-3 min-w-0">
        <button
          onClick={onBack}
          className="w-9 h-9 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex items-center justify-center text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex-shrink-0"
          aria-label="Back"
        >
          <i className="fa-solid fa-arrow-left text-[13px]" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-user-plus text-[12px]" />
            </span>
            <h1 className="text-[19px] font-bold text-gray-900 dark:text-white tracking-tight">
              {title}
            </h1>
          </div>
          <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1 ml-[38px]">
            Step {stepIndex + 1} of {WIZARD_STEPS.length} &nbsp;•&nbsp; {tagline}
          </p>
        </div>
      </div>

      <button
        onClick={onSaveDraft}
        className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap flex-shrink-0"
      >
        <i className="fa-regular fa-bookmark text-[11px]" /> Save as draft
      </button>
    </div>

    {/* ── Three-stage rail ── */}
    <div className="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-5 py-4">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-0">
        {WIZARD_STEPS.map((step, idx) => {
          const isDone = idx < stepIndex;
          const isCurrent = idx === stepIndex;
          return (
            <React.Fragment key={step.key}>
              <div className="flex items-center gap-3 min-w-0 flex-shrink-0">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${
                    isDone || isCurrent
                      ? 'bg-[#0f172a] dark:bg-white text-white dark:text-gray-900'
                      : 'bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-400 dark:text-slate-500'
                  }`}
                >
                  {isDone ? <i className="fa-solid fa-check text-[10px]" /> : idx + 1}
                </div>
                <div className="min-w-0">
                  <p
                    className={`text-[12.5px] font-bold leading-snug ${
                      isDone || isCurrent
                        ? 'text-gray-900 dark:text-white'
                        : 'text-gray-400 dark:text-slate-500'
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-snug">
                    {subs[step.key] || step.sub}
                  </p>
                </div>
              </div>

              {/* Connector only between stages, never trailing the last one */}
              {idx < WIZARD_STEPS.length - 1 && (
                <div className="hidden sm:block flex-1 h-[1px] bg-gray-200 dark:bg-slate-700 mx-4" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  </>
);

export default WizardChrome;
