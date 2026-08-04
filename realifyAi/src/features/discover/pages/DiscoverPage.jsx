import React, { useState } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import FeedCard from '@/features/discover/components/FeedCard';
import { TrendingTopics, SuggestedFollows, MarketSummary, UpcomingEvents } from '@/features/discover/components/DiscoverWidgets';
import { feedData } from '@/features/discover/data/discoverData';

const DiscoverPage = () => {
  const [activeTab, setActiveTab] = useState('trending');

  const tabs = [
    { id: 'trending', label: 'Trending', icon: 'fa-arrow-trend-up' },
    { id: 'latest', label: 'Latest', icon: 'fa-clock' },
    { id: 'following', label: 'Following', icon: 'fa-user-check' },
    { id: 'community', label: 'Community', icon: 'fa-users' },
  ];

  return (
    <DashboardLayout 
      title="Discover" 
      subtitle="Explore trending insights, market updates, and community discussions"
      showTabs={false}
    >
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main Content Column */}
        <div className="w-full lg:w-[70%] space-y-6">
          {/* Filter Tabs */}
          <section id="filter-tabs">
            <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-2 shadow-sm flex gap-2 flex-wrap transition-colors duration-300">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'bg-brand text-white shadow-md dark:bg-gray-600'
                      : 'bg-white dark:bg-slate-900 text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 border border-transparent'
                  }`}
                >
                  <i className={`fa-solid ${tab.icon}`}></i>
                  {tab.label}
                </button>
              ))}
            </div>
          </section>

          {/* Feed List */}
          <section id="public-feed" className="space-y-4">
            {feedData.map((post, i) => (
              <FeedCard key={i} post={post} />
            ))}

            <div className="text-center py-5">
              <button className="px-6 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-slate-300 rounded-xl font-medium transition shadow-sm">
                <i className="fa-solid fa-rotate mr-2"></i>Load More Posts
              </button>
            </div>
          </section>
        </div>

        {/* Sidebar Widgets Column */}
        <div className="w-full lg:w-[30%] space-y-6">
           <div className="sticky sticky-below-header space-y-6">
              <TrendingTopics />
              <SuggestedFollows />
              <MarketSummary />
              <UpcomingEvents />
           </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DiscoverPage;
