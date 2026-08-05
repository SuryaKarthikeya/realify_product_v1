import React from "react";
import { useUIStore } from "@/store/useUIStore";
import { useAIStore } from "@/store/useAIStore";
import { motion, AnimatePresence } from "framer-motion";
import ModelSelector from "@/components/ai/ModelSelector";

const AIPromptBox = ({ placeholder = "Ask Realify...", sidebarActive = true, fullWidth: _fullWidth = false }) => {
  const { isSidebarCollapsed } = useUIStore();
  const {
    aiPromptValue, setAiPromptValue,
    aiReferences, removeAiReference,
    setAIResultOpen, setAiThinking
  } = useAIStore();

  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleSubmit = () => {
    if (aiPromptValue.trim() || aiReferences.length > 0) {
      setAIResultOpen(true);
      setAiThinking(true);
      setTimeout(() => setAiThinking(false), 2000); // Mock thinking delay
      setAiPromptValue('');
    }
  };

  return (
    <motion.div
      initial={false}
      animate={{
        // Match the page content's horizontal bounds exactly: left = sidebar
        // width (200 / 56 collapsed) + <main> padding (10px); right = <main>
        // padding (10px). Same max-w + inner px as the sections below the brief,
        // so the box lines up with them at every viewport width.
        left: isMobile ? 8 : (!sidebarActive ? 10 : (isSidebarCollapsed ? 79 : 223)),
        right: isMobile ? 8 : 23,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed bottom-0 z-50 pb-2 pointer-events-none"
    >
      <div className="pointer-events-auto max-w-[1600px] mx-auto px-3 sm:px-4">
        {/* Outer Container — neutral surface. The accent lives on the input ring
            below, so the box reads as a lit field rather than a glowing slab. */}
        <div className="bg-white/95 backdrop-blur-sm shadow-[0_8px_28px_-10px_rgba(15,23,42,0.18)] border border-gray-200/90 dark:border-slate-700/80 dark:bg-slate-900/95 rounded-2xl p-3 sm:p-4 transition-colors">

          {/* Reference Tag Section (If active) */}
          <AnimatePresence>
            {aiReferences.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                animate={{ opacity: 1, height: 'auto', marginBottom: 12 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                className="flex items-center flex-wrap gap-2"
              >
                {aiReferences.map(ref => (
                  <div key={ref.id} className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-lg group transition-all">
                    <i className="fa-solid fa-paperclip text-blue-500 dark:text-blue-400 text-[10px]"></i>
                    <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                      {ref.title}
                    </span>
                    <button
                      onClick={() => removeAiReference(ref.id)}
                      className="ml-1 text-blue-400 hover:text-blue-600 dark:hover:text-blue-200 transition-colors"
                    >
                      <i className="fa-solid fa-xmark text-[10px]"></i>
                    </button>
                  </div>
                ))}
                <div className="h-[1px] flex-1 bg-gradient-to-r from-blue-100 dark:from-blue-800 to-transparent"></div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input Row */}
          <div className="flex items-center gap-1.5 sm:gap-3 bg-white dark:bg-slate-800 border border-blue-500/45 dark:border-blue-500/40 rounded-full px-2.5 sm:px-4 py-2 shadow-[inset_0_0_0_1px_rgba(37,99,235,0.06)] focus-within:border-blue-500/80 focus-within:ring-2 focus-within:ring-blue-500/15 transition-all">

            {/* Add Button */}
            <button
              className="w-6 h-6 flex items-center justify-center bg-slate-500 hover:bg-slate-600 text-white rounded-full transition-colors flex-shrink-0"
              title="Add context"
            >
              <i className="fa-solid fa-plus text-[10px]"></i>
            </button>

            <button
              className="hidden sm:flex w-8 h-8 items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Preferences"
            >
              <i className="fa-solid fa-sliders text-sm"></i>
            </button>

            {/* Input */}
            <input
              type="text"
              value={aiPromptValue}
              onChange={(e) => setAiPromptValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder={aiReferences.length > 0 ? "Ask about the attached context..." : placeholder}
              className="ai-prompt-input flex-1 min-w-0 bg-transparent text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 text-sm outline-none px-1 sm:px-2 py-1.5"
            />

            {/* Right Controls */}
            <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
              <ModelSelector variant="compact" />

              <button className="hidden sm:block text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                <i className="fa-solid fa-microphone text-sm"></i>
              </button>

              {/* Submit Button */}
              <button
                onClick={handleSubmit}
                className={`w-8 h-8 flex items-center justify-center rounded-full transition-all flex-shrink-0 ${aiPromptValue.trim() || aiReferences.length > 0 ? 'bg-brand hover:bg-brand-hover text-white dark:bg-gray-600 dark:hover:bg-gray-500' : 'bg-slate-200 dark:bg-slate-700 text-slate-400'
                  }`}
              >
                <i className="fa-solid fa-arrow-up"></i>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center gap-2 mt-2 sm:mt-3 px-2">
            <span className="text-[9px] sm:text-[10px] font-bold text-slate-400 dark:text-slate-500 tracking-wide truncate">
              Realify is AI & can make mistakes.
            </span>
            <span className="text-[9px] sm:text-[10px] font-bold text-slate-400 dark:text-slate-500 tracking-wide whitespace-nowrap">
              100% tokens available
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default AIPromptBox;
