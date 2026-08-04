import React, { useState } from 'react';
import Modal from '@/components/overlays/Modal';

const SHARE_OPTIONS = [
  {
    id: 'private',
    icon: 'fa-solid fa-lock',
    title: 'Keep private',
    subtitle: 'Only you have access',
  },
  {
    id: 'public',
    icon: 'fa-solid fa-globe',
    title: 'Create public link',
    subtitle: 'Anyone with the link can view',
  },
];

const makeShareId = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });

const ShareChatModal = ({ isOpen, onClose }) => {
  const [mode, setMode] = useState('private');
  const [linkCreated, setLinkCreated] = useState(false);
  const [copied, setCopied] = useState(false);
  const [shareId] = useState(makeShareId);

  if (!isOpen) return null;

  const shareUrl = `https://app.realify.ai/share/${shareId}`;

  const handleSelect = (id) => {
    setMode(id);
    setLinkCreated(id === 'public');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const shared = mode === 'public' && linkCreated;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 overflow-hidden"
      >
        <div className="flex items-start justify-between px-6 pt-5 pb-1">
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">
              {shared ? 'Chat shared' : 'Share chat'}
            </h3>
            <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">
              {shared
                ? 'Anyone with the link can view this chat.'
                : 'Only messages up to this point will be shared.'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg text-gray-400 dark:text-slate-500 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-700 dark:hover:text-slate-200 transition-colors"
          >
            <i className="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <div className="px-4 py-3 space-y-1">
          {SHARE_OPTIONS.map((opt) => {
            const selected = mode === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => handleSelect(opt.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-colors ${
                  selected
                    ? 'bg-gray-50 dark:bg-slate-800/70'
                    : 'hover:bg-gray-50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300">
                  <i className={`${opt.icon} text-sm`}></i>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{opt.title}</p>
                  <p className="text-xs text-gray-400 dark:text-slate-500">{opt.subtitle}</p>
                </div>
                {selected && (
                  <i className="fa-solid fa-check text-brand text-sm flex-shrink-0"></i>
                )}
              </button>
            );
          })}
        </div>

        {shared && (
          <div className="px-4 pb-3">
            <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 dark:bg-slate-800/70 border border-gray-200 dark:border-slate-700 rounded-xl">
              <span className="flex-1 min-w-0 truncate text-xs text-gray-500 dark:text-slate-400">
                {shareUrl}
              </span>
              <button
                onClick={handleCopy}
                className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg transition-all active:scale-95 ${
                  copied
                    ? 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                    : 'bg-white dark:bg-slate-700 text-gray-800 dark:text-slate-100 border border-gray-200 dark:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600'
                }`}
              >
                <i className={`fa-solid ${copied ? 'fa-check' : 'fa-copy'} text-[11px]`}></i>
                {copied ? 'Copied!' : 'Copy link'}
              </button>
            </div>
          </div>
        )}

        {mode === 'private' && (
          <div className="px-6 pb-3 pt-2">
            <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-relaxed">
              Don't share personal information or third-party content without permission, and see our{' '}
              <span className="font-semibold text-gray-600 dark:text-slate-300 underline underline-offset-2">
                Usage Policy
              </span>.
            </p>
          </div>
        )}

        <div className="flex justify-end px-6 py-2 border-t border-gray-100 dark:border-slate-800">
          <button
            onClick={onClose}
            className="px-5 py-[0.325rem] bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-800 dark:text-slate-100 text-sm font-bold rounded-xl transition-all active:scale-95"
          >
            Done
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ShareChatModal;
