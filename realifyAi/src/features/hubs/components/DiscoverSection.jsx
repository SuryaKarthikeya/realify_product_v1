import { memo } from 'react';
import PluginCard from '@/features/hubs/components/PluginCard';
import FAQItem from '@/features/hubs/components/FAQItem';
import { PLUGINS_LIST, MAIN_FAQS, MAIN_REVIEWS, RATING_BARS } from '@/features/hubs/data/hubsData';
import SelectInput from '@/components/ui/SelectInput';

const DISCOVER_SELECT_CLASS = 'px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm font-medium text-gray-700 dark:text-slate-300 shadow-sm outline-none cursor-pointer';

// ─── Featured Banner ──────────────────────────────────────────────────────────

const FeaturedBanner = memo(({ onSelect }) => (
  <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 text-white mb-5 shadow-lg relative overflow-hidden">
    <div className="relative z-10 max-w-2xl">
      <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs font-bold tracking-wider mb-4 uppercase">
        Featured Plugin
      </span>
      <h1 className="text-3xl font-bold mb-3">Agentic Mailbox AI</h1>
      <p className="text-blue-100 mb-6 text-lg">
        Connect your email accounts and let AI manage, organize, and auto-respond to your messages with
        intelligent actions.
      </p>
      <div className="flex items-center gap-4">
        <button
          onClick={() => onSelect('agentic')}
          className="px-6 py-3 bg-white text-blue-700 font-bold rounded-xl hover:bg-blue-50 transition shadow-sm"
        >
          View Details
        </button>
        <span className="text-sm font-medium flex items-center gap-1">
          <i className="fa-solid fa-star text-yellow-400" /> 4.9 (2.4k reviews)
        </span>
      </div>
    </div>
    <div className="absolute right-0 top-0 h-full w-1/3 opacity-20 pointer-events-none">
      <i className="fa-solid fa-envelope-open-text text-9xl absolute -right-4 top-1/2 -translate-y-1/2" />
    </div>
  </div>
));

FeaturedBanner.displayName = 'FeaturedBanner';

// ─── Filters + View Toggle ────────────────────────────────────────────────────

const FilterBar = memo(({ viewMode, onViewMode }) => (
  <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
    <div className="flex gap-2 flex-wrap">
      <SelectInput className={DISCOVER_SELECT_CLASS}>
        <option>All Categories</option>
        <option>Marketing</option>
        <option>Finance</option>
        <option>Productivity</option>
        <option>Analytics</option>
      </SelectInput>
      <SelectInput className={DISCOVER_SELECT_CLASS}>
        <option>Sort by: Popular</option>
        <option>Newest</option>
        <option>Price: Low to High</option>
        <option>Highest Rated</option>
      </SelectInput>
    </div>

    <div className="flex items-center bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl p-1 shadow-sm">
      {['list', 'grid'].map((mode) => (
        <button
          key={mode}
          onClick={() => onViewMode(mode)}
          className={`p-2 rounded-lg transition-colors ${
            viewMode === mode
              ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          <i className={`fa-solid ${mode === 'grid' ? 'fa-border-all' : 'fa-list'}`} />
        </button>
      ))}
    </div>
  </div>
));

FilterBar.displayName = 'FilterBar';

// ─── Pagination ───────────────────────────────────────────────────────────────

const Pagination = memo(() => (
  <div className="flex items-center justify-center gap-2 mt-5">
    <button
      disabled
      className="w-10 h-10 flex items-center justify-center rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-400 hover:bg-gray-50 transition-colors disabled:opacity-50"
    >
      <i className="fa-solid fa-chevron-left text-sm" />
    </button>

    {[1, 2, 3, 4].map((n) => (
      <button
        key={n}
        className={`w-10 h-10 flex items-center justify-center rounded-lg border font-medium transition-colors ${
          n === 1
            ? 'border-blue-500 bg-blue-500 text-white font-semibold'
            : 'border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
        }`}
      >
        {n}
      </button>
    ))}

    <span className="text-gray-400 px-2">...</span>

    <button className="w-10 h-10 flex items-center justify-center rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium transition-colors">
      12
    </button>
    <button className="w-10 h-10 flex items-center justify-center rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-400 hover:bg-gray-50 transition-colors">
      <i className="fa-solid fa-chevron-right text-sm" />
    </button>
  </div>
));

Pagination.displayName = 'Pagination';

// ─── Reviews Panel ────────────────────────────────────────────────────────────

const ReviewsPanel = memo(() => (
  <div className="space-y-6">
    {/* Rating Overview */}
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-6 border border-blue-100 dark:border-blue-900/40">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">Customer Reviews</h3>
        <div className="flex items-center gap-2">
          <i className="fa-solid fa-star text-yellow-400 text-lg" />
          <span className="text-2xl font-bold text-gray-900 dark:text-white">4.8</span>
        </div>
      </div>
      <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
        Based on 8,537 verified reviews across all plugins
      </p>
      <div className="space-y-2">
        {RATING_BARS.map(({ label, pct }) => (
          <div key={label} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 dark:text-slate-400 w-8">{label}</span>
            <div className="flex-1 h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-yellow-400" style={{ width: `${pct}%` }} />
            </div>
            <span className="text-sm text-gray-600 dark:text-slate-400 w-12 text-right">{pct}%</span>
          </div>
        ))}
      </div>
    </div>

    {/* Individual Reviews */}
    <div className="space-y-4">
      {MAIN_REVIEWS.map((r, i) => (
        <div key={i} className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
          <div className="flex items-start gap-4 mb-3">
            <img src={r.avatar} className="w-12 h-12 rounded-full object-cover flex-shrink-0" alt={r.name} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
                <h4 className="font-semibold text-gray-900 dark:text-white">{r.name}</h4>
                <span className="text-sm text-gray-500 dark:text-slate-400">{r.date}</span>
              </div>
              <div className="flex items-center gap-0.5 mb-1">
                {Array.from({ length: 5 }, (_, idx) => (
                  <i
                    key={idx}
                    className={`text-sm ${
                      idx < r.stars ? 'fa-solid fa-star text-yellow-400' : 'fa-regular fa-star text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <p className="text-sm text-gray-500 dark:text-slate-400">{r.plugin}</p>
            </div>
          </div>
          <p className="text-gray-700 dark:text-slate-300 leading-relaxed mb-3 text-sm">{r.text}</p>
          <button className="text-gray-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 transition-colors flex items-center gap-1 text-sm">
            <i className="fa-regular fa-thumbs-up" /> Helpful ({r.helpful})
          </button>
        </div>
      ))}

      <div className="text-center mt-6">
        <button className="px-6 py-2.5 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition text-sm">
          View All Reviews
        </button>
      </div>
    </div>
  </div>
));

ReviewsPanel.displayName = 'ReviewsPanel';

// ─── Discover Section ─────────────────────────────────────────────────────────

const DiscoverSection = ({ viewMode, onViewMode, onSelect, openFAQs, onToggleFAQ }) => (
  <main className="p-4 sm:p-6 lg:px-8 lg:py-6">
    <FeaturedBanner onSelect={onSelect} />
    <FilterBar viewMode={viewMode} onViewMode={onViewMode} />

    {/* Plugin Cards */}
    {viewMode === 'grid' ? (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {PLUGINS_LIST.map((plugin) => (
          <PluginCard key={plugin.id} plugin={plugin} variant="grid" onSelect={onSelect} />
        ))}
      </div>
    ) : (
      <div className="flex flex-col gap-4">
        {PLUGINS_LIST.map((plugin) => (
          <PluginCard key={plugin.id} plugin={plugin} variant="list" onSelect={onSelect} />
        ))}
      </div>
    )}

    <Pagination />

    {/* FAQ + Reviews */}
    <section className="mt-8 mb-5">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
          Frequently Asked Questions
        </h2>
        <p className="text-gray-600 dark:text-slate-400">
          Find answers to common questions about our Hubs Marketplace
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="space-y-4">
          {MAIN_FAQS.map((faq, i) => (
            <FAQItem
              key={i}
              faq={faq}
              isOpen={!!openFAQs[i]}
              onToggle={() => onToggleFAQ(i)}
            />
          ))}
        </div>
        <ReviewsPanel />
      </div>
    </section>
  </main>
);

export default DiscoverSection;
