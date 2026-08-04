import React from 'react';
import { formatCompactMoney, formatNumber } from '@/utils/formatters';

/**
 * Executive Brief Card — headline + description, plus 3 stat tiles, from
 * GET /api/workspace's `brief` object: { headline, detail, opportunity,
 * sku_count, at_risk }.
 */
const BriefCard = ({ data, isLoading = false }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [canExpand, setCanExpand] = React.useState(false);
  const headlineRef = React.useRef(null);
  const detailRef = React.useRef(null);

  // A fresh brief shouldn't inherit the previous one's expanded state.
  React.useLayoutEffect(() => {
    setExpanded(false);
  }, [data?.headline, data?.detail]);

  // Whether the clamped headline/detail are actually cutting text off,
  // measured against the real rendered layout rather than guessed from
  // character count — so "Show more" only appears when there's truly more
  // to see. Skipped while expanded, since the clamp (and therefore any
  // overflow to measure) is removed in that state.
  React.useLayoutEffect(() => {
    if (expanded) return;
    const isOverflowing = (el) => Boolean(el) && el.scrollHeight > el.clientHeight + 1;
    setCanExpand(isOverflowing(headlineRef.current) || isOverflowing(detailRef.current));
  }, [data?.headline, data?.detail, expanded]);

  if (isLoading || !data) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-gray-200/80 dark:border-slate-800 rounded-2xl p-6 animate-pulse">
        <div className="h-4 w-32 bg-gray-200 dark:bg-slate-800 rounded mb-4" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="h-14 bg-gray-200 dark:bg-slate-800 rounded-lg" />
          <div className="h-14 bg-gray-200 dark:bg-slate-800 rounded-lg" />
          <div className="h-14 bg-gray-200 dark:bg-slate-800 rounded-lg" />
        </div>
      </div>
    );
  }

  const tiles = [
    { key: 'opportunity', label: 'OPPORTUNITY', value: formatCompactMoney(data.opportunity), icon: 'fa-arrow-trend-up', bg: 'bg-[#E8F5E9] dark:bg-emerald-950/60', color: 'text-[#10B981]' },
    { key: 'sku_count', label: '# SKUs', value: formatNumber(data.sku_count ?? 0), icon: 'fa-cubes', bg: 'bg-[#E3F2FD] dark:bg-blue-950/60', color: 'text-[#3B82F6]' },
    { key: 'at_risk', label: 'AT RISK', value: formatCompactMoney(data.at_risk), icon: 'fa-triangle-exclamation', bg: 'bg-[#FFEBEE] dark:bg-rose-950/60', color: 'text-[#F43F5E]' },
  ];

  return (
    <div className="bg-[linear-gradient(60deg,#ffffff4D_0%,#eaecf04D_100%)] dark:bg-none dark:bg-slate-900 border border-[#e2e8f0] dark:border-slate-800 rounded-2xl p-4 sm:p-5 text-xs font-sans shadow-[inset_-1px_1px_16px_10px_#00000008] space-y-3.5">
      {/* ── Header Title ("THE BRIEF") ── */}
      <div>
        <span className="text-[11px] font-mono font-bold tracking-wider text-gray-400 dark:text-slate-500 uppercase">
          THE BRIEF
        </span>
      </div>

      {/* ── 3 Metrics Row ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 items-center">
        {tiles.map((tile) => (
          <div key={tile.key} className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-full ${tile.bg} ${tile.color} flex items-center justify-center text-xs flex-shrink-0`}>
              <i className={`fa-solid ${tile.icon}`} />
            </div>
            <div>
              <span className="text-[10px] font-mono font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider block leading-tight">
                {tile.label}
              </span>
              <strong className={`text-xl sm:text-[22px] font-bold ${tile.color} block leading-tight mt-0.5`}>
                {tile.value ?? '—'}
              </strong>
            </div>
          </div>
        ))}
      </div>

      {/* ── Headline + Description ──
          Both fields can run to a full paragraph (product names + numbers
          packed in), so they're clamped to 2 lines by default with a
          "Show more" toggle rather than left to blow up the card's height. */}
      {(data.headline || data.detail) && (
        <div className="space-y-1.5">
          {data.headline && (
            <p
              ref={headlineRef}
              className={`text-xs text-gray-500 dark:text-slate-400 leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}
            >
              {data.headline}
            </p>
          )}
          {data.detail && (
            <p
              ref={detailRef}
              className={`text-xs text-gray-500 dark:text-slate-400 leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}
            >
              {data.detail}
            </p>
          )}
          {canExpand && (
            <button
              type="button"
              onClick={() => setExpanded((cur) => !cur)}
              className="text-[11px] font-bold text-blue-600 dark:text-blue-400 hover:underline"
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default React.memo(BriefCard);
