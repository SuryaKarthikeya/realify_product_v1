import React, { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import HistoryItem from '@/features/history/components/HistoryItem';
import HistoryRightSidebar from '@/features/history/components/HistoryRightSidebar';
import { historyItems, quickFilters, modules, mostUsedSearches, MODULE_ITEM_IDS } from '@/features/history/data/historyData';

// Flat array used for filtering — defined once outside the component
const allItems = [
  ...historyItems.today.map(i => ({ ...i, section: 'Today' })),
  ...historyItems.yesterday.map(i => ({ ...i, section: 'Yesterday' })),
  ...historyItems.week.map(i => ({ ...i, section: 'Previous 7 Days' })),
];

const HistoryPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState('all');
  const [moduleFilter, setModuleFilter] = useState(location.state?.moduleFilter || null);

  const [prevModuleFilterState, setPrevModuleFilterState] = useState(location.state?.moduleFilter);
  if (location.state?.moduleFilter !== prevModuleFilterState) {
    setPrevModuleFilterState(location.state?.moduleFilter);
    const mFilter = location.state?.moduleFilter;
    if (mFilter !== undefined) setModuleFilter(mFilter || null);
  }

  // Bookmark state — initialised from data, updated in memory
  const [bookmarks, setBookmarks] = useState(
    () => new Set(allItems.filter(i => i.bookmarked).map(i => i.id))
  );

  const toggleBookmark = (id) => {
    setBookmarks(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Merge live bookmark state into items
  const augment = (item) => ({ ...item, bookmarked: bookmarks.has(item.id) });

  const todayItems = historyItems.today.map(augment);
  const yestItems  = historyItems.yesterday.map(augment);
  const weekItems  = historyItems.week.map(augment);

  // Items for flat filter views
  const filteredFlat = useMemo(() => {
    const augmented = allItems.map(i => ({ ...i, bookmarked: bookmarks.has(i.id) }));
    if (activeFilter === 'bookmarked') return augmented.filter(i => i.bookmarked);
    if (activeFilter === 'artifacts')  return augmented.filter(i => i.files || i.charts);
    return [];
  }, [bookmarks, activeFilter]);

  const isFiltered = activeFilter === 'bookmarked' || activeFilter === 'artifacts';

  // Items for module-filtered view
  const moduleItems = useMemo(() => {
    if (!moduleFilter) return [];
    const ids = MODULE_ITEM_IDS[moduleFilter] || [];
    return allItems.filter(i => ids.includes(i.id)).map(i => ({ ...i, bookmarked: bookmarks.has(i.id) }));
  }, [moduleFilter, bookmarks]);

  return (
    <DashboardLayout
      title="History"
      subtitle="Track your previous intelligence searches and AI analysis"
      showTabs={false}
      showAIPrompt={false}
    >
      {/* List view */}
      <div className="flex flex-col lg:flex-row gap-5 min-h-full">
          <div className="flex-1">

            {/* Search bar */}
            <div className="mb-5">
              <div className="relative">
                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                  <i className="fa-solid fa-magnifying-glass text-gray-400 text-sm"></i>
                </div>
                <input
                  type="text"
                  placeholder="Search chats..."
                  className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl text-sm text-gray-700 dark:text-slate-300 placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand dark:focus:ring-gray-500/20 dark:focus:border-gray-500 transition-all shadow-sm"
                />
              </div>
            </div>

            {moduleFilter ? (
              /* ── Module filtered view ── */
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setModuleFilter(null)}
                      className="w-7 h-7 flex items-center justify-center rounded-lg bg-gray-900 dark:bg-slate-200 text-white dark:text-slate-900 hover:bg-gray-700 dark:hover:bg-slate-300 transition-colors"
                    >
                      <i className="fa-solid fa-arrow-left text-[10px]" />
                    </button>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 capitalize">
                      {moduleFilter}
                    </h2>
                  </div>
                  <button
                    onClick={() => setModuleFilter(null)}
                    className="text-sm text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 transition-colors"
                  >
                    Clear filter
                  </button>
                </div>
                {moduleItems.length > 0 ? (
                  <div className="grid grid-cols-1 gap-3">
                    {moduleItems.map((item) => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onClick={() => navigate('/history/detail', { state: { chatId: item.id } })}
                        onBookmark={toggleBookmark}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No items in this module yet.</p>
                  </div>
                )}
              </div>
            ) : isFiltered ? (
              /* ── Flat filtered view (Bookmarked / Artifacts) ── */
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 capitalize">
                    {activeFilter === 'bookmarked' ? 'Bookmarked' : 'Artifacts'}
                  </h2>
                  <button
                    onClick={() => setActiveFilter('all')}
                    className="text-sm text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 transition-colors"
                  >
                    Clear filter
                  </button>
                </div>

                {filteredFlat.length > 0 ? (
                  <div className="grid grid-cols-1 gap-3">
                    {filteredFlat.map((item) => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onClick={() => navigate('/history/detail', { state: { chatId: item.id } })}
                        onBookmark={toggleBookmark}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                      <i className={`fa-solid ${activeFilter === 'artifacts' ? 'fa-file' : 'fa-bookmark'} text-gray-400 dark:text-slate-500 text-lg`}></i>
                    </div>
                    <p className="text-sm font-medium text-gray-500 dark:text-slate-400">
                      {activeFilter === 'artifacts' ? 'No artifacts available.' : 'No bookmarked chats yet.'}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">
                      {activeFilter === 'artifacts'
                        ? 'Chats with files or charts will appear here.'
                        : 'Click the bookmark icon on any chat to save it.'}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              /* ── Grouped view: Today / Yesterday / 7 Days ── */
              <>
                <div id="today-section" className="mb-5">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Today</h2>
                    <button className="text-sm text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 transition-colors">Clear all</button>
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    {todayItems.map((item) => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onClick={() => navigate('/history/detail', { state: { chatId: item.id } })}
                        onBookmark={toggleBookmark}
                      />
                    ))}
                  </div>
                </div>

                <div id="yesterday-section" className="mb-5">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Yesterday</h2>
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    {yestItems.map((item) => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onClick={() => navigate('/history/detail', { state: { chatId: item.id } })}
                        onBookmark={toggleBookmark}
                      />
                    ))}
                  </div>
                </div>

                <div id="week-section" className="mb-5">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Previous 7 Days</h2>
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    {weekItems.map((item) => (
                      <HistoryItem
                        key={item.id}
                        item={item}
                        onClick={() => navigate('/history/detail', { state: { chatId: item.id } })}
                        onBookmark={toggleBookmark}
                      />
                    ))}
                  </div>
                </div>

                <div className="flex justify-center py-5">
                  <button className="px-6 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-600 rounded-lg text-sm font-medium text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-all shadow-sm">
                    Load more history
                  </button>
                </div>
              </>
            )}
          </div>

          <HistoryRightSidebar
            quickFilters={quickFilters}
            modules={modules}
            mostUsedSearches={mostUsedSearches}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            bookmarkCount={bookmarks.size}
          />
        </div>
    </DashboardLayout>
  );
};

export default HistoryPage;
