import React from 'react';
import ModalPanel from '@/components/overlays/ModalPanel';

const DismissModal = ({ isOpen, onClose }) => {
  return (
    <ModalPanel 
      isOpen={isOpen} 
      onClose={onClose} 
      maxWidth="max-w-[500px]"
    >
      <div className="bg-white">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-slate-800">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 flex-shrink-0 bg-gray-900 rounded-xl flex items-center justify-center text-white">
              <i className="fa-solid fa-xmark text-lg" />
            </div>
            <div>
              <h2 className="text-[19px] font-bold text-gray-900 dark:text-white font-sans leading-snug">
                Dismissed.
              </h2>
              <p className="text-[12px] font-sans text-gray-400 mt-1">
                internal
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5">
          <p className="text-[10px] font-sans font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3">
            WHAT THIS DOES & WHY
          </p>
          <p className="text-[14px] text-gray-700 dark:text-slate-300 leading-relaxed mb-6">
            You dismissed this card. Realify removes it from the feed; the underlying condition is re-checked on the next data pull, so if it recurs it will surface again as a new card.
          </p>
          <div className="h-8 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-100 dark:border-slate-700 w-full mb-2"></div>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 dark:border-slate-800 flex justify-end">
          <button 
            onClick={onClose}
            className="px-5 py-2 bg-white border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-lg text-[13px] font-semibold transition-colors shadow-sm"
          >
            Close
          </button>
        </div>
      </div>
    </ModalPanel>
  );
};

export default DismissModal;
