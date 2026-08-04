import { memo } from 'react';

// ─── Shared Star Rating ───────────────────────────────────────────────────────

const Stars = ({ count, total = 5, size = 'text-sm' }) =>
  Array.from({ length: total }, (_, i) => (
    <i
      key={i}
      className={`${
        i < count ? 'fa-solid fa-star text-yellow-400' : 'fa-regular fa-star text-gray-300'
      } ${size}`}
    />
  ));

// ─── Grid Card ────────────────────────────────────────────────────────────────

const GridCard = ({ plugin, onSelect }) => (
  <div
    onClick={() => onSelect(plugin.id)}
    className={`bg-white dark:bg-slate-900 border rounded-2xl p-5 shadow-sm cursor-pointer flex flex-col h-full transition-all duration-300 hover:-translate-y-1 hover:shadow-xl relative ${
      plugin.featured
        ? 'border-blue-400 dark:border-blue-500 ring-1 ring-blue-400 dark:ring-blue-500'
        : 'border-gray-200 dark:border-slate-700'
    }`}
  >
    {plugin.featured && (
      <div className="absolute top-0 right-0 bg-blue-500 text-white text-[10px] font-bold px-2 py-1 rounded-bl-lg rounded-tr-xl uppercase tracking-wider">
        Featured
      </div>
    )}

    <div className={`flex items-start justify-between mb-4 ${plugin.featured ? 'mt-2' : ''}`}>
      <div
        className={`w-14 h-14 ${plugin.iconBg} ${plugin.iconColor} rounded-2xl flex items-center justify-center text-2xl shadow-inner`}
      >
        <i className={`fa-solid ${plugin.icon}`} />
      </div>
      <span className={`px-2.5 py-1 ${plugin.priceBadge} text-xs font-bold rounded-lg`}>
        {plugin.price}{plugin.priceSuffix}
      </span>
    </div>

    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">{plugin.title}</h3>
    <p className="text-sm text-gray-500 dark:text-slate-400 mb-2">by {plugin.author}</p>
    <p className="text-sm text-gray-600 dark:text-slate-400 mb-4 flex-1">{plugin.description}</p>

    <div className="flex items-center justify-between mt-auto pt-4 border-t border-gray-100 dark:border-slate-700">
      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-slate-400">
        <i className="fa-solid fa-star text-yellow-400" />
        <span className="font-medium dark:text-slate-300">{plugin.rating}</span>
        <span className="text-gray-400">({plugin.reviewsBadge})</span>
      </div>
      <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-slate-500">
        <i className="fa-solid fa-download" /> {plugin.installsBadge}
      </div>
    </div>
  </div>
);

// ─── List Card ────────────────────────────────────────────────────────────────

const ListCard = ({ plugin, onSelect }) => (
  <div
    onClick={() => onSelect(plugin.id)}
    className={`bg-white dark:bg-slate-900 border rounded-2xl p-4 shadow-sm cursor-pointer flex items-center gap-6 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl relative overflow-hidden ${
      plugin.featured
        ? 'border-blue-200 dark:border-blue-700'
        : 'border-gray-200 dark:border-slate-700'
    }`}
  >
    {plugin.featured && <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500" />}

    <div
      className={`w-16 h-16 ${plugin.iconBg} ${plugin.iconColor} rounded-2xl flex items-center justify-center text-2xl shadow-inner flex-shrink-0 ${
        plugin.featured ? 'ml-2' : ''
      }`}
    >
      <i className={`fa-solid ${plugin.icon}`} />
    </div>

    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-3 mb-1 flex-wrap">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{plugin.title}</h3>
        <span className="text-sm text-gray-500 dark:text-slate-400">by {plugin.author}</span>
        {plugin.featured && (
          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 text-[10px] font-bold rounded uppercase">
            Featured
          </span>
        )}
      </div>
      <p className="text-sm text-gray-600 dark:text-slate-400 line-clamp-1">{plugin.description}</p>
      <div className="flex items-center gap-4 mt-2 flex-wrap">
        <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-slate-400">
          <Stars count={Math.round(parseFloat(plugin.rating))} />
          <span className="font-medium dark:text-slate-300 ml-1">{plugin.rating}</span>
          <span className="text-gray-400 ml-0.5">({plugin.reviewsBadge})</span>
        </div>
        <div className="text-sm text-gray-500 dark:text-slate-500 border-l border-gray-300 dark:border-slate-600 pl-4">
          {plugin.categoryBadge}
        </div>
      </div>
    </div>

    <div className="flex flex-col items-end gap-3 flex-shrink-0">
      <span className={`px-3 py-1 ${plugin.priceBadge} text-sm font-bold rounded-lg`}>
        {plugin.price}{plugin.priceSuffix}
      </span>
      <button
        className={`px-4 py-2 font-medium rounded-lg transition text-sm ${
          plugin.featured
            ? 'bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500'
            : 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50'
        }`}
      >
        View Details
      </button>
    </div>
  </div>
);

// ─── Unified Export ───────────────────────────────────────────────────────────

const PluginCard = memo(({ plugin, variant = 'grid', onSelect }) =>
  variant === 'list' ? (
    <ListCard plugin={plugin} onSelect={onSelect} />
  ) : (
    <GridCard plugin={plugin} onSelect={onSelect} />
  ),
);

PluginCard.displayName = 'PluginCard';

export default PluginCard;
