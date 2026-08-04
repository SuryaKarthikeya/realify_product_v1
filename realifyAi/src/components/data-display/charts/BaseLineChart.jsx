import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { CHART_CATEGORICAL } from '@/utils/chartColors';

const BaseLineChart = ({
  data,
  lines, // Array of { key, name, color, type }
  xAxisKey = "name",
  height = 300,
  yAxisFormatter = (val) => val,
  tooltipFormatter = (val) => [val, ""],
  showGrid = true,
  gridType = "3 3",
  margin = { top: 10, right: 10, left: 0, bottom: 0 }
}) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={margin}>
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
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--tooltip-bg, #fff)',
              borderRadius: '12px',
              border: '1px solid var(--tooltip-border, #e2e8f0)',
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
              fontSize: '12px'
            }}
            itemStyle={{ padding: '2px 0' }}
            formatter={tooltipFormatter}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ paddingBottom: '20px', fontSize: '12px' }}
          />
          {lines.map((line, idx) => (
            <Line
              key={line.key || idx}
              type={line.type || "monotone"}
              dataKey={line.key}
              name={line.name}
              stroke={line.color || CHART_CATEGORICAL[idx % CHART_CATEGORICAL.length]}
              strokeWidth={3}
              dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
              activeDot={{ r: 6, strokeWidth: 0 }}
              animationDuration={1000}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BaseLineChart;
