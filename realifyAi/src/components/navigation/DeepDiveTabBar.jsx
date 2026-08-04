import React, { useRef, useState, useEffect } from 'react';

const DeepDiveTabBar = ({ children }) => {
  const ref = useRef(null);
  const [showLeft, setShowLeft] = useState(false);
  const [showRight, setShowRight] = useState(false);

  const update = (el) => {
    if (!el) return;
    setShowLeft(el.scrollLeft > 2);
    setShowRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 2);
  };

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    update(el);
    const ro = new ResizeObserver(() => update(el));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="relative border-b border-gray-200 dark:border-slate-800">
      <div
        ref={ref}
        className="flex items-center overflow-x-auto gap-0.5"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          paddingLeft: showLeft ? '2rem' : '1rem',
          paddingRight: showRight ? '2rem' : '1rem',
          paddingBottom: '1px',
        }}
        onScroll={e => update(e.currentTarget)}
      >
        {children}
      </div>
      {showLeft && (
        <button
          className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white dark:from-slate-900 to-transparent flex items-center justify-center z-10"
          onClick={() => ref.current?.scrollTo({ left: ref.current.scrollLeft - 120, behavior: 'smooth' })}
        >
          <span className="w-5 h-5 bg-white dark:bg-slate-800 rounded-full shadow-sm border border-gray-200 dark:border-slate-700 flex items-center justify-center">
            <i className="fa-solid fa-chevron-left text-[8px] text-gray-600 dark:text-slate-400"></i>
          </span>
        </button>
      )}
      {showRight && (
        <button
          className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white dark:from-slate-900 to-transparent flex items-center justify-center z-10"
          onClick={() => ref.current?.scrollTo({ left: ref.current.scrollLeft + 120, behavior: 'smooth' })}
        >
          <span className="w-5 h-5 bg-white dark:bg-slate-800 rounded-full shadow-sm border border-gray-200 dark:border-slate-700 flex items-center justify-center">
            <i className="fa-solid fa-chevron-right text-[8px] text-gray-600 dark:text-slate-400"></i>
          </span>
        </button>
      )}
    </div>
  );
};

export default DeepDiveTabBar;
