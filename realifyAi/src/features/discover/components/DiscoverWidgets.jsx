import React from 'react';
import { trendingTopicsData, suggestedFollowsData, marketSummaryData, upcomingEventsData } from '@/features/discover/data/discoverData';

export const TrendingTopics = () => (
  <section id="trending-topics" className="mb-6">
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 transition-colors duration-300">
      <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-4">Trending Topics</h4>
      <div className="space-y-3">
        {trendingTopicsData.map((topic, i) => (
          <div key={i} className={`flex items-center justify-between p-3 ${topic.bg} rounded-xl border ${topic.border} cursor-pointer hover:opacity-80 transition`}>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-200">{topic.label}</p>
              <p className="text-xs text-gray-600 dark:text-slate-400">{topic.count}</p>
            </div>
            <i className={`fa-solid ${topic.icon}`}></i>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export const SuggestedFollows = () => (
  <section id="suggested-follows" className="mb-6">
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 transition-colors duration-300">
      <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-4">Suggested to Follow</h4>
      <div className="space-y-4">
        {suggestedFollowsData.map((user, i) => (
          <div key={i} className="flex items-center gap-3">
            <img src={user.avatar} alt={user.name} className="w-12 h-12 rounded-full object-cover border border-gray-100 dark:border-slate-700" />
            <div className="flex-1">
              <p className="text-sm font-bold text-gray-900 dark:text-slate-200">{user.name}</p>
              <p className="text-xs text-gray-600 dark:text-slate-400">{user.role}</p>
            </div>
            <button className="px-3 py-1.5 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 rounded-lg text-xs font-medium transition">Follow</button>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export const MarketSummary = () => (
  <section id="market-summary" className="mb-6">
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 transition-colors duration-300">
      <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-4">Market Summary</h4>
      <div className="space-y-3">
        {marketSummaryData.map((index, i) => (
          <div key={i} className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-800 last:border-0 last:pb-0">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-slate-200">{index.label}</p>
              <p className="text-xs text-gray-500 dark:text-slate-500">{index.value}</p>
            </div>
            <span className={`text-sm font-bold ${index.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>{index.change}</span>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export const UpcomingEvents = () => (
  <section id="upcoming-events">
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-5 transition-colors duration-300">
      <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-4">Upcoming Events</h4>
      <div className="space-y-3">
        {upcomingEventsData.map((event, i) => (
          <div key={i} className="flex gap-3 pb-3 border-b border-gray-100 dark:border-slate-800 last:border-0 last:pb-0">
            <div className={`w-12 h-12 ${event.bg} rounded-lg flex flex-col items-center justify-center flex-shrink-0 border border-transparent`}>
              <span className={`text-[10px] ${event.text} font-bold`}>{event.month}</span>
              <span className={`text-lg font-bold ${event.text}`}>{event.date}</span>
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{event.title}</p>
              <p className="text-xs text-gray-600 dark:text-slate-400">{event.desc}</p>
              <p className="text-[10px] text-gray-500 mt-1 font-semibold">{event.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  </section>
);
