import React from 'react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, CartesianGrid, Cell, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { priceTrendData7d, priceTrendAnalysis7d, buyBoxCategoryData, promoList } from '@/features/screener/data/screenerData';
import PriceMonitoringSection from '@/features/screener/components/price-buybox/PriceMonitoringSection';

/** Body of the PriceBuyBox drill-down dialog, keyed by which card was expanded. */
const PriceBuyBoxExpandContent = ({ modalKey, activePromo, setActivePromo }) => (
  <>

              {/* Pricing Landscape Summary */}
              {modalKey === 'pricing-landscape' && (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <p className="text-sm text-gray-600 dark:text-slate-400">Overview of market pricing dynamics and competitive positioning</p>
                    <button className="px-3 py-1.5 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 rounded-xl text-sm font-medium">
                      <i className="fa-solid fa-download mr-1.5"></i>Export Report
                    </button>
                  </div>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { icon: 'fa-dollar-sign', label: 'Market Avg Price', value: '$67.84', sub: 'Across 2,456 products', color: 'blue' },
                      { icon: 'fa-chart-line', label: 'Price Volatility', value: 'Medium', sub: '±12% weekly variance', color: 'purple' },
                      { icon: 'fa-trophy', label: 'Your Position', value: '2nd', sub: 'Out of 47 competitors', color: 'green' },
                      { icon: 'fa-percent', label: 'Discount Rate', value: '18%', sub: 'Avg across category', color: 'orange' },
                    ].map((item, i) => (
                      <div key={i} className={`bg-gradient-to-br from-${item.color}-50 to-${item.color}-100 dark:from-${item.color}-900/20 dark:to-${item.color}-800/20 border border-${item.color}-200 dark:border-${item.color}-800 rounded-xl p-4`}>
                        <div className="flex items-center gap-3 mb-2">
                          <div className={`w-10 h-10 bg-${item.color}-600 rounded-lg flex items-center justify-center flex-shrink-0`}>
                            <i className={`fa-solid ${item.icon} text-white`}></i>
                          </div>
                          <div>
                            <p className={`text-xs text-${item.color}-600 dark:text-${item.color}-400 font-medium`}>{item.label}</p>
                            <p className={`text-2xl font-bold text-${item.color}-900 dark:text-${item.color}-100`}>{item.value}</p>
                          </div>
                        </div>
                        <p className={`text-xs text-${item.color}-700 dark:text-${item.color}-300`}>{item.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div className="bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl p-5">
                    <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                      <i className="fa-solid fa-lightbulb text-yellow-500"></i>Key Insights
                    </h4>
                    <div className="space-y-2">
                      {[
                        { color: 'blue', text: 'Your average pricing is 8.3% below market, creating strong competitive advantage' },
                        { color: 'purple', text: 'Price wars detected in Electronics — 5 competitors dropped prices by 15%+ this week' },
                        { color: 'green', text: 'Premium segment ($100+) showing 22% growth opportunity with limited competition' },
                      ].map((ins, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <i className={`fa-solid fa-circle text-${ins.color}-600 text-xs mt-1 flex-shrink-0`}></i>
                          <p className="text-sm text-gray-700 dark:text-slate-300">{ins.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Price Distribution Analysis */}
              {modalKey === 'price-distribution' && (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <p className="text-sm text-gray-600 dark:text-slate-400">How your products are distributed across price ranges</p>
                    <select className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm text-gray-900 dark:text-slate-100">
                      <option>All Categories</option><option>Electronics</option><option>Home & Kitchen</option><option>Sports</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="h-[350px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={[
                            { name: 'Budget ($0-$30)', value: 42 },
                            { name: 'Mid-Range ($30-$80)', value: 35 },
                            { name: 'Premium ($80-$150)', value: 18 },
                            { name: 'Luxury ($150+)', value: 5 },
                          ]} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={4} dataKey="value">
                            {['#2563eb', '#7c3aed', '#ea580c', '#16a34a'].map((color, i) => (
                              <Cell key={i} fill={color} />
                            ))}
                          </Pie>
                          <RechartsTooltip formatter={(val) => `${val}%`} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-4">
                      {[
                        { label: 'Budget ($0-$30)', pct: 42, bgColor: 'bg-blue-600', textColor: 'text-blue-600 dark:text-blue-400', products: 156, avg: '$24.50' },
                        { label: 'Mid-Range ($30-$80)', pct: 35, bgColor: 'bg-purple-600', textColor: 'text-purple-600 dark:text-purple-400', products: 128, avg: '$54.80' },
                        { label: 'Premium ($80-$150)', pct: 18, bgColor: 'bg-orange-600', textColor: 'text-orange-600 dark:text-orange-400', products: 67, avg: '$112.30' },
                        { label: 'Luxury ($150+)', pct: 5, bgColor: 'bg-green-600', textColor: 'text-green-600 dark:text-green-400', products: 19, avg: '$224.90' },
                      ].map((item, i) => (
                        <div key={i} className="bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{item.label}</p>
                            <p className={`text-lg font-bold ${item.textColor}`}>{item.pct}%</p>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2 mb-2">
                            <div className={`${item.bgColor} h-2 rounded-full`} style={{ width: `${item.pct}%` }}></div>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-slate-400">{item.products} products • Avg: {item.avg}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Active Promotions & Deals */}
              {modalKey === 'promotions' && (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <p className="text-sm text-gray-600 dark:text-slate-400">Current promotional campaigns and their performance</p>
                    <button className="px-4 py-2 bg-green-600 text-white hover:bg-green-700 rounded-xl text-sm font-medium">
                      <i className="fa-solid fa-plus mr-2"></i>Create Promotion
                    </button>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-12 border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden" style={{ minHeight: 400 }}>
                    <div className="lg:col-span-4 border-r border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-800/30">
                      <div className="divide-y divide-gray-200 dark:divide-slate-800">
                        {promoList.map(promo => (
                          <div
                            key={promo.id}
                            onClick={() => setActivePromo(promo.id)}
                            className={`p-4 cursor-pointer transition-all ${activePromo === promo.id ? 'bg-white dark:bg-slate-800 border-l-4 border-l-blue-600' : 'hover:bg-white/60 dark:hover:bg-slate-800/50 border-l-4 border-l-transparent'}`}
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-center flex-shrink-0">
                                <i className={`fa-solid ${promo.icon} text-blue-600`}></i>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-bold text-sm text-gray-900 dark:text-slate-100 truncate">{promo.title}</p>
                                <div className="flex items-center justify-between gap-1">
                                  <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{promo.type}</p>
                                  <span className="text-xs font-medium text-green-600 flex-shrink-0">{promo.status}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="lg:col-span-8 p-6 bg-white dark:bg-slate-900">
                      {promoList.filter(p => p.id === activePromo).map(promo => (
                        <div key={promo.id}>
                          <div className="bg-blue-50 dark:bg-blue-900/10 border-2 border-blue-200 dark:border-blue-800 rounded-2xl p-6 mb-6">
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-12 h-12 bg-brand rounded-xl flex items-center justify-center dark:bg-gray-600 flex-shrink-0">
                                <i className={`fa-solid ${promo.icon} text-white text-lg`}></i>
                              </div>
                              <div>
                                <h4 className="text-xl font-bold text-gray-900 dark:text-slate-100">{promo.title}</h4>
                                <p className="text-sm text-gray-600 dark:text-slate-400">{promo.type} • {promo.status}</p>
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                              <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm text-center">
                                <p className="text-xs text-gray-500 dark:text-slate-400 mb-1">Avg Discount</p>
                                <p className="text-2xl font-bold text-blue-600">{promo.avgDiscount}</p>
                              </div>
                              <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm text-center">
                                <p className="text-xs text-gray-500 dark:text-slate-400 mb-1">Revenue</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{promo.sales}</p>
                              </div>
                              <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm text-center">
                                <p className="text-xs text-gray-500 dark:text-slate-400 mb-1">Conversion</p>
                                <p className="text-2xl font-bold text-green-600">{promo.conversion}</p>
                              </div>
                            </div>
                          </div>
                          <div className="flex gap-3">
                            <button className="flex-1 px-4 py-2.5 bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 rounded-xl text-sm font-medium transition">
                              <i className="fa-solid fa-pen mr-2"></i>Edit Promotion
                            </button>
                            <button className="px-4 py-2.5 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-medium transition">
                              <i className="fa-solid fa-chart-bar mr-2"></i>Analytics
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Price Monitoring */}
              {modalKey === 'price-monitoring' && <PriceMonitoringSection />}

              {/* 7-Day Price Trends */}
              {modalKey === 'price-chart-trend7d' && (
                <>
                  <p className="text-sm text-gray-600 dark:text-slate-400">Track price movements and competitor activity over the past week</p>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={priceTrendData7d} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                        <XAxis dataKey="day" axisLine={false} tickLine={false} />
                        <YAxis axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                        <RechartsTooltip formatter={(val) => `$${val}`} />
                        <Legend />
                        <Line type="monotone" dataKey="yourPrice" stroke="#2563eb" strokeWidth={3} dot={{ r: 5, fill: '#fff', strokeWidth: 2, stroke: '#2563eb' }} name="Your Price" />
                        <Line type="monotone" dataKey="marketAvg" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" name="Market Avg" />
                        <Line type="monotone" dataKey="competitor" stroke="#f59e0b" strokeWidth={2} strokeDasharray="3 3" name="Competitor" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Avg Price Change', val: '-2.4%', sub: 'Last 7 days', color: 'blue' },
                      { label: 'Price Updates', val: '47', sub: 'Across portfolio', color: 'purple' },
                      { label: 'Lowest Price Day', val: 'Wed', sub: '$62.30 avg', color: 'green' },
                      { label: 'Highest Price Day', val: 'Mon', sub: '$68.50 avg', color: 'orange' },
                    ].map((s, i) => (
                      <div key={i} className={`bg-${s.color}-50 dark:bg-${s.color}-900/20 border border-${s.color}-200 dark:border-${s.color}-800 rounded-xl p-4`}>
                        <p className={`text-xs text-${s.color}-600 dark:text-${s.color}-400 font-medium mb-1`}>{s.label}</p>
                        <p className={`text-2xl font-bold text-${s.color}-900 dark:text-${s.color}-100`}>{s.val}</p>
                        <p className={`text-xs text-${s.color}-700 dark:text-${s.color}-300 mt-1`}>{s.sub}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Price Trend Analysis */}
              {modalKey === 'price-chart-trend' && (
                <>
                  <p className="text-sm text-gray-600 dark:text-slate-400">7-day price comparison between your brand and top competitors</p>
                  <div className="h-[420px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={priceTrendAnalysis7d} margin={{ top: 10, right: 18, left: 10, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                        <XAxis dataKey="day" axisLine={false} tickLine={false} />
                        <YAxis axisLine={false} tickLine={false} />
                        <RechartsTooltip formatter={(v) => `$${v}`} />
                        <Legend />
                        <Line type="monotone" dataKey="yourBrand" name="Your Brand" stroke="#2563eb" strokeWidth={3} dot={{ r: 4, fill: '#fff', strokeWidth: 2, stroke: '#2563eb' }} />
                        <Line type="monotone" dataKey="techMaster" name="TechMaster Pro" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}

              {/* Buy Box Win Rate by Category */}
              {modalKey === 'price-chart-buybox' && (
                <>
                  <p className="text-sm text-gray-600 dark:text-slate-400">Buy Box win rate performance across product categories</p>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={buyBoxCategoryData} margin={{ top: 10, right: 18, left: 10, bottom: 40 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                        <XAxis dataKey="category" axisLine={false} tickLine={false} angle={-22} textAnchor="end" height={60} />
                        <YAxis axisLine={false} tickLine={false} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                        <RechartsTooltip formatter={(v) => `${v}%`} />
                        <Bar dataKey="winRate" name="Win Rate">
                          {buyBoxCategoryData.map((entry, i) => (
                            <Cell key={i} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                    {buyBoxCategoryData.map((item, i) => (
                      <div key={i} className="bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl p-3 text-center">
                        <p className="text-xs text-gray-500 dark:text-slate-400 mb-1">{item.category}</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-slate-100" style={{ color: item.color }}>{item.winRate}%</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

  </>
);

export default PriceBuyBoxExpandContent;
