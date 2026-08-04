import React, { useEffect, useMemo, useState } from 'react';
import {
  getSimulationInputs,
  computeSimulation,
  ASSUMPTION_PRESETS,
} from '@/features/workspace/modules/simulation/data/simulationModalData';

export const SimulateContent = ({ insight, onClose, isModal = false }) => {
  // Resolve the base inputs for whichever insight opened the modal.
  const baseInputs = useMemo(() => getSimulationInputs(insight), [insight]);

  // Editable assumptions (start from the insight's defaults).
  const [capturePct, setCapturePct] = useState(baseInputs.capturePct);
  const [marginPct, setMarginPct] = useState(baseInputs.marginPct);
  const [rampDays, setRampDays] = useState(baseInputs.rampDays);
  const [activePreset, setActivePreset] = useState('expected');

  // Which formula panel (if any) is open. null = closed.
  const [activeFormula, setActiveFormula] = useState(null);

  // Recompute everything from the current assumptions.
  const sim = useMemo(
    () => computeSimulation({ ...baseInputs, capturePct, marginPct, rampDays }),
    [baseInputs, capturePct, marginPct, rampDays]
  );

  const applyPreset = (key) => {
    const preset = ASSUMPTION_PRESETS[key];
    if (!preset) return;
    setActivePreset(key);
    setCapturePct(preset.capturePct);
    setMarginPct(preset.marginPct);
    setRampDays(preset.rampDays);
    setActiveFormula(null);
  };

  const openFormula = (key) => setActiveFormula((prev) => (prev === key ? null : key));

  const renderInfoButton = (formulaKey) => (
    <button
      type="button"
      onClick={() => openFormula(formulaKey)}
      className="inline-flex items-center justify-center w-[15px] h-[15px] rounded-full border border-gray-900 dark:border-slate-300 text-gray-900 dark:text-slate-300 bg-transparent hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors align-middle shrink-0"
      aria-label="Show the math behind this number"
    >
      <span className="text-[9px] font-sans italic leading-none">i</span>
    </button>
  );

  const formula = activeFormula ? sim.formulas[activeFormula] : null;

  return (
    <div className={`relative w-full ${isModal ? 'max-w-[1280px] max-h-[96vh] rounded-[18px] shadow-2xl bg-white dark:bg-slate-900' : 'h-full bg-transparent overflow-y-auto custom-scrollbar'} flex flex-col p-4`} onClick={isModal ? (e) => e.stopPropagation() : undefined}>
      
      <div className="flex flex-col gap-3">
        
        {/* Header Box */}
        <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-4">
          <h3 className="text-[15px] font-bold text-gray-600 dark:text-slate-300 font-sans mb-1.5">Autofy Car Body Cover, Premium (12 SKUs)</h3>
          <p className="text-[13px] text-gray-500 dark:text-slate-400 leading-relaxed font-sans pr-4">
            Match price within 3% on the 8 highest-volume SKUs; hold price and lean on reviews for the remaining 4 lower-velocity SKUs.
          </p>
        </div>

        {/* Impact Metrics Row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-4">
            <div className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">REVENUE IMPACT</div>
            <div className="text-[16px] font-mono tracking-tight font-bold text-red-500">-$410K</div>
          </div>
          <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-4">
            <div className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">PROFIT IMPACT</div>
            <div className="text-[16px] font-mono tracking-tight font-bold text-red-500">-$90,200</div>
          </div>
          <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-4">
            <div className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">CONFIDENCE</div>
            <div className="text-[16px] font-mono tracking-tight font-bold text-emerald-600">Very high</div>
          </div>
        </div>

        {/* Affected SKUs */}
        <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-4">
          <div className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-3">AFFECTED SKUS</div>
          <div className="flex flex-wrap items-center gap-2">
            {['AF-CC-2044', 'AF-CC-2045', 'AF-CC-2046', 'AF-CC-2047', 'AF-CC-2048'].map(sku => (
              <span key={sku} className="bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-md px-3 py-1.5 text-[12px] font-mono text-gray-600 dark:text-slate-300 shadow-sm">
                {sku}
              </span>
            ))}
            <span className="text-[12px] text-gray-400 dark:text-slate-500 ml-1 font-sans mt-1">+7 more</span>
          </div>
        </div>

        {/* Adjust and Re-Run */}
        <div className="bg-gray-100/80 dark:bg-slate-800/80 rounded-xl p-5">
          <div className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-4">ADJUST AND RE-RUN</div>
          
          <div className="flex items-center justify-between mb-3">
            <span className="text-[14px] text-gray-700 dark:text-slate-300 font-sans">Price match depth</span>
            <span className="text-[14px] font-bold text-gray-900 dark:text-white font-mono">-6%</span>
          </div>
          
          <div className="relative w-full h-1 bg-gray-300 dark:bg-slate-600 rounded-full mb-6">
            <div className="absolute left-0 top-0 h-full bg-slate-800 dark:bg-slate-400 rounded-full" style={{width: '60%'}}></div>
            <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-slate-800 dark:bg-slate-200 rounded-full cursor-pointer shadow" style={{left: '60%'}}></div>
          </div>

          <div className="flex items-center p-1 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700">
            <button className="flex-1 py-2 text-[13px] font-bold text-gray-600 dark:text-slate-400 rounded-lg transition-colors hover:bg-gray-50 dark:hover:bg-slate-800 font-sans">
              Conservative
            </button>
            <button className="flex-1 py-2 text-[13px] font-bold text-gray-600 dark:text-slate-400 rounded-lg transition-colors hover:bg-gray-50 dark:hover:bg-slate-800 font-sans">
              Expected
            </button>
            <button className="flex-1 py-2 text-[13px] font-bold text-white bg-[#1a1f36] dark:bg-slate-700 rounded-lg transition-colors shadow-sm font-sans">
              Optimistic
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="px-1 mt-2">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200 dark:border-slate-700">
                <th className="py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider w-[33%]">HORIZON</th>
                <th className="py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider w-[33%]">REVENUE</th>
                <th className="py-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider w-[33%]">PROFIT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
              <tr>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">30 days</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$182,655</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$40,184</td>
              </tr>
              <tr>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">60 days</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$365,310</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$80,368</td>
              </tr>
              <tr>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">90 days</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$553,500</td>
                <td className="py-3.5 text-[14px] font-mono text-gray-700 dark:text-slate-300">-$121,770</td>
              </tr>
            </tbody>
          </table>
          
          <div className="mt-2 pt-4 border-t border-gray-100 dark:border-slate-800">
            <p className="text-[12px] text-gray-400 dark:text-slate-500 leading-relaxed font-sans pr-4">
              Directional estimate, not a guarantee. Based on high-confidence signal data and current run-rate.
            </p>
          </div>
        </div>

      </div>
      
      {isModal && (
        <div className="mt-4 pt-4 flex justify-end">
          <button onClick={onClose} className="px-6 py-2 rounded-lg bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 transition">Close</button>
        </div>
      )}
    </div>
  );
};

const SimulateModal = ({ isOpen, onClose, insight }) => {
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />
      <SimulateContent insight={insight} onClose={onClose} isModal={true} />
    </div>
  );
};

export default SimulateModal;
