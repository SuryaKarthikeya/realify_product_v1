/* eslint-disable react-hooks/refs -- the tooltip side is derived from the
   container width during render. Pre-existing behaviour; changing it would
   move the tooltip. */
import React, { useState, useRef } from 'react';
import { Treemap, ResponsiveContainer } from 'recharts';
import { PRODUCT_HEATMAP_DATA, WORKSPACE_METRIC } from '@/features/workspace/modules/dashboard-view/data/dashboardViewData';
import { getHeatColor } from '@/utils/filterUtils';
import useProductNavigation from '@/hooks/useProductNavigation';
import { dashboardPath } from '@/features/workspace/workspaceRoutes';

const LEGEND_STOPS = ['#f9fafb', '#f3f4f6', '#e5e7eb', '#d1d5db', '#9ca3af', '#4b5563', '#374151', '#1f2937', '#111827', '#000000'];

const ProductHeatmap = ({ domain }) => {
  const { goToProduct, buildFallbackWatchlistItem, NO_SPECIFIC_INSIGHTS } = useProductNavigation();
  const [hovered, setHovered] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [expanded, setExpanded] = useState(false);
  const containerRef = useRef(null);
  const metric = WORKSPACE_METRIC[domain] || WORKSPACE_METRIC.sales;

  const handleMouseMove = (e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const navToProduct = (item) => goToProduct({
    name: item.name, sku: `SKU-${item.abbr}`, image: null,
    description: `${item.name} is a top performer in ${item.category}, currently driving ${item.revenue} in revenue.`,
    kpiGroups: [{
      label: 'Overview', color: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-50 dark:bg-blue-900/10',
      kpis: [
        { label: 'Revenue', value: item.revenue },
        { label: 'Margin', value: item.margin },
        { label: 'Units Sold', value: item.units },
        { label: 'ROAS', value: item.roas },
        { label: 'DOC (days)', value: item.doc },
        { label: 'Ad Spend', value: item.adSpend },
        { label: 'Cash Flow', value: item.cashFlow },
      ],
    }],
    insights: NO_SPECIFIC_INSIGHTS,
    watchlistItem: buildFallbackWatchlistItem(item.name, `SKU-${item.abbr}`, { velocity: '—', subtext: '' }),
  }, dashboardPath(domain));

  const renderContent = (props) => {
    const { x, y, width, height, name, change, abbr } = props;
    if (!name || width < 8 || height < 8) return null;
    const bg = getHeatColor(change ?? 0);
    const textFill = (change ?? 0) < 3 ? '#1e293b' : '#ffffff';
    const fontSize = Math.min(12, Math.max(8, width / 6));
    return (
      <g
        onMouseEnter={() => setHovered(props)}
        onMouseLeave={() => setHovered(null)}
        onClick={() => navToProduct(props)}
        style={{ cursor: 'pointer' }}
      >
        <rect
          x={x + 1} y={y + 1}
          width={Math.max(0, width - 2)} height={Math.max(0, height - 2)}
          fill={bg} rx={4}
        />
        {width > 38 && height > 24 && (
          <text
            x={x + 6} y={y + height / 2 + (height > 38 ? -7 : 4)}
            fill={textFill} fontSize={fontSize} fontWeight="700"
            textAnchor="start" dominantBaseline="middle"
          >
            {abbr}
          </text>
        )}
        {width > 44 && height > 38 && (
          <text
            x={x + 6} y={y + height / 2 + 9}
            fill={textFill} fontSize={Math.max(8, fontSize - 2)}
            textAnchor="start" dominantBaseline="middle"
          >
            {change > 0 ? '+' : ''}{change}%
          </text>
        )}
      </g>
    );
  };

  const tooltipRight = mousePos.x > (containerRef.current?.offsetWidth ?? 600) / 2;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-base font-bold text-gray-900 dark:text-slate-100">Margin Distribution</h3>
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">SKU count by margin bucket</p>
        </div>
        <button
          onClick={() => setExpanded(e => !e)}
          className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 transition-colors px-2.5 py-1 rounded-lg border border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600"
        >
          <i className={`fa-solid ${expanded ? 'fa-compress' : 'fa-expand'} text-[10px]`} />
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>
      <div
        ref={containerRef}
        className="relative select-none"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHovered(null)}
      >
        <ResponsiveContainer width="100%" height={expanded ? 520 : 300}>
          <Treemap
            data={PRODUCT_HEATMAP_DATA}
            dataKey="size"
            aspectRatio={expanded ? 4 / 3 : 16 / 9}
            content={renderContent}
          />
        </ResponsiveContainer>

        {hovered && (
          <div
            className="absolute z-50 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl shadow-xl p-3 w-52 pointer-events-none"
            style={{
              left: tooltipRight ? mousePos.x - 216 : mousePos.x + 14,
              top: Math.max(0, mousePos.y - 70),
            }}
          >
            <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-0.5">
              {hovered.category}
            </p>
            <p className="text-sm font-bold text-gray-900 dark:text-slate-100 leading-tight mb-2">
              {hovered.name}
            </p>
            <div className="grid grid-cols-2 gap-1.5 mb-2">
              <div className="p-1.5 rounded-lg bg-gray-50 dark:bg-slate-800 border border-gray-100 dark:border-slate-700">
                <p className="text-[9px] text-gray-400 dark:text-slate-500 mb-0.5">{metric.label}</p>
                <p className="text-xs font-bold text-gray-900 dark:text-slate-100">{hovered[metric.valueKey]}</p>
              </div>
              <div className="p-1.5 rounded-lg bg-gray-50 dark:bg-slate-800 border border-gray-100 dark:border-slate-700">
                <p className="text-[9px] text-gray-400 dark:text-slate-500 mb-0.5">{metric.secondaryLabel}</p>
                <p className="text-xs font-bold text-gray-900 dark:text-slate-100">{hovered[metric.secondary]}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`text-xs font-bold ${hovered.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}
              >
                {hovered.change > 0 ? '↑' : '↓'} {Math.abs(hovered.change)}%
              </span>
              <span className="text-[10px] text-gray-400 dark:text-slate-500">vs last period</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-end gap-1 mt-2">
        <span className="text-[10px] text-gray-400 dark:text-slate-500">Low</span>
        {LEGEND_STOPS.map((c, i) => (
          <div key={i} className="w-5 h-2 rounded-sm" style={{ backgroundColor: c }} />
        ))}
        <span className="text-[10px] text-gray-400 dark:text-slate-500">High</span>
      </div>
    </div>
  );
};

export default ProductHeatmap;
