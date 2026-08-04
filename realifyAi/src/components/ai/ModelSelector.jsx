import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import useClickOutside from '@/hooks/useClickOutside';
import { useNavigate } from 'react-router-dom';

const MODELS = [
  { id: 'base', label: 'Starter', locked: false, icon: 'fa-solid fa-star', tagline: 'Great for everyday research' },
  { id: 'pro', label: 'Pro', locked: true, icon: 'fa-solid fa-bolt', tagline: 'Deeper insights & priority speed' },
  { id: 'pro_plus', label: 'Pro+', locked: true, icon: 'fa-solid fa-building', tagline: 'Advanced limits & dedicated support' },
  { id: 'custom', label: 'Custom', locked: true, icon: 'fa-solid fa-cogs', tagline: 'Tailored solutions for your business' },
];

const ModelSelector = ({ variant = 'default' }) => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(MODELS.find(m => !m.locked) || MODELS[0]);
  const [dropdownPos, setPos] = useState({ top: 0, bottom: 0, left: 0 });
  const triggerRef = useRef(null);
  const dropdownRef = useRef(null);
  const isTopbar = variant === 'topbar';
  const isCompact = variant === 'compact';

  useClickOutside(triggerRef, open, () => setOpen(false), dropdownRef);

  const handleToggle = () => {
    if (!open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const dropdownWidth = isTopbar ? 288 : 224;
      const safeLeft = Math.min(
        window.innerWidth - dropdownWidth - 8,
        Math.max(8, rect.left)
      );
      if (isTopbar) {
        setPos({ top: rect.bottom + 8, left: safeLeft });
      } else {
        setPos({ bottom: window.innerHeight - rect.top + 8, left: safeLeft });
      }
    }
    setOpen(v => !v);
  };

  const triggerClass = isTopbar
    ? 'flex items-center gap-1.5 text-[15px] font-normal text-gray-900 dark:text-slate-100 hover:bg-gray-100 dark:hover:bg-slate-800 px-0 md:px-2.5 py-1.5 rounded-lg transition-colors'
    : variant === 'compact'
      ? 'flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors whitespace-nowrap'
      : 'flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 rounded-full border border-transparent hover:border-gray-200 dark:hover:border-slate-600 transition-all';

  return (
    <div ref={triggerRef} className="relative">
      <button onClick={handleToggle} className={triggerClass}>
        {isTopbar ? (
          <>
            {/* Mobile Back Button */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                navigate(-1);
              }}
              className="md:hidden w-7 pl-0 pr-2 h-7 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800"
            >
              <i className="fa-solid fa-arrow-left text-sm"></i>
            </button>

            <span className="text-[13px]"> {selected.label} </span>
          </>
        ) : (
          <>
            <span className={`${isCompact ? 'hidden sm:inline' : ''} text-gray-400 dark:text-slate-500 font-medium`}>Model</span>
            <span className={`${isCompact ? 'hidden sm:inline' : ''} text-gray-300 dark:text-slate-600 mx-0.5`}>|</span>
            <span className="text-[13px] text-gray-700 dark:text-slate-200 font-medium">{selected.label}</span>
          </>
        )}
        <i className={`fa-solid fa-chevron-down ${isTopbar ? 'text-[10px] text-gray-400 dark:text-slate-500' : 'text-[8px]'}`}></i>
      </button>

      {open && isTopbar && ReactDOM.createPortal(
        <div
          ref={dropdownRef}
          style={{ position: 'fixed', top: dropdownPos.top, left: dropdownPos.left, zIndex: 99999 }}
          className="w-72 bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-slate-700 rounded-2xl shadow-2xl py-2"
        >
          {MODELS.map((model) => {
            const isSelected = selected.id === model.id && !model.locked;
            return (
              <div
                key={model.id}
                className="flex items-center gap-3 px-3 py-2.5 mx-1 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-800/60 transition-colors"
              >
                <div className="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300">
                  <i className={`${model.icon} text-xs`}></i>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-normal text-gray-900 dark:text-slate-100 leading-snug">
                    {model.label}
                  </p>
                  <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-snug truncate">
                    {model.tagline}
                  </p>
                </div>
                {model.locked ? (
                  <button
                    onClick={() => {
                      setOpen(false);
                      navigate('/settings?tab=subscription');
                    }}
                    className="flex-shrink-0 px-3 py-1.5 text-xs font-bold text-white bg-brand hover:bg-brand-hover dark:text-gray-900 rounded-lg transition-colors cursor-pointer"
                  >
                    Upgrade
                  </button>
                ) : (
                  <button
                    onClick={() => { setSelected(model); setOpen(false); }}
                    className="flex-shrink-0 w-6 h-6 flex items-center justify-center"
                  >
                    {isSelected && <i className="fa-solid fa-check text-gray-700 dark:text-slate-300 text-xs"></i>}
                  </button>
                )}
              </div>
            );
          })}
        </div>,
        document.body
      )}

      {open && !isTopbar && ReactDOM.createPortal(
        <div
          ref={dropdownRef}
          style={{ position: 'fixed', bottom: dropdownPos.bottom, left: dropdownPos.left, zIndex: 99999 }}
          className="w-[13rem] bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5"
        >
          {/* Section label */}
          <div className="px-4 pt-1.5 pb-2">
            <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest uppercase">Select Model</p>
          </div>

          {MODELS.map((model) => {
            const isSelected = selected.id === model.id && !model.locked;
            return (
              <div key={model.id} className="relative group">
                <button
                  onClick={() => {
                    if (!model.locked) {
                      setSelected(model);
                      setOpen(false);
                    } else {
                      setOpen(false);
                      navigate('/settings?tab=subscription');
                    }
                  }}
                  className={`w-full text-left px-4 py-1.5 text-sm flex items-center justify-between transition-colors ${isSelected
                    ? 'bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-slate-100'
                    : model.locked
                      ? 'text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-700/60 cursor-pointer'
                      : 'text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700/60 cursor-pointer'
                    }`}
                >
                  <span className={`font-medium ${isSelected ? 'text-gray-900 dark:text-slate-100' : ''}`}>
                    {model.label}
                  </span>

                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    {isSelected && (
                      <i className="fa-solid fa-check text-gray-700 dark:text-slate-300 text-[10px]"></i>
                    )}
                    {model.locked && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpen(false);
                          navigate('/settings?tab=subscription');
                        }}
                        className="px-2 py-0.5 text-[10px] font-bold text-white bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 rounded-md transition-colors shadow-2xs cursor-pointer"
                      >
                        Upgrade
                      </button>
                    )}
                  </div>
                </button>

                {/* Locked upgrade popover — slides in from left on row hover */}
                {model.locked && (
                  <div className="absolute right-full mr-2.5 top-1/2 -translate-y-1/2 w-52 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-xl p-3.5 z-[10000] pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                    <p className="text-xs font-semibold text-gray-900 dark:text-slate-100 mb-1.5 leading-snug">
                      Upgrade your plan
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-slate-400 leading-relaxed">
                      Unlock advanced features by upgrading your plan today.
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>,
        document.body
      )}
    </div>
  );
};

export default ModelSelector;
