import { memo } from 'react';
import FAQItem from '@/features/hubs/components/FAQItem';
import { SUBSCRIPTION_META, PLUGIN_META_LINKS } from '@/features/hubs/data/hubsData';

// ─── Stars helper (local, not worth sharing globally) ─────────────────────────

const Stars = ({ count, total = 5, size = 'text-sm' }) =>
  Array.from({ length: total }, (_, i) => (
    <i
      key={i}
      className={`${
        i < count ? 'fa-solid fa-star text-yellow-400' : 'fa-regular fa-star text-gray-300'
      } ${size}`}
    />
  ));

// ─── Rating Bars ──────────────────────────────────────────────────────────────

const RatingBars = ({ bars }) => (
  <div className="space-y-2">
    {bars.map((pct, i) => (
      <div key={i} className="flex items-center gap-3">
        <span className="text-sm text-gray-600 dark:text-slate-400 w-8">{5 - i}★</span>
        <div className="flex-1 h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full bg-yellow-400" style={{ width: `${pct}%` }} />
        </div>
        <span className="text-sm text-gray-600 dark:text-slate-400 w-12 text-right">{pct}%</span>
      </div>
    ))}
  </div>
);

// ─── Review Card ──────────────────────────────────────────────────────────────

const ReviewCard = ({ review }) => (
  <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-5">
    <div className="flex items-start gap-4 mb-3">
      <img src={review.avatar} className="w-12 h-12 rounded-full object-cover flex-shrink-0" alt={review.name} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <h4 className="font-semibold text-gray-900 dark:text-white">{review.name}</h4>
          <span className="text-sm text-gray-500 dark:text-slate-400">{review.date}</span>
        </div>
        <div className="flex items-center gap-1 mb-1">
          <Stars count={review.stars} />
        </div>
      </div>
    </div>
    <p className="text-gray-700 dark:text-slate-300 leading-relaxed mb-3 text-sm">{review.text}</p>
    <div className="flex items-center gap-4 text-sm">
      <button className="text-gray-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 transition-colors flex items-center gap-1">
        <i className="fa-regular fa-thumbs-up" /> Helpful ({review.helpful})
      </button>
      <button className="text-gray-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 transition-colors">
        Reply
      </button>
    </div>
  </div>
);

// ─── Plugin Detail ────────────────────────────────────────────────────────────

const PluginDetail = memo(({ plugin, onBack, onCheckout, openFAQs, onToggleFAQ }) => {
  const starCount = Math.round(parseFloat(plugin.rating));

  return (
    <main className="p-4 sm:p-6 lg:px-8 lg:py-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors mb-6 font-medium text-sm"
      >
        <i className="fa-solid fa-arrow-left" /> Back to Hubs
      </button>

      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-sm">
        {/* Plugin Header */}
        <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex flex-col md:flex-row gap-5 items-start">
          <div
            className={`w-24 h-24 ${plugin.iconBg} ${plugin.iconColor} rounded-3xl flex items-center justify-center text-4xl shadow-inner flex-shrink-0`}
          >
            <i className={`fa-solid ${plugin.icon}`} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{plugin.title}</h1>
                <p className="text-gray-500 dark:text-slate-400 mt-1">
                  by {plugin.author}{' '}
                  <i className="fa-solid fa-circle-check text-blue-500 text-sm ml-1" />
                </p>
              </div>
              <div className="flex flex-col items-start md:items-end">
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {plugin.price}
                  <span className="text-sm text-gray-500 dark:text-slate-400 font-normal">
                    {plugin.priceSuffix ? `/${plugin.priceSuffix.replace('/', '')}` : ''}
                  </span>
                </span>
                <span className="text-xs text-green-600 font-medium bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded mt-1">
                  14-day free trial
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 mt-4 text-sm">
              <div className="flex items-center gap-1 text-gray-700 dark:text-slate-300">
                <Stars count={starCount} />
                <span className="font-medium ml-1">{plugin.rating}</span>
                <a href="#detail-reviews" className="text-blue-600 hover:underline ml-1">
                  ({plugin.detailReviews} reviews)
                </a>
              </div>
              <span className="w-1 h-1 bg-gray-300 rounded-full" />
              <span className="text-gray-600 dark:text-slate-400">
                <i className="fa-solid fa-download mr-1" />
                {plugin.detailInstalls} installs
              </span>
              <span className="w-1 h-1 bg-gray-300 rounded-full" />
              <span className="text-gray-600 dark:text-slate-400">
                <i className="fa-solid fa-tag mr-1" />
                {plugin.detailCategory}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row">
          {/* ── Left: Main Content ── */}
          <div className="flex-1 p-6 border-r border-gray-100 dark:border-slate-800 min-w-0">
            {/* Overview */}
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Overview</h2>
            <p className="text-gray-700 dark:text-slate-300 leading-relaxed mb-6">{plugin.overview}</p>

            {/* Screenshots */}
            {plugin.screenshots.length > 0 && (
              <div className="mb-5">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Screenshots</h3>
                <div className="flex gap-4 overflow-x-auto pb-4 snap-x [&::-webkit-scrollbar]:hidden">
                  {plugin.screenshots.map((src, i) => (
                    <div
                      key={i}
                      className="min-w-[400px] h-64 bg-slate-100 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 snap-center relative overflow-hidden group flex-shrink-0"
                    >
                      <img className="w-full h-full object-cover" src={src} alt={`Screenshot ${i + 1}`} />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <button className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-gray-900 shadow-lg">
                          <i className="fa-solid fa-expand" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Features */}
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Key Features</h3>
            <ul className="space-y-3 mb-5">
              {plugin.features.map((f, i) => (
                <li key={i} className="flex items-start gap-3">
                  <i className="fa-solid fa-check text-green-500 mt-1 flex-shrink-0" />
                  <div>
                    <strong className="text-gray-900 dark:text-white">{f.title}:</strong>{' '}
                    <span className="text-gray-600 dark:text-slate-400">{f.desc}</span>
                  </div>
                </li>
              ))}
            </ul>

            {/* Reviews Section */}
            <section id="detail-reviews" className="mb-5 pt-5 border-t border-gray-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Customer Reviews</h3>
                <button className="px-4 py-2 bg-brand text-white text-sm font-medium rounded-lg hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition">
                  Write a Review
                </button>
              </div>

              <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="text-5xl font-bold text-gray-900 dark:text-white mb-2">{plugin.rating}</div>
                    <div className="flex items-center gap-1 mb-2">
                      <Stars count={starCount} size="text-lg" />
                    </div>
                    <p className="text-sm text-gray-600 dark:text-slate-400">
                      Based on {plugin.detailReviews} reviews
                    </p>
                  </div>
                  <RatingBars bars={plugin.detailRatingBars} />
                </div>
              </div>

              <div className="space-y-4">
                {plugin.detailReviewsList.map((review, i) => (
                  <ReviewCard key={i} review={review} />
                ))}
              </div>

              <div className="mt-6 text-center">
                <button className="px-6 py-2.5 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition">
                  Load More Reviews
                </button>
              </div>
            </section>

            {/* Plugin-specific FAQs */}
            <section className="pt-5 border-t border-gray-100 dark:border-slate-800">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                Frequently Asked Questions
              </h3>
              <div className="space-y-3">
                {plugin.detailFaqs.map((faq, i) => (
                  <FAQItem
                    key={i}
                    faq={faq}
                    isOpen={!!openFAQs[i]}
                    onToggle={() => onToggleFAQ(i)}
                  />
                ))}
              </div>
            </section>
          </div>

          {/* ── Right: Sidebar ── */}
          <div className="w-full lg:w-80 p-6 bg-gray-50 dark:bg-slate-800/50 flex flex-col flex-shrink-0">
            {/* Subscription Card */}
            <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm mb-6">
              <h3 className="font-bold text-gray-900 dark:text-white mb-4">Subscription Details</h3>
              <div className="space-y-3 text-sm mb-6">
                {SUBSCRIPTION_META.map(({ label, value }) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-gray-600 dark:text-slate-400">{label}</span>
                    <span className="font-medium text-gray-900 dark:text-white">{value}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={onCheckout}
                className="w-full py-3 bg-brand text-white font-bold rounded-xl hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition shadow-sm mb-3"
              >
                Start 14-Day Free Trial
              </button>
              <p className="text-xs text-center text-gray-500 dark:text-slate-400">
                Then {plugin.priceModal}/month. Cancel anytime.
              </p>
            </div>

            {/* Plugin Meta */}
            <div className="space-y-4 text-sm">
              {PLUGIN_META_LINKS.map(({ icon, text }) => (
                <div key={icon} className="flex items-center gap-3 text-gray-600 dark:text-slate-400">
                  <i className={`fa-solid ${icon} w-5 text-center`} />
                  <span>{text}</span>
                </div>
              ))}
              <div className="flex items-center gap-3 text-gray-600 dark:text-slate-400">
                <i className="fa-solid fa-globe w-5 text-center" />
                <a href="#" className="text-blue-600 hover:underline">
                  Developer Website
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
});

PluginDetail.displayName = 'PluginDetail';

export default PluginDetail;
