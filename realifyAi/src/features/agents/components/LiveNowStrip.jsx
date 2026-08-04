import React from 'react';

const TONES = {
  indigo: { stroke: '#6366f1' },
  emerald: { stroke: '#10b981' },
  amber: { stroke: '#f59e0b' },
  violet: { stroke: '#a855f7' },
};

/**
 * Inline sparkline — a plain SVG polyline scaled to the series, so it needs no
 * charting library and stays crisp at this size.
 *
 * `preserveAspectRatio="none"` lets the 100x28 viewBox stretch to whatever width
 * the card ends up at while the stroke stays a constant screen width via
 * `vector-effect`.
 */
const Sparkline = ({ series, stroke }) => {
  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const points = series
    .map((v, i) => {
      const x = (i / (series.length - 1)) * 100;
      const y = 26 - ((v - min) / span) * 24;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return (
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" className="w-full h-7" aria-hidden="true">
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

/**
 * The "Live Now" row — one card per specialist with work in flight.
 *
 * Rendered only when at least one agent is live; otherwise the page shows the
 * five-step hire rail in this slot instead.
 */
const LiveNowStrip = ({ agents }) => {
  const trackRef = React.useRef(null);

  /* Arrows nudge the track by one card rather than a fixed pixel count, so they
     stay correct as the card width changes across breakpoints. */
  const nudge = (dir) => {
    const track = trackRef.current;
    if (!track) return;
    const step = track.firstElementChild?.getBoundingClientRect().width || 260;
    track.scrollBy({ left: dir * (step + 16), behavior: 'smooth' });
  };

  return (
  <div>
    <div className="flex items-center justify-between gap-3 mb-2.5">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        <h2 className="text-[13px] font-bold text-gray-900 dark:text-white">Live Now</h2>
      </div>

      {/* Only worth showing once the row can actually overflow */}
      {agents.length > 4 && (
        <div className="flex items-center gap-1.5">
          {[-1, 1].map((dir) => (
            <button
              key={dir}
              onClick={() => nudge(dir)}
              aria-label={dir < 0 ? 'Scroll left' : 'Scroll right'}
              className="w-6 h-6 rounded-md border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center"
            >
              <i className={`fa-solid fa-chevron-${dir < 0 ? 'left' : 'right'} text-[9px]`} />
            </button>
          ))}
        </div>
      )}
    </div>

    <div
      ref={trackRef}
      className={
        agents.length > 4
          ? 'flex gap-3 overflow-x-auto scrollbar-hide snap-x [&>*]:min-w-[240px] [&>*]:snap-start'
          : 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3'
      }
    >
      {agents.map((agent) => {
        const tone = TONES[agent.live.tone] || TONES.indigo;
        return (
          <div
            key={agent.id}
            className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-3.5 flex flex-col"
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug min-w-0">
                {agent.live.label}
              </p>
              <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-[9px] font-bold uppercase tracking-wider whitespace-nowrap flex-shrink-0">
                Active
              </span>
            </div>

            <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-snug">
              {agent.live.verb}
            </p>
            <p className="text-[13.5px] font-bold text-gray-900 dark:text-white mt-0.5">
              {agent.live.subject}
            </p>

            <div className="mt-3 mb-2">
              <Sparkline series={agent.live.trend} stroke={tone.stroke} />
            </div>

            <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-auto pt-2.5 border-t border-gray-100 dark:border-slate-800">
              Updated {agent.live.updated}
            </p>
          </div>
        );
      })}
    </div>
  </div>
  );
};

export default LiveNowStrip;
