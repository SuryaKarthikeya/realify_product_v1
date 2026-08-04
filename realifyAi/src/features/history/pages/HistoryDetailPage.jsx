import React, { useState } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import ChatDetailView from '@/features/history/components/ChatDetailView';
import ModelSelector from '@/components/ai/ModelSelector';
import ChatOptionsMenu from '@/features/history/components/ChatOptionsMenu';
import ShareChatModal from '@/features/history/components/ShareChatModal';
import { historyItems } from '@/features/history/data/historyData';

const allItems = [
  ...historyItems.today,
  ...historyItems.yesterday,
  ...historyItems.week,
];

const HistoryDetailPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState('');
  const [shareOpen, setShareOpen] = useState(false);

  const chatId = location.state?.chatId;
  const chat = chatId ? allItems.find(i => i.id === chatId) : null;

  if (!chat) {
    return <Navigate to="/history" replace />;
  }

  const pageTitle = chat.title.length > 52
    ? chat.title.slice(0, 52) + '…'
    : chat.title;

  return (
    <DashboardLayout
      title={pageTitle}
      subtitle=""
      showTabs={false}
      showAIPrompt={false}
      noPadding={true}
      contentClassName="!p-0 !overflow-hidden"
    >
      <div className="flex h-full overflow-hidden">
        <div className="flex flex-col flex-1 min-h-0">

          {/* Chat toolbar: model selector (left) + share / options (right) */}
          <div className="shrink-0 flex items-center justify-between px-4 sm:px-6 py-2.5 border-b border-gray-100 dark:border-slate-800">
            <ModelSelector variant="topbar" />
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setShareOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <i className="fa-solid fa-share-nodes text-xs"></i>
                Share
              </button>
              <ChatOptionsMenu chatId={chat.id} />
            </div>
          </div>

          {/* Scrollable chat messages */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 min-h-0">
            <div className="max-w-3xl mx-auto">
              <ChatDetailView chat={chat} onBack={() => navigate('/history')} />
            </div>
          </div>

          {/* Pinned prompt */}
          <div className="shrink-0 px-4 sm:px-6 pb-5 pt-3">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3.5">
                  <button className="w-7 h-7 flex items-center justify-center bg-slate-600 hover:bg-slate-700 text-white rounded-full transition-colors flex-shrink-0">
                    <i className="fa-solid fa-plus text-[10px]"></i>
                  </button>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder={`Ask anything about ${chat.title.split(' ').slice(0, 5).join(' ').toLowerCase()}...`}
                    className="flex-1 bg-transparent text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 text-sm outline-none"
                  />
                </div>
                <div className="flex items-center justify-between px-4 py-1 border-t border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/40">
                  <div className="flex items-center gap-2">
                    <button className="w-7 h-7 flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                      <i className="fa-solid fa-sliders text-sm"></i>
                    </button>
                    <button className="w-7 h-7 flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
                      <i className="fa-solid fa-microphone text-sm"></i>
                    </button>
                  </div>
                  <div className="flex items-center gap-3">
                    <ModelSelector variant="compact" />
                    <button
                      className={`w-8 h-8 flex items-center justify-center rounded-full transition-all ${
                        inputValue.trim()
                          ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 hover:bg-gray-700'
                          : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-default'
                      }`}
                    >
                      <i className="fa-solid fa-arrow-up text-xs"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div className="flex justify-between items-center mt-2 px-1">
                <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 tracking-wide">AI can make mistakes.</span>
                <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 tracking-wide">100% tokens available</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ShareChatModal isOpen={shareOpen} onClose={() => setShareOpen(false)} />
    </DashboardLayout>
  );
};

export default HistoryDetailPage;
