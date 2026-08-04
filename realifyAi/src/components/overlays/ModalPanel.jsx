import React from 'react';
import Modal from '@/components/overlays/Modal';

/**
 * The standard modal shell: centred card, scrollable body, optional sticky
 * footer. Locks body scroll while open.
 *
 * Use this for ordinary dialogs. Reach for the bare `Modal` primitive only when
 * a call site needs a panel this shell can't express.
 */
const ModalPanel = ({ isOpen, onClose, maxWidth = 'max-w-[850px]', children, footer }) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    portal={false}
    lockScroll
    zIndex="z-[9999]"
    align="items-center"
    padding="p-4 sm:p-6"
    overflow=""
    scrim="bg-slate-900/40 backdrop-blur-sm transition-opacity"
    scrimMode="element"
  >
    <div
      className={`relative bg-white dark:bg-slate-900 w-full ${maxWidth} max-h-[95vh] rounded-[16px] shadow-2xl flex flex-col overflow-hidden`}
      onClick={e => e.stopPropagation()}
    >
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-6 relative">
        {children}
      </div>

      {/* Sticky Footer */}
      {footer && (
        <div className="border-t border-gray-100 dark:border-slate-800 p-5 bg-white dark:bg-slate-900 flex items-center justify-between shrink-0">
          {footer}
        </div>
      )}
    </div>
  </Modal>
);

export default ModalPanel;
