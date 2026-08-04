import React, { useState, useRef } from 'react';
import useClickOutside from '@/hooks/useClickOutside';
import { usePinnedChatsStore } from '@/store/usePinnedChatsStore';

const OPTIONS = [
  { id: 'start-asin',   label: 'Start ASIN Tool',   icon: 'fa-solid fa-comment-medical' },
  { id: 'compare-asin',  label: 'Compare ASIN', icon: 'fa-solid fa-code-compare' },
  { id: 'pin',           label: 'Pin chat',          icon: 'fa-solid fa-thumbtack' },
];

const ChatOptionsMenu = ({ chatId }) => {
  const [open, setOpen] = useState(false);
  const pinned = usePinnedChatsStore(s => chatId != null && s.pinnedIds.includes(chatId));
  const togglePinned = usePinnedChatsStore(s => s.togglePinned);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  useClickOutside(triggerRef, open, () => setOpen(false), menuRef);

  const handleSelect = (id) => {
    if (id === 'pin' && chatId != null) togglePinned(chatId);
    setOpen(false);
  };

  return (
    <div ref={triggerRef} className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        title="More options"
        className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
      >
        <i className="fa-solid fa-ellipsis text-sm"></i>
      </button>

      {open && (
        <div
          ref={menuRef}
          className="absolute right-0 top-full mt-2 w-52 bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 z-[9999]"
        >
          {OPTIONS.map((opt) => {
            const isPin = opt.id === 'pin';
            const active = isPin && pinned;
            return (
              <button
                key={opt.id}
                onClick={() => handleSelect(opt.id)}
                className="w-full text-left px-3.5 py-2.5 text-sm flex items-center gap-2.5 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800/60 transition-colors"
              >
                <i className={`${opt.icon} text-xs w-3.5 text-center ${active ? 'text-brand' : 'text-gray-400 dark:text-slate-500'}`}></i>
                <span className={active ? 'font-semibold text-gray-900 dark:text-slate-100' : ''}>
                  {isPin && pinned ? 'Unpin chat' : opt.label}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ChatOptionsMenu;
