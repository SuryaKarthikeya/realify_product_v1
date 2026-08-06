import React from 'react';
import {
  useFloating,
  autoUpdate,
  offset,
  flip,
  shift,
  size,
  FloatingPortal,
} from '@floating-ui/react';
import { pillSurface } from '@/features/workspace/components/filterPillSurface';

const DateFilterSelect = ({ timeRange, setTimeRange, isOpen, onToggle, onClose, surface }) => {
  /**
   * Same floating setup as SkuFilterPopover.
   *
   * This panel is tall (two month grids), so anchoring it with `absolute
   * top-full` ran it off the bottom of the viewport whenever the trigger sat low
   * on the page — the fixed `max-h-[calc(100vh-7rem)]` ceiling could not help,
   * because it measures the viewport rather than the space below the button.
   *
   * `flip` opens it upwards when there is no room below, `shift` keeps it inside
   * the horizontal edges, and `size` caps its height to the space actually
   * available on whichever side it landed.
   *
   * `bottom-end` preserves the previous right-edge alignment.
   */
  const { refs, floatingStyles } = useFloating({
    open: isOpen,
    onOpenChange: (open) => {
      if (!open) onClose();
    },
    placement: 'bottom-end',
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(8),
      flip({ padding: 12 }),
      shift({ padding: 12 }),
      size({
        apply({ availableHeight, elements }) {
          /* No minimum floor here on purpose: a floor larger than the space
             `flip` actually found would push the panel back off the edge it was
             just moved away from. Better a short scrolling panel than a clipped
             one. */
          Object.assign(elements.floating.style, {
            maxHeight: `${Math.max(0, availableHeight - 16)}px`,
          });
        },
        padding: 12,
      }),
    ],
  });

  /* Destructured up here rather than read as `refs.setFloating` inside JSX:
     these are floating-ui's callback ref setters, but react-hooks/refs sees the
     member access on an object named `refs` and flags it as reading a ref
     during render. */
  const { setReference, setFloating } = refs;

  return (
    <div className="relative" data-filter-dropdown>
      <button
        ref={setReference}
        onClick={onToggle}
        className={`px-3 py-1.5 ${pillSurface(surface)} border rounded-xl text-xs font-semibold focus:outline-none cursor-pointer shadow-2xs flex items-center gap-1.5 transition-colors ${
          isOpen
            ? 'border-blue-600 text-blue-600'
            : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700'
        }`}
      >
        <i className="fa-regular fa-calendar" />
        {timeRange !== '30D' && (
          <span>
            {timeRange === '7D'
              ? 'Last 7 Days'
              : timeRange === '60D'
              ? 'Last 60 Days'
              : timeRange === 'ALL'
              ? 'All Time'
              : 'Last 30 Days'}
          </span>
        )}
        {timeRange === '30D' && <span>30D</span>}
        <i className="fa-solid fa-chevron-down text-[10px] opacity-80" />
      </button>

      {isOpen && (
        <FloatingPortal>
          <div
            ref={setFloating}
            style={{ ...floatingStyles, display: 'flex', flexDirection: 'column' }}
            className="z-50 outline-none"
            /* Portalled out of the trigger's wrapper, so it carries the marker
               the page's outside-click handler looks for via closest(). */
            data-filter-dropdown
          >
        <div className="w-[300px] sm:w-[480px] bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-gray-100 dark:border-slate-800 p-4 min-h-0 overflow-y-auto custom-scrollbar animate-in fade-in zoom-in-95 duration-200">
          <div className="flex justify-between items-center mb-2.5">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Date Range</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300">
              <i className="fa-solid fa-xmark text-sm" />
            </button>
          </div>

          {/* Quick Filters */}
          <div className="mb-3">
            <h4 className="text-[11px] font-semibold text-gray-400 dark:text-slate-500 mb-2">Quick Filters</h4>
            <div className="flex gap-2">
              <button
                onClick={() => setTimeRange('7D')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                  timeRange === '7D'
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-sm'
                    : 'border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                Last 7 Days
              </button>
              <button
                onClick={() => setTimeRange('30D')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                  timeRange === '30D'
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-sm'
                    : 'border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                Last 30 Days
              </button>
              <button
                onClick={() => setTimeRange('60D')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                  timeRange === '60D'
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-sm'
                    : 'border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                Last 60 Days
              </button>
              <button
                onClick={() => setTimeRange('ALL')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                  timeRange === 'ALL'
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-sm'
                    : 'border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                All Time
              </button>
            </div>
          </div>

          {/* Custom Range Inputs */}
          <div className="mb-4">
            <h4 className="text-[11px] font-semibold text-gray-400 dark:text-slate-500 mb-2">Custom</h4>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 border border-gray-200 dark:border-slate-700 rounded-xl px-3 py-2.5 bg-gray-50/50 dark:bg-slate-800/50">
                <div className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">START DATE</div>
                <div className="flex justify-between items-center text-[13px] font-semibold text-gray-900 dark:text-white">
                  4 May 2026 <i className="fa-regular fa-calendar text-gray-400" />
                </div>
              </div>
              <div className="flex-1 border border-gray-200 dark:border-slate-700 rounded-xl px-3 py-2.5 bg-gray-50/50 dark:bg-slate-800/50">
                <div className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">END DATE</div>
                <div className="flex justify-between items-center text-[13px] font-semibold text-gray-900 dark:text-white">
                  2 Jun 2026 <i className="fa-regular fa-calendar text-gray-400" />
                </div>
              </div>
            </div>
          </div>

          {/* Mock Calendar Grid */}
          <div className="hidden sm:flex gap-6 mb-4">
            {/* May Calendar */}
            <div className="flex-1">
              <div className="flex justify-between items-center mb-2.5 px-1">
                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300"><i className="fa-solid fa-chevron-left text-xs" /></button>
                <span className="text-[13px] font-bold text-gray-900 dark:text-white">May 2026</span>
                <div className="w-3"></div>
              </div>
              <div className="grid grid-cols-7 text-center text-[11px] font-semibold text-gray-400 mb-1">
                <div>Su</div><div>Mo</div><div>Tu</div><div>We</div><div>Th</div><div>Fr</div><div>Sa</div>
              </div>
              <div className="grid grid-cols-7 text-center text-[12.5px] font-medium text-gray-700 dark:text-slate-300 [&>div]:h-6 [&>div]:flex [&>div]:items-center [&>div]:justify-center">
                <div className="text-gray-300 dark:text-slate-600">26</div><div className="text-gray-300 dark:text-slate-600">27</div><div className="text-gray-300 dark:text-slate-600">28</div><div className="text-gray-300 dark:text-slate-600">29</div><div className="text-gray-300 dark:text-slate-600">30</div><div>1</div><div>2</div>
                <div>3</div><div className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg mx-auto w-6 h-6 flex items-center justify-center font-bold shadow-sm">4</div><div>5</div><div>6</div><div>7</div><div>8</div><div>9</div>
                <div>10</div><div>11</div><div>12</div><div>13</div><div>14</div><div>15</div><div>16</div>
                <div>17</div><div>18</div><div>19</div><div>20</div><div>21</div><div>22</div><div>23</div>
                <div>24</div><div>25</div><div>26</div><div>27</div><div>28</div><div>29</div><div>30</div>
                <div>31</div>
              </div>
            </div>
            
            {/* June Calendar */}
            <div className="flex-1">
              <div className="flex justify-between items-center mb-2.5 px-1">
                <div className="w-3"></div>
                <span className="text-[13px] font-bold text-gray-900 dark:text-white">Jun 2026</span>
                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300"><i className="fa-solid fa-chevron-right text-xs" /></button>
              </div>
              <div className="grid grid-cols-7 text-center text-[11px] font-semibold text-gray-400 mb-1">
                <div>Su</div><div>Mo</div><div>Tu</div><div>We</div><div>Th</div><div>Fr</div><div>Sa</div>
              </div>
              <div className="grid grid-cols-7 text-center text-[12.5px] font-medium text-gray-700 dark:text-slate-300 [&>div]:h-6 [&>div]:flex [&>div]:items-center [&>div]:justify-center">
                <div className="text-gray-300 dark:text-slate-600">31</div><div>1</div><div className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg mx-auto w-6 h-6 flex items-center justify-center font-bold shadow-sm">2</div><div>3</div><div>4</div><div>5</div><div>6</div>
                <div>7</div><div>8</div><div>9</div><div>10</div><div>11</div><div>12</div><div>13</div>
                <div>14</div><div>15</div><div>16</div><div>17</div><div>18</div><div>19</div><div>20</div>
                <div>21</div><div>22</div><div>23</div><div>24</div><div>25</div><div>26</div><div>27</div>
                <div>28</div><div>29</div><div>30</div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-3 border-t border-gray-100 dark:border-slate-800">
            <button onClick={onClose} className="px-5 py-1.5 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 rounded-xl text-xs font-bold hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors">
              Cancel
            </button>
            <button onClick={onClose} className="px-5 py-1.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl text-xs font-bold shadow-md transition-colors hover:bg-gray-800 dark:hover:bg-gray-100">
              Apply
            </button>
          </div>
        </div>
          </div>
        </FloatingPortal>
      )}
    </div>
  );
};

export default DateFilterSelect;
