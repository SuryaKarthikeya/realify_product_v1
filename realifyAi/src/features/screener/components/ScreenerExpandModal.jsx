import React from 'react';
import { createPortal } from 'react-dom';

/**
 * The full-screen "expand" dialog every Research tab opens from its deep-dive
 * card. The chrome is shared; each tab supplies its own accent, heading and
 * body.
 *
 * Accent and close-icon classes are passed as complete class strings rather
 * than colour tokens, so each tab keeps exactly the markup it had before this
 * shell was extracted.
 *
 * Callers keep their own `{state && <ScreenerExpandModal …>}` guard so the body
 * is not evaluated while the dialog is closed.
 */
const ScreenerExpandModal = ({
  onClose,
  iconWrapClass,
  iconClass,
  title,
  closeIconClass = '',
  children,
}) =>
  createPortal(
    <div
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 w-full max-w-5xl max-h-[92vh] rounded-[1.5rem] shadow-2xl overflow-hidden flex flex-col border border-gray-100 dark:border-slate-800"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 ${iconWrapClass} rounded-lg flex items-center justify-center`}>
              <i className={`fa-solid ${iconClass}`}></i>
            </div>
            <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100">{title}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors"
          >
            <i className={`fa-solid fa-xmark${closeIconClass}`}></i>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );

export default ScreenerExpandModal;
