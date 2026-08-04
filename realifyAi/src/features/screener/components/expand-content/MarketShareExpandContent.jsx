import React from 'react';
import { ResponsiveContainer, LineChart, Line, PieChart, Pie, ScatterChart, Scatter, ZAxis, LabelList, XAxis, YAxis, CartesianGrid, Cell, Tooltip as RechartsTooltip } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { COLORS, pieData, trendData, matrixData } from '@/features/screener/data/screenerData';

// Rendered both standalone (chart-positioning modal) and inside the combined "charts" view.
const positioningQuadrants = [
  { title: 'Stars', sub: 'High Share, High Growth', color: 'indigo', icon: 'fa-star', items: ['Market Leader (28.7% • +22%)', 'TechMaster Pro (22.3% • +18%)'] },
  { title: 'Rising Stars', sub: 'Low Share, High Growth', color: 'blue', icon: 'fa-rocket', items: ['Your Brand (18.4% • +15%)', 'SmartBuy Co (9.2% • +24%)'] },
  { title: 'Cash Cows', sub: 'High Share, Low Growth', color: 'sky', icon: 'fa-coins', items: ['EliteGadgets (14.8% • +5%)', 'ValueMart (11.6% • +3%)'] },
  { title: 'Question Marks', sub: 'Low Share, Low Growth', color: 'slate', icon: 'fa-question', items: ['BudgetTech (5.4% • -2%)', 'Others (10.2% • +1%)'] },
];

const trendsSummaryStats = [
  { label: 'Your Growth', val: '+2.1%', sub: 'vs last year', color: 'blue' },
  { label: 'Best Month', val: 'Nov', sub: '19.2% share', color: 'indigo' },
  { label: 'Momentum', val: 'Positive', sub: '3 months up', color: 'sky' },
  { label: 'Volatility', val: 'Low', sub: '±1.2% variance', color: 'slate' },
];

const PositioningMatrixScatter = () => (
  <ResponsiveContainer width="100%" height="100%">
    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
      <XAxis type="number" dataKey="x" name="Market Share" unit="%" label={{ value: 'Market Share (%)', position: 'insideBottom', offset: -10 }} />
      <YAxis type="number" dataKey="y" name="Growth Rate" unit="%" label={{ value: 'Growth Rate (%)', angle: -90, position: 'insideLeft' }} />
      <ZAxis type="number" dataKey="size" range={[200, 1500]} />
      <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
      <Scatter name="Brands" data={matrixData}>
        {matrixData.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={entry.color} />
        ))}
        <LabelList dataKey="name" position="top" style={{ fontSize: 10, fill: '#64748b', fontWeight: 'bold' }} />
      </Scatter>
    </ScatterChart>
  </ResponsiveContainer>
);


const PositioningQuadrantsGrid = () => (
  <div className="grid grid-cols-2 gap-4 mt-4">
    {positioningQuadrants.map((quad, i) => (
      <div key={i} className={`bg-${quad.color}-50 dark:bg-${quad.color}-900/10 border border-${quad.color}-200 dark:border-${quad.color}-800/50 rounded-xl p-4`}>
        <div className="flex items-center gap-2 mb-2">
          <i className={`fa-solid ${quad.icon} text-${quad.color}-600 dark:text-${quad.color}-400`}></i>
          <h4 className="font-bold text-gray-900 dark:text-slate-100 text-sm">{quad.title}</h4>
        </div>
        <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">{quad.sub}</p>
        {quad.items.map((item, j) => (
          <div key={j} className="flex items-center justify-between bg-white dark:bg-slate-900 rounded-lg px-2 py-1.5 mb-1 border border-white dark:border-slate-800">
            <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.split(' (')[0]}</span>
            <span className={`text-xs font-bold text-${quad.color}-600 dark:text-${quad.color}-400`}>{item.split(' (')[1].replace(')', '')}</span>
          </div>
        ))}
      </div>
    ))}
  </div>
);


// Rendered both standalone (chart-trends modal) and inside the combined "charts" view.
const TrendsLineChart = () => (
  <ResponsiveContainer width="100%" height="100%">
    <LineChart data={trendData}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
      <RechartsTooltip />
      <Line type="monotone" dataKey="yourBrand" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 3, fill: '#fff', strokeWidth: 2, stroke: '#8B5CF6' }} name="Your Brand" />
      <Line type="monotone" dataKey="leader" stroke="#22D3EE" strokeWidth={2} strokeDasharray="5 5" name="Leader" />
      <Line type="monotone" dataKey="techMaster" stroke="#10B981" strokeWidth={2} strokeDasharray="5 5" name="TechMaster" />
      <Line type="monotone" dataKey="elite" stroke="#F59E0B" strokeWidth={2} strokeDasharray="5 5" name="EliteGadgets" />
    </LineChart>
  </ResponsiveContainer>
);


const TrendsStatsGrid = () => (
  <div className="grid grid-cols-4 gap-3 mt-4">
    {trendsSummaryStats.map((s, i) => (
      <div key={i} className={`bg-${s.color}-50 dark:bg-${s.color}-900/20 border border-${s.color}-200 dark:border-${s.color}-800 rounded-xl p-3`}>
        <p className={`text-xs text-${s.color}-600 dark:text-${s.color}-400 font-medium mb-1`}>{s.label}</p>
        <p className={`text-xl font-bold text-${s.color}-900 dark:text-${s.color}-100`}>{s.val}</p>
        <p className={`text-xs text-${s.color}-700 dark:text-${s.color}-500 mt-0.5`}>{s.sub}</p>
      </div>
    ))}
  </div>
);


/** Body of the MarketShare drill-down dialog, keyed by which card was expanded. */
const MarketShareExpandContent = ({ modalKey, expandedCategory, setExpandedCategory, expandedMovement, setExpandedMovement }) => (
  <>

              {/* Distribution */}
              {modalKey === 'distribution' && (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <p className="text-sm text-gray-600 dark:text-slate-400">Breakdown of market share across top competitors</p>
                    <div className="flex items-center gap-2">
                      <select className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-sm dark:text-slate-200">
                        <option>All Categories</option><option>Electronics</option><option>Home & Kitchen</option><option>Sports</option>
                      </select>
                      <button className="px-3 py-1.5 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 rounded-xl text-sm font-medium">
                        <i className="fa-solid fa-download mr-1.5"></i>Export
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="h-[360px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={pieData} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value">
                            {pieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <RechartsTooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3">
                      {[
                        { name: 'Your Brand', rank: '#3', value: 18.4, products: 370, revenue: '$2.8M', color: 'blue', icon: 'fa-building' },
                        { name: 'Market Leader', rank: '#1', value: 28.7, products: 892, revenue: '$4.3M', color: 'indigo', icon: 'fa-crown' },
                        { name: 'TechMaster Pro', rank: '#2', value: 22.3, products: 542, revenue: '$3.4M', color: 'blue', icon: 'fa-building' },
                        { name: 'EliteGadgets', rank: '#4', value: 14.8, products: 289, revenue: '$2.2M', color: 'indigo', icon: 'fa-building' },
                        { name: 'Others', rank: '43 brands', value: 15.8, products: '1,234', revenue: '$2.4M', color: 'slate', icon: 'fa-ellipsis' },
                      ].map((brand, i) => (
                        <div key={i} className={`bg-gradient-to-r from-${brand.color}-50 to-${brand.color}-100 dark:from-${brand.color}-900/10 dark:to-${brand.color}-900/20 border border-${brand.color}-200 dark:border-${brand.color}-800/50 rounded-xl p-3`}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 bg-${brand.color}-600 rounded-lg flex items-center justify-center`}>
                                <i className={`fa-solid ${brand.icon} text-white text-xs`}></i>
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{brand.name}</p>
                                <p className="text-xs text-gray-500 dark:text-slate-400">Rank {brand.rank}</p>
                              </div>
                            </div>
                            <p className={`text-xl font-bold text-${brand.color}-900 dark:text-${brand.color}-400`}>{brand.value}%</p>
                          </div>
                          <div className={`w-full bg-${brand.color}-200 dark:bg-slate-700 rounded-full h-2`}>
                            <div className={`bg-${brand.color}-600 h-2 rounded-full`} style={{ width: `${brand.value}%` }}></div>
                          </div>
                          <p className={`text-xs text-${brand.color}-700 dark:text-${brand.color}-500 mt-1`}>{brand.products} products • {brand.revenue} revenue</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* By Category */}
              {modalKey === 'by-category' && (
                <>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600 dark:text-slate-400">Your performance across different product categories</p>
                    <button className="px-3 py-1.5 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 rounded-xl text-sm font-medium">
                      <i className="fa-solid fa-plus mr-1.5"></i>Add Category
                    </button>
                  </div>
                  <div className="space-y-3">
                    {[
                      { id: 'electronics', label: 'Electronics', icon: 'fa-laptop', count: 156, share: '22.4%', rank: '#2', trend: '+18%', color: 'blue' },
                      { id: 'home-kitchen', label: 'Home & Kitchen', icon: 'fa-blender', count: 128, share: '16.8%', rank: '#4', trend: '+15%', color: 'indigo' },
                      { id: 'sports', label: 'Sports & Outdoors', icon: 'fa-basketball', count: 67, share: '19.2%', rank: '#3', trend: '+8%', color: 'blue' },
                      { id: 'toys', label: 'Toys & Games', icon: 'fa-baby', count: 19, share: '12.3%', rank: '#6', trend: '-3%', color: 'indigo' },
                    ].map((cat) => (
                      <div key={cat.id} className="border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden">
                        <div
                          onClick={() => setExpandedCategory(expandedCategory === cat.id ? null : cat.id)}
                          className="bg-gray-50 dark:bg-slate-800/50 p-4 hover:bg-gray-100 dark:hover:bg-slate-800 transition cursor-pointer"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4 flex-1">
                              <div className={`w-10 h-10 bg-${cat.color}-100 dark:bg-${cat.color}-900/30 rounded-lg flex items-center justify-center`}>
                                <i className={`fa-solid ${cat.icon} text-${cat.color}-600 dark:text-${cat.color}-400`}></i>
                              </div>
                              <div className="flex-1">
                                <p className="font-semibold text-gray-900 dark:text-slate-100">{cat.label}</p>
                                <p className="text-xs text-gray-500 dark:text-slate-400">{cat.count} products</p>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className="text-right">
                                  <p className="font-bold text-gray-900 dark:text-slate-100">{cat.share}</p>
                                  <p className="text-xs text-gray-500 font-bold">Share</p>
                                </div>
                                <span className="px-2 py-1 bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-lg text-sm font-bold border border-yellow-200 dark:border-yellow-800">{cat.rank}</span>
                                <span className={`px-2 py-1 ${cat.trend.startsWith('+') ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400'} rounded-lg text-sm font-bold`}>
                                  <i className={`fa-solid fa-arrow-${cat.trend.startsWith('+') ? 'up' : 'down'} mr-1`}></i>{cat.trend}
                                </span>
                              </div>
                            </div>
                            <i className={`fa-solid fa-chevron-${expandedCategory === cat.id ? 'up' : 'down'} text-gray-400 ml-4`}></i>
                          </div>
                        </div>
                        <AnimatePresence>
                          {expandedCategory === cat.id && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 overflow-hidden"
                            >
                              <div className="p-5 space-y-4">
                                <div className="grid grid-cols-3 gap-4">
                                  <div className={`bg-${cat.color}-50 dark:bg-${cat.color}-900/20 rounded-lg p-4`}>
                                    <p className={`text-xs text-${cat.color}-600 dark:text-${cat.color}-400 font-medium mb-1`}>Total Market</p>
                                    <p className={`text-xl font-bold text-${cat.color}-900 dark:text-${cat.color}-100`}>$8.2M</p>
                                  </div>
                                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                                    <p className="text-xs text-green-600 dark:text-green-400 font-medium mb-1">Your Revenue</p>
                                    <p className="text-xl font-bold text-green-900 dark:text-green-100">$1.84M</p>
                                  </div>
                                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                                    <p className="text-xs text-purple-600 dark:text-purple-400 font-medium mb-1">Growth Trend</p>
                                    <p className="text-xl font-bold text-purple-900 dark:text-purple-100">Rising</p>
                                  </div>
                                </div>
                                <div className="flex gap-3">
                                  <button className={`flex-1 px-4 py-2 bg-${cat.color}-600 text-white hover:bg-${cat.color}-700 rounded-lg transition text-sm font-medium`}>
                                    <i className="fa-solid fa-chart-line mr-2"></i>View Detailed Analytics
                                  </button>
                                  <button className="flex-1 px-4 py-2 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition text-sm font-medium">
                                    <i className="fa-solid fa-lightbulb mr-2"></i>Growth Opportunities
                                  </button>
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    ))}
                  </div>
                  <div className="bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-800 rounded-xl p-4">
                    <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                      <i className="fa-solid fa-lightbulb text-yellow-500"></i>Category Insights
                    </h4>
                    <div className="space-y-2">
                      {[
                        { color: 'blue', text: 'Electronics is your strongest category with 22.4% share and #2 ranking' },
                        { color: 'purple', text: 'Home & Kitchen showing strong growth at +15% with opportunity to improve ranking' },
                        { color: 'orange', text: 'Toys & Games requires attention - declining share and low product count' },
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <i className={`fa-solid fa-circle text-${item.color}-600 text-[6px] mt-2 flex-shrink-0`}></i>
                          <p className="text-sm text-gray-700 dark:text-slate-300">{item.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Recent Market Movements */}
              {modalKey === 'movements' && (
                <>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600 dark:text-slate-400">Latest shifts and competitive actions</p>
                    <button className="px-3 py-1.5 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 rounded-xl text-sm font-medium">
                      <i className="fa-solid fa-bell mr-1.5"></i>Set Alerts
                    </button>
                  </div>
                  <div className="space-y-3">
                    {[
                      { id: 'competitor-gain', title: 'Market Leader gained 2.3% in Electronics', status: 'CRITICAL', time: '3 hours ago', icon: 'fa-arrow-trend-up', color: 'blue', analysis: ['Competitor launched 23 new products in wireless audio segment', 'Aggressive pricing strategy with 15-20% discounts', 'Major marketing campaign with influencer partnerships'], stats: [{ l: 'Share Gained', v: '+2.3%', c: 'blue' }, { l: 'Affected Category', v: 'Electronics', c: 'indigo' }, { l: 'Impact on You', v: '-0.8%', c: 'sky' }] },
                      { id: 'your-gain', title: 'You gained 1.8% in Home & Kitchen', status: 'POSITIVE', time: '1 day ago', icon: 'fa-arrow-trend-up', color: 'indigo', analysis: ['New premium cookware line exceeded sales targets by 40%', 'Improved product ratings from 3.8 to 4.5 stars average', 'Holiday bundle promotion drove 30% increase in orders'], stats: [{ l: 'Share Gained', v: '+1.8%', c: 'indigo' }, { l: 'Revenue Impact', v: '+$101K', c: 'blue' }, { l: 'New Ranking', v: '#4 → #3', c: 'sky' }] },
                      { id: 'new-entrant', title: 'MegaTech entered Sports category', status: 'MONITOR', time: '2 days ago', icon: 'fa-building', color: 'sky', analysis: ['Launched with aggressive pricing 10-15% below market average', 'Strong brand reputation from electronics category', 'Focus on fitness equipment and outdoor gear segments'], stats: [{ l: 'Initial Share', v: '1.2%', c: 'sky' }, { l: 'Product Count', v: '200+ SKUs', c: 'blue' }, { l: 'Threat Level', v: 'Medium', c: 'blue' }] },
                      { id: 'price-war', title: 'Price war in Electronics accessories', status: 'ACTIVE', time: '5 days ago', icon: 'fa-dollar-sign', color: 'slate', analysis: ['Major players cutting prices on cables, chargers, and cases', 'Overall category volume up 35% but margin pressure increasing', 'Opportunity to gain share if margins can be maintained'], stats: [{ l: 'Avg Price Drop', v: '-18%', c: 'blue' }, { l: 'Competitors Involved', v: '7 brands', c: 'indigo' }, { l: 'Volume Impact', v: '+35%', c: 'sky' }] },
                    ].map((move) => (
                      <div key={move.id} className="border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden">
                        <div
                          onClick={() => setExpandedMovement(expandedMovement === move.id ? null : move.id)}
                          className={`bg-${move.color}-50 dark:bg-${move.color}-900/10 border-l-4 border-${move.color}-500 p-4 hover:bg-${move.color}-100 dark:hover:bg-${move.color}-900/20 transition cursor-pointer`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <div className={`w-10 h-10 bg-${move.color}-500 rounded-lg flex items-center justify-center flex-shrink-0`}>
                                <i className={`fa-solid ${move.icon} text-white`}></i>
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <p className="font-bold text-gray-900 dark:text-slate-100">{move.title}</p>
                                  <span className={`px-2 py-0.5 bg-${move.color}-600 text-white rounded text-[10px] font-bold`}>{move.status}</span>
                                </div>
                                <p className="text-sm text-gray-600 dark:text-slate-400">Detected {move.time}</p>
                              </div>
                            </div>
                            <i className={`fa-solid fa-chevron-${expandedMovement === move.id ? 'up' : 'down'} text-gray-400 ml-4`}></i>
                          </div>
                        </div>
                        <AnimatePresence>
                          {expandedMovement === move.id && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 overflow-hidden"
                            >
                              <div className="p-5 space-y-4">
                                <div className="grid grid-cols-3 gap-4">
                                  {move.stats.map((s, idx) => (
                                    <div key={idx} className={`bg-${s.c}-50 dark:bg-${s.c}-900/20 rounded-lg p-4`}>
                                      <p className={`text-xs text-${s.c}-600 dark:text-${s.c}-400 font-medium mb-1`}>{s.l}</p>
                                      <p className={`text-2xl font-bold text-${s.c}-900 dark:text-${s.c}-100`}>{s.v}</p>
                                    </div>
                                  ))}
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4">
                                  <h4 className="font-semibold text-gray-900 dark:text-slate-100 mb-3">Analysis</h4>
                                  <ul className="space-y-2">
                                    {move.analysis.map((a, idx) => (
                                      <li key={idx} className="flex items-start gap-2">
                                        <i className={`fa-solid fa-circle text-${move.color}-600 text-[6px] mt-2 flex-shrink-0`}></i>
                                        <span className="text-sm text-gray-700 dark:text-slate-300">{a}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                                <div className="flex gap-3">
                                  <button className={`flex-1 px-4 py-2 bg-${move.color}-600 text-white hover:bg-${move.color}-700 rounded-lg transition text-sm font-medium`}>
                                    <i className={`fa-solid ${move.id === 'your-gain' ? 'fa-rocket' : 'fa-shield'} mr-2`}></i>
                                    {move.id === 'your-gain' ? 'Replicate Success' : 'Counter Strategy'}
                                  </button>
                                  <button className="flex-1 px-4 py-2 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition text-sm font-medium">
                                    <i className="fa-solid fa-chart-line mr-2"></i>View Details
                                  </button>
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Individual Chart: Competitive Positioning Matrix */}
              {modalKey === 'chart-positioning' && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">Market share vs growth rate analysis across all competitors</p>
                  <div className="h-[420px] w-full bg-gray-50 dark:bg-slate-800/30 rounded-xl p-4">
                    <PositioningMatrixScatter />
                  </div>
                  <PositioningQuadrantsGrid />
                </div>
              )}

              {/* Individual Chart: Market Share Trends */}
              {modalKey === 'chart-trends' && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">Track how market share has evolved over the past 12 months</p>
                  <div className="h-[400px] w-full">
                    <TrendsLineChart />
                  </div>
                  <TrendsStatsGrid />
                </div>
              )}

              {/* Charts (both) */}
              {modalKey === 'charts' && (
                <div className="space-y-5">
                  {/* Competitive Positioning Matrix */}
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-1">Competitive Positioning Matrix</h3>
                    <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">Market share vs growth rate analysis</p>
                    <div className="h-[400px] w-full bg-gray-50 dark:bg-slate-800/30 rounded-xl p-4">
                      <PositioningMatrixScatter />
                    </div>
                    <PositioningQuadrantsGrid />
                  </div>

                  {/* Market Share Trends */}
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-1">Market Share Trends (12 Months)</h3>
                    <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">Track how market share has evolved over the past year</p>
                    <div className="h-[380px] w-full">
                      <TrendsLineChart />
                    </div>
                    <TrendsStatsGrid />
                  </div>
                </div>
              )}

  </>
);

export default MarketShareExpandContent;
