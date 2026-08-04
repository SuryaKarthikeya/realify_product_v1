import React, { useEffect, useState } from 'react';

/** Cycles while the mock analysis runs, so the wait reads as progress. */
const STAGES = ['Reading your data', 'Checking signals', 'Composing answer'];

/**
 * The "working on it" row: a spinning mark plus a label that advances through
 * STAGES. Purely cosmetic — the caller decides how long it stays mounted.
 */
const AnalysisThinking = () => {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 700);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-2.5 py-1" aria-live="polite">
      <i className="fa-solid fa-asterisk text-[15px] text-blue-600 dark:text-blue-400 animate-spin [animation-duration:1.6s]" />
      <span className="text-[14px] text-gray-500 dark:text-slate-400 animate-pulse">
        {STAGES[stage]}
      </span>
    </div>
  );
};

export default AnalysisThinking;
