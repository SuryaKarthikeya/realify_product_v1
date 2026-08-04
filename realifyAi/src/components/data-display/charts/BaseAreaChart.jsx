import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { CHART_CATEGORICAL } from '@/utils/chartColors';

const BaseAreaChart = ({
  data,
  areas, // Array of { key, name, color, type, strokeDasharray, fillOpacity, stackId }
  xAxisKey = "name",
  height = 300,
  yAxisFormatter = (val) => val,
  tooltipFormatter = (val) => [val, ""],
  showGrid = true,
  gridType = "3 3",
  margin = { top: 10, right: 10, left: 0, bottom: 0 },
  showLegend = true,
  yDomain,
}) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={margin}>
          <defs>
            {areas.map((area, idx) => {
              const color = area.color || CHART_CATEGORICAL[idx % CHART_CATEGORICAL.length];
              return (
                <linearGradient key={`gradient-${area.key}`} id={`color-${area.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={area.fillOpacity || 0.1}/>
                  <stop offset="95%" stopColor={color} stopOpacity={0}/>
                </linearGradient>
              );
            })}
          </defs>
          {showGrid && (
            <CartesianGrid 
              strokeDasharray={gridType} 
              vertical={false} 
              stroke="currentColor" 
              className="text-gray-200 dark:text-slate-800" 
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'currentColor', fontSize: 11 }}
            className="text-gray-500 dark:text-slate-400"
            dy={10}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'currentColor', fontSize: 11 }}
            className="text-gray-500 dark:text-slate-400"
            tickFormatter={yAxisFormatter}
            domain={yDomain}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--tooltip-bg, #ffffff)',
              borderRadius: '12px',
              border: '1px solid var(--tooltip-border, #e2e8f0)',
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
              fontSize: '12px',
              color: 'var(--tooltip-text, #0f172a)',
            }}
            itemStyle={{ padding: '2px 0' }}
            formatter={tooltipFormatter}
          />
          {showLegend && (
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: '20px', fontSize: '12px' }}
            />
          )}
          {areas.map((area, idx) => (
            <Area
              key={area.key || idx}
              type={area.type || "monotone"}
              dataKey={area.key}
              name={area.name}
              stroke={area.color || CHART_CATEGORICAL[idx % CHART_CATEGORICAL.length]}
              strokeWidth={area.strokeWidth || 3}
              strokeDasharray={area.strokeDasharray}
              fillOpacity={1}
              fill={area.fill === 'none' ? 'none' : `url(#color-${area.key})`}
              stackId={area.stackId}
              animationDuration={1000}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BaseAreaChart;
