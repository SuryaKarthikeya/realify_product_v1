import React, { useState, useRef, useEffect } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import { motion, AnimatePresence } from 'framer-motion';
import { analysisCategories, getAnalysisReply } from '@/features/new-analysis/data/analysisData';
import AnalysisThinking from '@/features/new-analysis/components/AnalysisThinking';
import AnalysisMessage from '@/features/new-analysis/components/AnalysisMessage';
import ModelSelector from '@/components/ai/ModelSelector';
import { useAuthStore } from '@/store/useAuthStore';
import { useOnboardingStore } from '@/features/onboarding/store/useOnboardingStore';
import { storage } from '@/utils/storage';
import logoDark from '@/assets/logo_dark.png';
import logoLight from '@/assets/logo_white.png';

const CategoryTab = ({ cat, idx, activeSuggestion, setActiveSuggestion }) => {
  return (
    <button
      onClick={() => setActiveSuggestion(activeSuggestion === idx ? null : idx)}
      className={`flex flex-1 items-center justify-center gap-2 px-4 py-2 border rounded-full text-[13px] font-md transition-all shadow-sm ${activeSuggestion === idx
        ? 'bg-gray-100 text-gray-900 border-gray-200 dark:bg-slate-800 dark:text-white dark:border-slate-700'
        : 'bg-white text-gray-600 border-gray-100 hover:border-gray-200 hover:bg-gray-50 dark:bg-slate-900 dark:text-slate-300 dark:border-slate-800 dark:hover:bg-slate-800'
        }`}
    >
      <i className={`fa-solid ${cat.icon} text-[13px] ${activeSuggestion === idx ? 'text-gray-900 dark:text-white' : 'text-gray-800 dark:text-slate-400'}`}></i>
      <span className="truncate">{cat.title}</span>
    </button>
  );
};

const NewAnalysisPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [activeSuggestion, setActiveSuggestion] = useState(null);

  // Chat transcript. While empty the page is the centred landing state; once the
  // first prompt is sent it becomes a scrolling conversation with the composer
  // docked at the bottom.
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const hasConversation = messages.length > 0;

  const scrollRef = useRef(null);
  const thinkingTimer = useRef(null);

  /* Monotonic, never derived from the array length: editing rewinds the
     transcript, so a length-based id would hand two different messages the same
     key and leave React unable to tell them apart. */
  const messageSeq = useRef(0);
  const nextId = (role) => `${role}-${messageSeq.current++}`;

  // Keep the newest message in view as the transcript grows.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isThinking]);

  useEffect(() => () => clearTimeout(thinkingTimer.current), []);

  /** Mock analysis latency, then answer from the canned replies. */
  const answer = (text) => {
    setIsThinking(true);
    clearTimeout(thinkingTimer.current);
    thinkingTimer.current = setTimeout(() => {
      setIsThinking(false);
      setMessages((m) => [
        ...m,
        { id: nextId('a'), role: 'assistant', reply: getAnalysisReply(text) },
      ]);
    }, 2000);
  };

  const handleSend = () => {
    const text = prompt.trim();
    if (!text || isThinking) return;

    setMessages((m) => [...m, { id: nextId('u'), role: 'user', text }]);
    setPrompt('');
    setActiveSuggestion(null);
    answer(text);
  };

  /**
   * Re-ask an earlier question with the user's edits.
   *
   * Everything after that turn is dropped before the new answer arrives — the
   * replies below it were answers to the old wording, so leaving them would
   * present a conversation that never happened. The edited question keeps its
   * own id so React re-uses the bubble rather than remounting it.
   */
  const handleEditMessage = (id, text) => {
    if (isThinking) return;
    const index = messages.findIndex((m) => m.id === id);
    if (index === -1) return;

    setMessages([...messages.slice(0, index), { ...messages[index], text }]);
    answer(text);
  };

  const { user } = useAuthStore();
  const onboardingFirstName = useOnboardingStore((s) => s.formValues.firstName);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  // Name captured in onboarding step 1 wins; storage covers a page reload, and
  // the auth user covers sessions that skipped onboarding entirely.
  const userName = onboardingFirstName?.trim() || storage.getUserName() || user?.name || '';

  const toggleDropdown = (id) => {
    setActiveDropdown(activeDropdown === id ? null : id);
  };

  const _recentHistory = [
    {
      day: 'Today', items: [
        { type: 'message', text: 'Q3 Market Analysis for Tech Sector and recent trends' },
        { type: 'message', text: 'Competitor breakdown: Acme vs Globex pricing' }
      ]
    },
    {
      day: 'Previous 7 Days', items: [
        { type: 'chart', text: 'Revenue projection model based on historical data' },
        { type: 'file', text: 'Summarize Q2 earnings report PDF' },
        { type: 'message', text: 'Drafting a cold outreach email template for sales' },
        { type: 'message', text: 'Best practices for user onboarding flows' }
      ]
    }
  ];

  return (
    <DashboardLayout showTabs={false} showAIPrompt={false} noPadding contentClassName="!p-0 overflow-hidden">
      {/* h-full, not flex-1: `<main>` is a block, so `flex-1` here resolved to
          nothing and the column sized to its content — which left the composer
          sitting directly under the answer instead of docked at the bottom.
          `<main>` has a definite height (flex-1 inside the h-screen column), so
          h-full fills it and the transcript below can take the leftover space. */}
      <div className="flex h-full min-h-0 overflow-hidden">
        {/* Main Content */}
        <div className={`flex-1 flex flex-col min-h-0 px-4 sm:px-6 lg:px-8 ${hasConversation ? '' : 'items-center overflow-y-auto hide-scroll py-3 md:py-4 mt-6'}`}>

          {/* Greeting — landing state only */}
          <div className={`mb-5 sm:mb-5 text-center mt-4 md:mt-5 ${hasConversation ? 'hidden' : ''}`}>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-center gap-2 sm:gap-3"
            >
              <img src={logoDark} alt="Realify" className="h-6 sm:h-10 object-contain block dark:hidden opacity-80" />
              <img src={logoLight} alt="Realify" className="h-6 sm:h-10 object-contain hidden dark:block opacity-80" />
              <h2 className="text-[22px] sm:text-[40px] font-medium tracking-tight text-gray-900 dark:text-slate-100" style={{ fontWeight: 200 }}>
                {greeting}{userName ? `, ${userName}` : ''}
              </h2>
            </motion.div>
          </div>

          {/* Transcript — scrolls above the docked composer */}
          {hasConversation && (
            <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto hide-scroll pt-6">
              <div className="w-full max-w-3xl mx-auto flex flex-col gap-5 pb-6">
                {messages.map((m) => (
                  <AnalysisMessage
                    key={m.id}
                    message={m}
                    isBusy={isThinking}
                    onEdit={(text) => handleEditMessage(m.id, text)}
                  />
                ))}
                {isThinking && <AnalysisThinking />}
              </div>
            </div>
          )}

          {/* Docked composer. In conversation mode this is the flex column's last
              child, so it stays pinned to the bottom while the transcript above
              scrolls — and the gradient lets content fade out under it rather
              than ending on a hard edge. */}
          <div className={`w-full max-w-3xl flex flex-col gap-6 ${hasConversation ? 'mx-auto flex-shrink-0 pb-3 pt-1 relative bg-white dark:bg-[#030712]' : ''}`}>
            {hasConversation && (
              <div className="pointer-events-none absolute -top-6 left-0 right-0 h-6 bg-gradient-to-t from-white dark:from-[#030712] to-transparent" />
            )}

            {/* Prompt Box */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-200 dark:border-slate-800 shadow-sm overflow-hidden focus-within:ring-2 focus-within:ring-slate-500/20 focus-within:border-slate-500 transition-all">
              <div className="p-3 sm:p-4">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
                  }}
                  className={`w-full resize-none bg-transparent border-none focus:ring-0 outline-none text-gray-900 dark:text-slate-100 placeholder-gray-400 dark:placeholder-slate-500 text-base sm:text-lg p-0 ${hasConversation ? 'min-h-[28px]' : 'min-h-[40px] sm:min-h-[60px]'}`}
                  placeholder={hasConversation ? 'Ask a follow-up...' : 'How may I help you?'}
                  rows="1"
                />
              </div>

              <div className="flex items-center justify-between p-3 py-2.5 bg-gray-50/50 dark:bg-slate-800/50">
                <div className="flex items-center gap-2">
                  {/* Attach Button */}
                  <div className="relative">
                    <button
                      onClick={() => toggleDropdown('attach')}
                      className="w-7 h-7 flex items-center justify-center text-gray-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 rounded-full transition-all border border-transparent hover:border-gray-200 dark:hover:border-slate-600"
                    >
                      <i className="fa-solid fa-plus"></i>
                    </button>
                    {activeDropdown === 'attach' && (
                      <div className="absolute bottom-full left-0 mb-2 w-48 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-xl z-50 py-2">
                        <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center gap-3">
                          <i className="fa-solid fa-paperclip text-gray-400"></i> Upload File
                        </button>
                        <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center gap-3">
                          <i className="fa-solid fa-image text-gray-400"></i> Upload Image
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Mic Button */}
                  <button
                    onClick={() => setIsRecording(!isRecording)}
                    className={`w-7 h-7 flex items-center justify-center rounded-full transition-all border border-transparent hover:border-gray-200 dark:hover:border-slate-600 ${isRecording ? 'text-red-500 animate-pulse' : 'text-gray-600 dark:text-slate-400'
                      }`}
                  >
                    <i className={`fa-solid ${isRecording ? 'fa-stop' : 'fa-microphone'}`}></i>
                  </button>

                </div>

                <div className="flex items-center gap-3">
                  <ModelSelector />

                  <button
                    onClick={handleSend}
                    disabled={!prompt.trim() || isThinking}
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all shadow-sm active:scale-95 ${prompt.trim() && !isThinking
                      ? 'bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 dark:hover:bg-gray-500'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                      }`}
                  >
                    <i className={`fa-solid ${isThinking ? 'fa-spinner fa-spin' : 'fa-arrow-up'}`}></i>
                  </button>
                </div>
              </div>
            </div>

            {/* Shown only once the user has actually asked something. */}
            {hasConversation && (
              <p className="text-center text-[11px] font-medium text-gray-400 dark:text-slate-500 -mt-4">
                Realify is AI and can make mistakes.
              </p>
            )}

            {/* Category Tab Buttons — landing state only */}
            <div className={`flex flex-col gap-3 w-full px-8 ${hasConversation ? 'hidden' : ''}`}>
              <div className="flex items-center justify-center gap-3 w-full">
                {analysisCategories.map((cat, idx) => (
                  <CategoryTab
                    key={idx}
                    cat={cat}
                    idx={idx}
                    activeSuggestion={activeSuggestion}
                    setActiveSuggestion={setActiveSuggestion}
                  />
                ))}
              </div>

              {/* Suggestions Panel */}
              <AnimatePresence>
                {activeSuggestion !== null && (
                  <motion.div
                    key={activeSuggestion}
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.15 }}
                    className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden"
                  >
                    <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 dark:border-slate-800">
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-slate-400">
                        <i className={`fa-solid ${analysisCategories[activeSuggestion].icon} text-xs`}></i>
                        <span>{analysisCategories[activeSuggestion].title}</span>
                      </div>
                      <button
                        onClick={() => setActiveSuggestion(null)}
                        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition-colors"
                      >
                        <span>Close suggestions</span>
                        <i className="fa-solid fa-xmark"></i>
                      </button>
                    </div>
                    <div>
                      {analysisCategories[activeSuggestion].suggestions.map((s, i) => (
                        <button
                          key={i}
                          onClick={() => { setPrompt(s); setActiveSuggestion(null); }}
                          className="w-full text-left px-4 py-3 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 border-b border-gray-100 dark:border-slate-800 last:border-0 transition-colors"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

          </div>
        </div>

        {/* Right Sidebar - History */}
        {/* Hidden for now */}
        {/* <div className="hidden xl:flex flex-col w-72 min-h-0 shrink-0 my-4 mr-4 bg-[#F6F8FC] dark:bg-slate-900 border border-[#E5EAF2] dark:border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-[#E5EAF2] dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900 flex-shrink-0">
            <h2 className="font-bold text-gray-900 dark:text-slate-100">Recent History</h2>
            <button className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition-colors">
              <i className="fa-solid fa-magnifying-glass"></i>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 scrollbar-hide min-h-0">
            {recentHistory.map((section, sIdx) => (
              <div key={sIdx} className="mb-6">
                <h3 className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest mb-3 px-2">
                  {section.day}
                </h3>
                <ul className="space-y-1">
                  {section.items.map((item, iIdx) => (
                    <li key={iIdx}>
                      <a href="#" className="block px-3 py-2.5 rounded-lg hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-gray-200 dark:hover:border-slate-700 hover:shadow-sm text-sm text-gray-700 dark:text-slate-300 transition-all group">
                        <div className="flex items-start gap-2">
                          <i className={`fa-${item.type === 'message' ? 'regular fa-message' : item.type === 'chart' ? 'solid fa-chart-line' : 'regular fa-file-lines'} mt-0.5 text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300`}></i>
                          <span className="line-clamp-2 leading-tight text-[12px]">{item.text}</span>
                        </div>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex-shrink-0">
            <button 
               onClick={() => navigate('/history')}
              className="w-full flex items-center justify-center gap-2 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-xl p-2 text-sm font-bold transition-all shadow-sm text-gray-700 dark:text-slate-200">
              <span>View all history</span>
            </button>
          </div>
        </div> */}
      </div>
    </DashboardLayout>
  );
};

export default NewAnalysisPage;
