import React from 'react';
import ModalPanel from '@/components/overlays/ModalPanel';

const CaseReportModal = ({ isOpen, onClose }) => {
  return (
    <ModalPanel 
      isOpen={isOpen} 
      onClose={onClose} 
      maxWidth="max-w-[550px]"
    >
      <div className="bg-white">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-slate-800">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 flex-shrink-0 bg-gray-900 rounded-xl flex items-center justify-center text-white">
              <i className="fa-solid fa-clipboard text-lg" />
            </div>
            <div>
              <h2 className="text-[19px] font-bold text-gray-900 dark:text-white font-sans leading-snug">
                Case / report
              </h2>
              <p className="text-[12px] font-sans text-gray-400 mt-1">
                draft + deep-link · logged #40
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5">
          <p className="text-[10px] font-sans font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3">
            WHAT THIS DOES & WHY
          </p>
          <p className="text-[14px] text-gray-700 dark:text-slate-300 leading-relaxed mb-6">
            Realify queried your settled orders, found those where the actual deposit fell short of the expected (gross — referral — FBA fees), summed the recoverable gap, and drafted a case body with the real order IDs. Realify does NOT file the case — you open the Case Log and paste. Every figure here comes from your own order/settlement data.
          </p>
          
          <div className="p-4 bg-[#faf9f7] dark:bg-slate-800 rounded-lg border border-[#e5e1d8] dark:border-slate-700 mb-6 shadow-sm">
            <p className="text-[13px] text-gray-800 dark:text-slate-300 leading-relaxed">
              Subject: Settlement reconciliation Affected ASIN: multiple. No settled orders currently show a deposit variance above threshold. Re-run after the next settlement cycle.
            </p>
          </div>

          <p className="text-[10px] font-sans font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3">
            DATA USED
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-white border border-[#e5e1d8] rounded text-[11px] font-sans text-gray-500">
              order deposits (OWN settlement)
            </span>
            <span className="px-3 py-1 bg-white border border-[#e5e1d8] rounded text-[11px] font-sans text-gray-500">
              expected fees (OWN)
            </span>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 dark:border-slate-800 flex items-center justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-5 py-2.5 bg-white border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-lg text-[13px] font-semibold transition-colors shadow-sm"
          >
            Close
          </button>
          <button 
            onClick={onClose}
            className="px-5 py-2.5 bg-[#1a1a1a] hover:bg-black text-white rounded-lg text-[13px] font-bold transition-colors shadow-sm flex items-center gap-2"
          >
            Open Case Log <i className="fa-solid fa-arrow-up-right-from-square text-[10px]" />
          </button>
        </div>
      </div>
    </ModalPanel>
  );
};

export default CaseReportModal;
