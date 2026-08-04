import React, { useState } from 'react';
import ModalPanel from '@/components/overlays/ModalPanel';
import { formatCompactMoney } from '@/utils/formatters';

/**
 * ConfirmActionModal — Confirm-and-Apply Flow for "Take Action" / "Apply Plan"
 */
const ConfirmActionModal = ({ isOpen, onClose, signal, onConfirm }) => {
  const [isApplying, setIsApplying] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!isOpen || !signal) return null;

  const skuCode = signal.skuCode || signal.category || 'GLOBAL-SKU';
  const headline = signal.headline || signal.skuCode || 'Selected AI Signal Action';
  const formattedExposure = typeof signal.exposure === 'number'
    ? formatCompactMoney(signal.exposure)
    : (signal.exposureFormatted || signal.monthlyRevenue || '$45,000');

  const handleApply = () => {
    setIsApplying(true);
    setTimeout(() => {
      setIsApplying(false);
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        if (onConfirm) onConfirm(signal);
        onClose();
      }, 1000);
    }, 600);
  };

  return (
    <ModalPanel
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="max-w-md"
    >
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 font-sans space-y-4">
        
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-gray-100 dark:border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-mono font-bold tracking-wider text-blue-600 dark:text-blue-400 uppercase bg-blue-50 dark:bg-blue-900/40 px-2 py-0.5 rounded">
              CONFIRM &amp; APPLY ACTION
            </span>
            <h3 className="text-[15px] font-bold text-gray-900 dark:text-white mt-1">
              {skuCode} — Action Execution
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400"
          >
            <i className="fa-solid fa-xmark text-sm" />
          </button>
        </div>

        {/* Content */}
        {isSuccess ? (
          <div className="py-5 text-center space-y-2">
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto text-xl font-bold animate-bounce">
              ✓
            </div>
            <h4 className="text-[16px] font-bold text-gray-900 dark:text-white">Action Applied Successfully</h4>
            <p className="text-[12px] text-gray-500 dark:text-slate-400">
              Intervention rules deployed to channel management engine.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-2 bg-gray-50 dark:bg-slate-800/50 p-3 rounded-lg border border-gray-200/70 dark:border-slate-700">
              <p className="text-[12.5px] font-medium text-gray-800 dark:text-slate-200">
                {headline}
              </p>
              <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-gray-500 dark:text-slate-400 border-t border-gray-200/50 dark:border-slate-700/50">
                <span>Revenue Impact at Risk:</span>
                <strong className="text-emerald-600 dark:text-emerald-400 font-bold">{formattedExposure}</strong>
              </div>
            </div>

            <div className="text-[12px] text-gray-600 dark:text-slate-300 leading-relaxed bg-blue-50/50 dark:bg-blue-950/30 p-3 rounded-lg border border-blue-100 dark:border-blue-900/30">
              ⚡ Applying this action will update channel pricing or bidding rules immediately. Monitoring tripwires will track performance over Day 7, Day 15, and Day 30 checkpoints.
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-gray-100 dark:border-slate-800">
              <button
                onClick={onClose}
                disabled={isApplying}
                className="px-4 py-2 border border-gray-300 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-[12px] font-semibold hover:bg-gray-50 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={isApplying}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[12px] font-bold shadow-2xs transition-colors flex items-center gap-2"
              >
                {isApplying ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Applying...</span>
                  </>
                ) : (
                  <span>Confirm &amp; Deploy</span>
                )}
              </button>
            </div>
          </>
        )}

      </div>
    </ModalPanel>
  );
};

export default ConfirmActionModal;
