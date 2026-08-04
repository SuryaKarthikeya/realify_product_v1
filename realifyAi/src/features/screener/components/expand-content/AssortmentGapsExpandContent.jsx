import React from 'react';
import { ResponsiveContainer, BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Cell, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { assortmentCategoryData, assortmentPriorityData, assortmentCompetitorData } from '@/features/screener/data/screenerData';

/** Body of the AssortmentGaps drill-down dialog, keyed by which card was expanded. */
const AssortmentGapsExpandContent = ({ modalKey }) => (
  <>

              {modalKey === 'gap-distribution' && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Gaps by Category</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={assortmentCategoryData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                            <Bar dataKey="gaps" radius={[4, 4, 0, 0]} barSize={40}>
                              {assortmentCategoryData.map((entry, idx) => (
                                <Cell key={idx} fill={entry.fill} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Priority Distribution</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={assortmentPriorityData}
                              cx="50%"
                              cy="50%"
                              innerRadius={70}
                              outerRadius={100}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {assortmentPriorityData.map((entry, idx) => (
                                <Cell key={idx} fill={entry.color} />
                              ))}
                            </Pie>
                            <RechartsTooltip />
                            <Legend iconType="circle" />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Critical Gaps', val: 43, sub: '$780K opp.', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', labelC: 'text-red-600 dark:text-red-400', valC: 'text-red-900 dark:text-red-100', subC: 'text-red-700 dark:text-red-500' },
                      { label: 'High Priority', val: 51, sub: '$620K opp.', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', labelC: 'text-orange-600 dark:text-orange-400', valC: 'text-orange-900 dark:text-orange-100', subC: 'text-orange-700 dark:text-orange-500' },
                      { label: 'Medium Priority', val: 23, sub: '$280K opp.', bg: 'bg-yellow-50 dark:bg-yellow-900/10', border: 'border-yellow-200 dark:border-yellow-800', labelC: 'text-yellow-600 dark:text-yellow-400', valC: 'text-yellow-900 dark:text-yellow-100', subC: 'text-yellow-700 dark:text-yellow-500' },
                      { label: 'Low Priority', val: 10, sub: '$120K opp.', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100', subC: 'text-blue-700 dark:text-blue-500' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-xl p-4`}>
                        <p className={`text-xs font-bold mb-1 uppercase tracking-wider ${item.labelC}`}>{item.label}</p>
                        <p className={`text-2xl font-bold ${item.valC}`}>{item.val}</p>
                        <p className={`text-xs mt-1 font-medium ${item.subC}`}>{item.sub}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {modalKey === 'gaps-by-category' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-2">
                    {[
                      { icon: 'fa-laptop', label: 'Electronics', gaps: 48, coverage: '38%', status: 'CRITICAL', opportunity: '$680K', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', statC: 'text-red-600 dark:text-red-400' },
                      { icon: 'fa-blender', label: 'Home & Kitchen', gaps: 34, coverage: '62%', status: 'HIGH', opportunity: '$520K', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', statC: 'text-orange-600 dark:text-orange-400' },
                      { icon: 'fa-basketball', label: 'Sports & Outdoors', gaps: 28, coverage: '71%', status: 'MEDIUM', opportunity: '$380K', bg: 'bg-amber-50 dark:bg-amber-900/10', border: 'border-amber-200 dark:border-amber-800', statC: 'text-amber-600 dark:text-amber-400' },
                      { icon: 'fa-baby', label: 'Toys & Games', gaps: 17, coverage: '89%', status: 'LOW', opportunity: '$220K', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', statC: 'text-blue-600 dark:text-blue-400' },
                    ].map((cat, i) => (
                      <div key={i} className={`${cat.bg} border ${cat.border} rounded-2xl p-5`}>
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                            <i className={`fa-solid ${cat.icon} ${cat.statC} text-base`}></i>
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 dark:text-slate-100 text-sm">{cat.label}</p>
                            <span className={`text-[10px] font-black tracking-widest ${cat.statC}`}>{cat.status}</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">Missing SKUs</span>
                            <span className="text-xs font-bold text-gray-900 dark:text-slate-100">{cat.gaps}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">Coverage</span>
                            <span className="text-xs font-bold text-gray-900 dark:text-slate-100">{cat.coverage}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">Opportunity</span>
                            <span className="text-xs font-bold text-green-600 dark:text-green-400">{cat.opportunity}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Gaps by Volume</h3>
                    <div className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={assortmentCategoryData} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} width={110} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                          <Bar dataKey="gaps" radius={[0, 4, 4, 0]} barSize={28}>
                            {assortmentCategoryData.map((entry, idx) => (
                              <Cell key={idx} fill={entry.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}

              {modalKey === 'competitor-comparison' && (
                <>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-1">SKU Count by Brand & Category</h3>
                    <p className="text-sm text-gray-500 dark:text-slate-400 mb-4">See how your product range compares to key competitors</p>
                    <div className="h-[360px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={assortmentCompetitorData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis dataKey="category" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <RechartsTooltip
                            cursor={{ fill: 'transparent' }}
                            contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '12px', color: 'var(--tooltip-text)', padding: '12px' }}
                          />
                          <Legend verticalAlign="top" height={36} iconType="circle" />
                          <Bar dataKey="yourBrand" name="Your Brand" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="marketLeader" name="Market Leader" fill="#22D3EE" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="techMaster" name="TechMaster Pro" fill="#10B981" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="eliteGadgets" name="EliteGadgets" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { label: 'Your Brand', val: 370, icon: 'fa-building', bg: 'bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/10 dark:to-blue-900/20', border: 'border-blue-200 dark:border-blue-800', iconBg: 'bg-blue-600', valC: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Market Leader', val: 892, icon: 'fa-crown', bg: 'bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/10 dark:to-red-900/20', border: 'border-red-200 dark:border-red-800', iconBg: 'bg-red-600', valC: 'text-red-600 dark:text-red-400' },
                      { label: 'TechMaster Pro', val: 542, icon: 'fa-microchip', bg: 'bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/10 dark:to-purple-900/20', border: 'border-purple-200 dark:border-purple-800', iconBg: 'bg-purple-600', valC: 'text-purple-600 dark:text-purple-400' },
                      { label: 'EliteGadgets', val: 289, icon: 'fa-shield-halved', bg: 'bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/10 dark:to-green-900/20', border: 'border-green-200 dark:border-green-800', iconBg: 'bg-green-600', valC: 'text-green-600 dark:text-green-400' },
                    ].map((brand, i) => (
                      <div key={i} className={`${brand.bg} border ${brand.border} rounded-2xl p-5 shadow-sm`}>
                        <div className="flex items-center gap-3 mb-4">
                          <div className={`w-10 h-10 ${brand.iconBg} rounded-xl flex items-center justify-center shadow-lg`}>
                            <i className={`fa-solid ${brand.icon} text-white`}></i>
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">{brand.label}</h4>
                            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Total SKUs</p>
                          </div>
                        </div>
                        <p className={`text-3xl font-black ${brand.valC}`}>{brand.val}</p>
                        <div className="mt-3 bg-white/80 dark:bg-slate-900/80 rounded-lg p-2 border border-white dark:border-slate-800 shadow-sm">
                          <span className="text-xs font-bold text-gray-600 dark:text-slate-400">Coverage: </span>
                          <span className={`text-xs font-black ${brand.valC}`}>{Math.round(brand.val / 9.5)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {modalKey === 'gap-summary' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    {[
                      { label: 'Total Gaps Found', sub: 'Across all categories', val: '127', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100' },
                      { label: 'Critical Priority', sub: 'Immediate action needed', val: '43', bg: 'bg-indigo-50 dark:bg-indigo-900/10', border: 'border-indigo-200 dark:border-indigo-800', labelC: 'text-indigo-600 dark:text-indigo-400', valC: 'text-indigo-900 dark:text-indigo-100' },
                      { label: 'Revenue Potential', sub: 'If all gaps filled', val: '$2.4M', bg: 'bg-sky-50 dark:bg-sky-900/10', border: 'border-sky-200 dark:border-sky-800', labelC: 'text-sky-600 dark:text-sky-400', valC: 'text-sky-900 dark:text-sky-100' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-2xl p-6`}>
                        <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${item.labelC}`}>{item.label}</p>
                        <p className={`text-4xl font-black ${item.valC} mb-1`}>{item.val}</p>
                        <p className="text-sm text-gray-500 dark:text-slate-400">{item.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100">Gap Priority Breakdown</h3>
                    <div className="space-y-3">
                      {[
                        { label: 'Critical', value: 43, sub: '$780K opp.', color: '#F43F5E', pct: 34 },
                        { label: 'High Priority', value: 51, sub: '$620K opp.', color: '#F97316', pct: 40 },
                        { label: 'Medium Priority', value: 23, sub: '$280K opp.', color: '#F59E0B', pct: 18 },
                        { label: 'Low Priority', value: 10, sub: '$120K opp.', color: '#3B82F6', pct: 8 },
                      ].map((item, i) => (
                        <div key={i} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-bold" style={{ color: item.color }}>{item.value} gaps</span>
                              <span className="text-xs text-gray-400 dark:text-slate-500">{item.sub}</span>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                            <div className="h-2 rounded-full" style={{ width: `${item.pct}%`, backgroundColor: item.color }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {modalKey === 'top-gap-categories' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    {[
                      { icon: 'fa-laptop', label: 'Electronics', gaps: 48, sub: '48 missing SKUs', status: 'CRITICAL', opportunity: '$680K', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', statC: 'text-red-600 dark:text-red-400' },
                      { icon: 'fa-blender', label: 'Home & Kitchen', gaps: 34, sub: '34 missing SKUs', status: 'HIGH', opportunity: '$520K', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', statC: 'text-orange-600 dark:text-orange-400' },
                      { icon: 'fa-basketball', label: 'Sports & Outdoors', gaps: 28, sub: '28 missing SKUs', status: 'HIGH', opportunity: '$380K', bg: 'bg-amber-50 dark:bg-amber-900/10', border: 'border-amber-200 dark:border-amber-800', statC: 'text-amber-600 dark:text-amber-400' },
                    ].map((cat, i) => (
                      <div key={i} className={`${cat.bg} border ${cat.border} rounded-2xl p-6`}>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                            <i className={`fa-solid ${cat.icon} ${cat.statC} text-base`}></i>
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 dark:text-slate-100">{cat.label}</p>
                            <span className={`text-[10px] font-black tracking-widest ${cat.statC}`}>{cat.status}</span>
                          </div>
                        </div>
                        <p className={`text-3xl font-black ${cat.statC} mb-1`}>{cat.gaps}</p>
                        <p className="text-sm text-gray-500 dark:text-slate-400 mb-3">{cat.sub}</p>
                        <div className="bg-white/80 dark:bg-slate-900/80 rounded-lg p-2 border border-white dark:border-slate-800">
                          <span className="text-xs text-gray-500 dark:text-slate-400">Revenue opportunity: </span>
                          <span className="text-xs font-bold text-green-600 dark:text-green-400">{cat.opportunity}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

  </>
);

export default AssortmentGapsExpandContent;
