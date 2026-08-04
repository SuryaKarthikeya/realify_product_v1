import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SaveBar = ({ isVisible, onSave, onDiscard }) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          exit={{ y: 100 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed bottom-0 left-0 right-0 z-50 px-8 pb-4 pointer-events-none"
        >
          <div className="max-w-5xl mx-auto bg-[#1e293b] dark:bg-[#0f172a] text-white rounded-2xl p-4 flex items-center justify-between shadow-2xl border border-slate-700 pointer-events-auto">
            <div className="flex items-center gap-3 ml-4">
              <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center">
                <i className="fa-solid fa-circle-exclamation text-amber-500 text-xs"></i>
              </div>
              <span className="text-sm font-bold tracking-wide">Unsaved changes</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={onDiscard}
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold transition-all border border-slate-600"
              >
                Discard
              </button>
              <button
                onClick={onSave}
                className="px-8 py-2.5 bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 dark:hover:bg-gray-500 rounded-xl text-xs font-bold transition-all shadow-lg shadow-black/10 dark:shadow-gray-700/20 active:scale-95"
              >
                Save
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SaveBar;
