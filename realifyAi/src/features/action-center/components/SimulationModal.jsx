import { motion } from 'framer-motion';
import React from 'react';
import Modal from '@/components/overlays/Modal';

const RISK_TEXT = { HIGH: 'text-red-600', MED: 'text-amber-600', LOW: 'text-green-600' };

const SimulationModal = ({ isOpen, onClose, action }) => {
  const stats = action?.miniStats || [];
  const metrics = action?.metrics || {};
  const [headStat, badgeStat, riskStat] = stats;
  const confidence = action?.confidenceScore ?? 0;
  const ease = action?.easeVal ?? 0;
  const complexity = action?.complexityVal ?? 0;
  const pct = (value, max) => `${Math.min(100, Math.round((value / max) * 100))}%`;

  return (
  <Modal isOpen={isOpen} onClose={onClose}>
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
      onClick={e => e.stopPropagation()}
    >
      {/* Modal Header */}
      <div className="p-6 border-b border-gray-200 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Action Simulation</h3>
            <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">Preview the impact of this action before implementing</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition"
          >
            <i className="fa-solid fa-xmark text-gray-600 dark:text-slate-400 text-xl"></i>
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Selected Action */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-200 dark:border-blue-800">
          <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-2">Selected Action</h4>
          <p className="text-gray-700 dark:text-slate-300">{action?.title || 'Select an action to simulate'}</p>
        </div>

        {/* States Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/10 dark:to-orange-900/10 p-5 rounded-xl border border-red-200 dark:border-red-900/30">
            <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <i className="fa-solid fa-chart-line text-red-600"></i>
              Current State
            </h5>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">{headStat?.label || 'Exposure'}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{headStat?.value || action?.exposureFormatted || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">{badgeStat?.label || 'Status'}</p>
                <span className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-lg text-xs font-medium">{badgeStat?.value || action?.tagCategory || '—'}</span>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">{riskStat?.label || 'Risk Level'}</p>
                <p className={`text-lg font-bold ${RISK_TEXT[action?.urgency] || 'text-red-600'}`}>{riskStat?.value || action?.urgency || '—'}</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/10 dark:to-emerald-900/10 p-5 rounded-xl border border-green-200 dark:border-green-900/30">
            <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <i className="fa-solid fa-arrow-trend-up text-green-600"></i>
              Projected State
            </h5>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">Recoverable Exposure</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{action?.exposureFormatted || '—'}</p>
                {metrics.exposureMo && (
                  <p className="text-xs text-green-600 font-medium">+{metrics.exposureMo} / month</p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">Status</p>
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg text-xs font-medium">Signal Cleared</span>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-slate-400">Risk Level</p>
                <p className="text-lg font-bold text-green-600">Low</p>
              </div>
            </div>
          </div>
        </div>

        {/* Impact Analysis */}
        <div className="mb-6">
          <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-3">Impact Analysis</h5>
          <div className="space-y-3">
            <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Signal Confidence</span>
                <span className="text-sm font-bold text-green-600">{confidence}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: pct(confidence, 100) }}></div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Implementation Complexity</span>
                <span className="text-sm font-bold text-green-600">{complexity}/5</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-red-600 h-2 rounded-full" style={{ width: pct(complexity, 5) }}></div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Execution Ease</span>
                <span className="text-sm font-bold text-green-600">{ease}/5</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: pct(ease, 5) }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Considerations */}
        <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/10 rounded-xl border border-yellow-200 dark:border-yellow-800">
          <h5 className="font-bold text-gray-900 dark:text-slate-100 mb-2 flex items-center gap-2">
            <i className="fa-solid fa-triangle-exclamation text-yellow-600"></i>
            Considerations
          </h5>
          <ul className="space-y-2 text-sm text-gray-700 dark:text-slate-300">
            <li className="flex items-start gap-2">
              <i className="fa-solid fa-circle text-yellow-600 text-[6px] mt-2 flex-shrink-0"></i>
              <span>Applies to {action?.skuCode || 'the selected SKU'} in the {action?.category || 'selected'} module.</span>
            </li>
            {metrics.velocity && metrics.threshold && (
              <li className="flex items-start gap-2">
                <i className="fa-solid fa-circle text-yellow-600 text-[6px] mt-2 flex-shrink-0"></i>
                <span>Currently {metrics.velocity} against a {metrics.threshold} threshold.</span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <i className="fa-solid fa-circle text-yellow-600 text-[6px] mt-2 flex-shrink-0"></i>
              <span>Owner {action?.assignee || '—'} · due {action?.due || '—'} · {action?.timeline || '—'}.</span>
            </li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button className="flex-1 px-6 py-3 bg-brand text-white rounded-xl font-medium hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition shadow-sm">
            <i className="fa-solid fa-play mr-2"></i>Execute Action
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-xl text-gray-700 dark:text-slate-300 font-medium transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </motion.div>
  </Modal>
  );
};

export default SimulationModal;
