import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { warehouseDistributionData } from '@/features/workspace/domains/inventory/data/inventoryData';

const WarehouseSection = ({ darkMode }) => {
  const warehouses = [
    {
      name: 'Main Warehouse',
      location: 'Chicago, IL',
      status: 'PRIMARY',
      capacity: 85,
      skus: '1,247',
      value: '$1.1M',
      color: 'bg-blue-600',
      gradient: 'from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-900/10',
      border: 'border-blue-200 dark:border-blue-900/30'
    },
    {
      name: 'East Coast DC',
      location: 'Newark, NJ',
      status: 'ACTIVE',
      capacity: 72,
      skus: '894',
      value: '$780K',
      color: 'bg-cb-600',
      gradient: 'from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-900/10',
      border: 'border-blue-200 dark:border-blue-900/30'
    },
    {
      name: 'West Coast DC',
      location: 'Los Angeles, CA',
      status: 'ACTIVE',
      capacity: 68,
      skus: '706',
      value: '$520K',
      color: 'bg-cb-500',
      gradient: 'from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-900/10',
      border: 'border-indigo-200 dark:border-indigo-900/30'
    }
  ];

  return (
    <section id="warehouse-distribution" className="mb-5 mt-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Warehouse Distribution Analysis</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400">Inventory allocation across distribution centers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Stock by Warehouse</h4>
          <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={warehouseDistributionData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={60}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {warehouseDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: darkMode ? '#0f172a' : '#ffffff',
                    borderColor: darkMode ? '#1e293b' : '#e2e8f0',
                    borderRadius: '12px'
                  }}
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Warehouse Performance</h4>
          <div className="space-y-4">
            {warehouses.map((wh, idx) => (
              <div key={idx} className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h5 className="font-bold text-gray-900 dark:text-slate-100">{wh.name}</h5>
                    <p className="text-xs text-gray-600 dark:text-slate-400">{wh.location}</p>
                  </div>
                  <span className="px-3 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 rounded-lg text-xs font-bold">{wh.status}</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div>
                    <p className="text-xs text-gray-600 dark:text-slate-400">Capacity</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{wh.capacity}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 dark:text-slate-400">SKUs</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{wh.skus}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 dark:text-slate-400">Value</p>
                    <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{wh.value}</p>
                  </div>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-400 dark:bg-slate-500 rounded-full" style={{ width: `${wh.capacity}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default WarehouseSection;
