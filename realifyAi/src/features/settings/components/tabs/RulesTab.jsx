import React, { useState } from 'react';

const RulesTab = () => {
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [rules, setRules] = useState({
    netMargin: { enabled: true, val: 15, surface: 'Watch' },
    returnRate: { enabled: true, val: 8, surface: 'Act' },
    revenueShare: { enabled: true, val: 8, surface: 'Watch' },
    daysOfCover: { enabled: true, val: 14, surface: 'Act' },
    buyBoxLoss: { enabled: true, val: 5, surface: 'Act' },
  });

  const toggleRule = (key) => {
    setRules(prev => ({
      ...prev,
      [key]: { ...prev[key], enabled: !prev[key].enabled }
    }));
  };

  const updateVal = (key, val) => {
    setRules(prev => ({
      ...prev,
      [key]: { ...prev[key], val }
    }));
  };

  const updateSurface = (key, surface) => {
    setRules(prev => ({
      ...prev,
      [key]: { ...prev[key], surface }
    }));
  };

  return (
    <>
      <div>
        {/* Full-bleed header, then padded body — same shell as the other
            settings tabs, which the panel itself provides no padding for. */}
        <div className="p-6 border-b border-gray-100 dark:border-slate-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">
            Detectors &amp; thresholds
          </h3>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-w-4xl">

          {/* Subtext description */}
          <p className="text-xs text-gray-500 dark:text-slate-400 leading-relaxed">
            These are the signals Realify watches. Tune the <strong className="text-gray-700 dark:text-slate-300">threshold</strong>, turn a detector on/off, or change how loudly it surfaces — changes apply to <strong className="text-gray-700 dark:text-slate-300">your account only</strong>. How Realify <em>interprets</em> a detector (the tailored readings shown as chips) is managed by Realify.
          </p>

          {/* ── Category 1: MARGIN ── */}
          <div className="space-y-4">
            <h3 className="text-[10px] font-bold tracking-wider uppercase text-gray-400 dark:text-slate-500">
              MARGIN
            </h3>

            {/* Rule 1 */}
            <div className="bg-gray-50/70 dark:bg-slate-800/50 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-slate-100">
                    Net margin falls below your floor
                  </h4>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">
                    Net margin falls below your floor
                  </p>
                </div>
                {/* Toggle switch */}
                <button
                  onClick={() => toggleRule('netMargin')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${rules.netMargin.enabled ? 'bg-emerald-600 dark:bg-emerald-500' : 'bg-gray-300 dark:bg-slate-700'
                    }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${rules.netMargin.enabled ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                </button>
              </div>

              {/* Threshold controls */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Net margin below %
                  </label>
                  <input
                    type="number"
                    value={rules.netMargin.val}
                    onChange={(e) => updateVal('netMargin', e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Surface as
                  </label>
                  <select
                    value={rules.netMargin.surface}
                    onChange={(e) => updateSurface('netMargin', e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200 cursor-pointer"
                  >
                    <option value="Watch">Watch</option>
                    <option value="Act">Act</option>
                    <option value="Ignore">Ignore</option>
                  </select>
                </div>
              </div>

              {/* Realify tailored chips */}
              <div className="pt-1 flex flex-wrap gap-1.5">
                <span className="text-[9px] font-medium text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 px-2 py-0.5 rounded-full border border-amber-200 dark:border-amber-800/40">
                  Returns eroding margin
                </span>
                <span className="text-[9px] font-medium text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full border border-indigo-200 dark:border-indigo-800/40">
                  Ad spend below breakeven
                </span>
                <span className="text-[9px] font-medium text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900/30 px-2 py-0.5 rounded-full border border-purple-200 dark:border-purple-800/40">
                  Margin thin while losing Buy Box
                </span>
              </div>
            </div>

            {/* Rule 2 */}
            <div className="bg-gray-50/70 dark:bg-slate-800/50 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-slate-100">
                    Return rate rises above your ceiling
                  </h4>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">
                    Return rate rises above your ceiling
                  </p>
                </div>
                <button
                  onClick={() => toggleRule('returnRate')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${rules.returnRate.enabled ? 'bg-emerald-600 dark:bg-emerald-500' : 'bg-gray-300 dark:bg-slate-700'
                    }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${rules.returnRate.enabled ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Return rate above %
                  </label>
                  <input
                    type="number"
                    value={rules.returnRate.val}
                    onChange={(e) => updateVal('returnRate', e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Surface as
                  </label>
                  <select
                    value={rules.returnRate.surface}
                    onChange={(e) => updateSurface('returnRate', e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200 cursor-pointer"
                  >
                    <option value="Act">Act</option>
                    <option value="Watch">Watch</option>
                    <option value="Ignore">Ignore</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* ── Category 2: SALES ── */}
          <div className="space-y-4">
            <h3 className="text-[10px] font-bold tracking-wider uppercase text-gray-400 dark:text-slate-500">
              SALES
            </h3>

            {/* Rule 3 */}
            <div className="bg-gray-50/70 dark:bg-slate-800/50 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-slate-100">
                    A SKU's revenue share crosses your concentration line
                  </h4>
                  <p className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">
                    A SKU's revenue share crosses your concentration line
                  </p>
                </div>
                <button
                  onClick={() => toggleRule('revenueShare')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${rules.revenueShare.enabled ? 'bg-emerald-600 dark:bg-emerald-500' : 'bg-gray-300 dark:bg-slate-700'
                    }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${rules.revenueShare.enabled ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Revenue-share above %
                  </label>
                  <input
                    type="number"
                    value={rules.revenueShare.val}
                    onChange={(e) => updateVal('revenueShare', e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Surface as
                  </label>
                  <select
                    value={rules.revenueShare.surface}
                    onChange={(e) => updateSurface('revenueShare', e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200 cursor-pointer"
                  >
                    <option value="Watch">Watch</option>
                    <option value="Act">Act</option>
                    <option value="Ignore">Ignore</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* ── Category 3: INVENTORY ── */}
          <div className="space-y-4">
            <h3 className="text-[10px] font-bold tracking-wider uppercase text-gray-400 dark:text-slate-500">
              INVENTORY
            </h3>

            {/* Rule 4 */}
            <div className="bg-gray-50/70 dark:bg-slate-800/50 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-slate-100">
                    Days of Cover drops below safety threshold
                  </h4>
                </div>
                <button
                  onClick={() => toggleRule('daysOfCover')}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${rules.daysOfCover.enabled ? 'bg-emerald-600 dark:bg-emerald-500' : 'bg-gray-300 dark:bg-slate-700'
                    }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${rules.daysOfCover.enabled ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    DOC below (days)
                  </label>
                  <input
                    type="number"
                    value={rules.daysOfCover.val}
                    onChange={(e) => updateVal('daysOfCover', e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 block mb-1">
                    Surface as
                  </label>
                  <select
                    value={rules.daysOfCover.surface}
                    onChange={(e) => updateSurface('daysOfCover', e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:border-blue-500 font-semibold text-gray-800 dark:text-slate-200 cursor-pointer"
                  >
                    <option value="Act">Act</option>
                    <option value="Watch">Watch</option>
                    <option value="Ignore">Ignore</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Apply Button */}
        <div className="pt-4 border-t border-gray-100 dark:border-slate-800 mt-6 flex justify-end">
          <button
            onClick={() => setShowSuccessModal(true)}
            className="px-6 py-2.5 bg-[#1C1C1E] hover:bg-black text-white text-sm font-bold rounded-xl transition-colors"
          >
            Apply changes & rebuild feed
          </button>
        </div>
      </div>

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 z-[999999] flex items-center justify-center">
          <div className="fixed inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setShowSuccessModal(false)} />
          <div className="bg-white dark:bg-slate-900 rounded-3xl w-full max-w-md shadow-2xl relative z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-[#E5E0D8]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#1C1C1E] rounded-xl flex items-center justify-center shrink-0">
                  <i className="fa-solid fa-check text-white"></i>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100">Rules applied ✔</h2>
              </div>
            </div>

            <div className="p-6 pb-5 bg-gray-50/50 dark:bg-slate-800/20">
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest uppercase mb-3">What this does & why</p>
              <p className="text-[15px] text-gray-700 dark:text-slate-300 leading-relaxed">
                Your rule changes are live and the feed has been rebuilt — 12 insights now active.
              </p>
            </div>

            <div className="p-4 border-t border-[#E5E0D8] flex justify-end">
              <button
                onClick={() => setShowSuccessModal(false)}
                className="px-6 py-2 border border-[#E5E0D8] rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default RulesTab;
