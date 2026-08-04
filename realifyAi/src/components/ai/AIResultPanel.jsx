import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAIStore } from '@/store/useAIStore';

// --- SIDE PANEL VARIANT (Original) ---
// --- Color Mapping ---
const COLOR = {
  blue:   { bg: 'bg-blue-50 dark:bg-blue-900/10', iconBg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400', tagBg: 'bg-blue-100 dark:bg-blue-900/50', tagText: 'text-blue-700 dark:text-blue-300' },
  orange: { bg: 'bg-orange-50 dark:bg-orange-900/10', iconBg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-400', tagBg: 'bg-orange-100 dark:bg-orange-900/50', tagText: 'text-orange-700 dark:text-orange-300' },
  green:  { bg: 'bg-green-50 dark:bg-green-900/10', iconBg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-600 dark:text-green-400', tagBg: 'bg-green-100 dark:bg-green-900/50', tagText: 'text-green-700 dark:text-green-300' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-900/10', iconBg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400', tagBg: 'bg-purple-100 dark:bg-purple-900/50', tagText: 'text-purple-700 dark:text-purple-300' },
};

// --- Mock Response Data ---
const DUMMY_RESPONSE = {
  summary: "Based on your current data, here's what Realify found:",
  sections: [
    {
      icon: 'fa-chart-line', color: 'blue',
      title: 'Performance Overview',
      body: 'Your sales are trending <strong class="text-blue-700 dark:text-blue-300">+12.4% above</strong> the 30-day average. The strongest growth is coming from the <strong>Electronics</strong> category, which accounts for 38% of total revenue this period.',
      tags: ['Revenue Up', 'Electronics Leading']
    },
    {
      icon: 'fa-triangle-exclamation', color: 'orange',
      title: 'Anomaly Detected',
      body: 'Cash flow dipped unexpectedly on <strong>Tuesday and Wednesday</strong> last week — likely tied to delayed receivables from 3 accounts. Total exposure: <strong class="text-orange-700 dark:text-orange-300">$24,800</strong>. Recommend following up with accounts AR-0041, AR-0078, AR-0112.',
      tags: ['Cash Flow', 'Action Needed']
    },
    {
      icon: 'fa-lightbulb', color: 'green',
      title: 'Recommendation',
      body: 'Consider shifting <strong class="text-green-700 dark:text-green-300">15–20% of ad spend</strong> from Facebook Ads to Google Shopping, where your ROAS is currently <strong>4.2×</strong> vs <strong>1.8×</strong>. Projected monthly impact: <strong class="text-green-700 dark:text-green-300">+$8,400 net revenue</strong>.',
      tags: ['Ads Optimisation', 'High Confidence']
    },
    {
      icon: 'fa-boxes-stacked', color: 'purple',
      title: 'Inventory Alert',
      body: '<strong class="text-purple-700 dark:text-purple-300">7 SKUs</strong> are projected to hit stockout within 14 days based on current sell-through rate. The highest risk item is <strong>Bluetooth Speaker Pro</strong> with only 42 units remaining.',
      tags: ['Low Stock', 'Reorder Soon']
    }
  ],
  followUps: [
    'Show me the at-risk SKUs',
    'Break down revenue by channel',
    'What drove the cash flow dip?',
    'Compare this month vs last month'
  ]
};

// --- SIDE PANEL VARIANT ---
const AIResultPanelSide = () => {
  const { 
    aiResultPanelMode, setAIResultMode, closeAIResult, 
    isAiThinking, aiReferences, removeAiReference,
  } = useAIStore();

  const variants = {
    half: { width: '50vw', x: 0 },
    full: { width: '100vw', x: 0 },
    minimized: { width: '64px', x: 'calc(100% - 64px)' },
    closed: { width: '0vw', x: '100%' }
  };

  const [followUpQuery, setFollowUpQuery] = useState('');

  const handleFollowUp = () => {
    if (followUpQuery.trim()) {
      // Mock triggering a new answer
      setFollowUpQuery('');
    }
  };

  return (
    <motion.div
      initial="closed"
      animate={aiResultPanelMode}
      variants={variants}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`fixed top-0 right-0 h-screen bg-white dark:bg-[#0f172a] shadow-2xl z-[100] border-l border-gray-200 dark:border-slate-800 flex flex-col`}
    >
      {/* Header Controls */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-slate-900 dark:bg-slate-100 rounded-lg flex items-center justify-center">
            <i className="fa-solid fa-wand-magic-sparkles text-white dark:text-slate-900 text-xs"></i>
          </div>
          {aiResultPanelMode !== 'minimized' && (
            <div>
              <p className="font-bold text-gray-900 dark:text-slate-100 text-sm leading-tight">Realify AI</p>
              <p className="text-[10px] text-gray-500 dark:text-slate-400 font-medium">{isAiThinking ? 'Thinking...' : 'Ready'}</p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setAIResultMode('minimized')}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 transition-colors"
            title="Minimize"
          >
            <i className="fa-solid fa-minus text-xs"></i>
          </button>

          <button
            onClick={() => setAIResultMode(aiResultPanelMode === 'full' ? 'half' : 'full')}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 transition-colors"
            title={aiResultPanelMode === 'full' ? 'Half Screen' : 'Full Screen'}
          >
            <i className={`fa-solid ${aiResultPanelMode === 'full' ? 'fa-compress' : 'fa-expand'} text-xs`}></i>
          </button>

          <button
            onClick={closeAIResult}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors"
            title="Close"
          >
            <i className="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      </div>

      {aiResultPanelMode !== 'minimized' ? (
        <>
          <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar">
            {isAiThinking ? (
              <AnalyzingState />
            ) : (
              <ContentArea />
            )}
          </div>

          {/* Follow-up / Bottom Bar */}
          {!isAiThinking && (
            <div className="p-4 border-t border-gray-200 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-900/50 flex-shrink-0">
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-3">Follow-up questions</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {DUMMY_RESPONSE.followUps.map((q, idx) => (
                  <button 
                    key={idx}
                    onClick={() => setFollowUpQuery(q)}
                    className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-[11px] font-medium text-gray-700 dark:text-slate-300 hover:bg-slate-900 hover:text-white dark:hover:bg-slate-100 dark:hover:text-slate-900 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Multiple References in Sidebar */}
              {aiReferences.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {aiReferences.map(ref => (
                    <div key={ref.id} className="flex items-center gap-2 px-2 py-1 bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-md text-[10px] text-blue-700 dark:text-blue-300 font-medium">
                      <i className="fa-solid fa-paperclip text-[8px]"></i>
                      <span className="truncate max-w-[100px]">{ref.title}</span>
                      <button onClick={() => removeAiReference(ref.id)} className="text-blue-400 hover:text-blue-600 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-2xl p-1.5 flex items-center gap-2 shadow-sm focus-within:ring-2 focus-within:ring-blue-100 dark:focus-within:ring-blue-900/20 transition-all">
                <input 
                  type="text" 
                  value={followUpQuery}
                  onChange={(e) => setFollowUpQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleFollowUp()}
                  placeholder="Ask Realify..." 
                  className="flex-1 bg-transparent text-sm text-gray-700 dark:text-slate-200 outline-none px-3"
                />
                <button 
                  onClick={handleFollowUp}
                  className="w-8 h-8 flex items-center justify-center bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-full hover:opacity-90 transition-opacity"
                >
                  <i className="fa-solid fa-arrow-up text-xs"></i>
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <MinimizedRestore onRestore={() => setAIResultMode('half')} />
      )}
    </motion.div>
  );
};

// --- Shared Sub-components ---

const AnalyzingState = () => (
  <div className="flex flex-col items-center justify-center py-12 space-y-6">
    <div className="flex gap-1.5">
      <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
      <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
      <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce"></span>
    </div>
    <p className="text-sm text-gray-500 dark:text-slate-400 font-medium">Analysing your data...</p>
  </div>
);

const ContentArea = () => (
  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <p className="text-sm text-gray-600 dark:text-slate-400 font-medium leading-relaxed">
      {DUMMY_RESPONSE.summary}
    </p>

    {DUMMY_RESPONSE.sections.map((section, idx) => {
      const c = COLOR[section.color] || COLOR.blue;
      return (
        <div 
          key={idx}
          className={`${c.bg} border border-gray-100 dark:border-slate-800 rounded-2xl p-5 shadow-sm transition-transform hover:scale-[1.01]`}
          style={{ animationDelay: `${idx * 150}ms` }}
        >
          <div className="flex items-start gap-4">
            <div className={`w-10 h-10 ${c.iconBg} rounded-xl flex items-center justify-center flex-shrink-0`}>
              <i className={`fa-solid ${section.icon} ${c.text} text-sm`}></i>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-2">{section.title}</h4>
              <p 
                className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: section.body }}
              ></p>
              <div className="flex flex-wrap gap-2">
                {section.tags.map((tag, tIdx) => (
                  <span key={tIdx} className={`${c.tagBg} ${c.tagText} px-3 py-1 rounded-full text-[10px] font-bold tracking-wider`}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    })}
  </div>
);

const MinimizedRestore = ({ onRestore }) => (
  <div className="flex-1 flex items-center justify-center cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors" onClick={onRestore}>
    <div className="transform -rotate-90 whitespace-nowrap text-xs font-bold text-gray-400 tracking-widest flex items-center gap-2">
      <i className="fa-solid fa-chevron-up"></i> Restore Analysis
    </div>
  </div>
);

// --- Main Exposure ---

const AIResultPanel = () => {
  const isAIResultOpen = useAIStore(s => s.isAIResultOpen);
  if (!isAIResultOpen) return null;

  return <AIResultPanelSide />;
};

export default AIResultPanel;
