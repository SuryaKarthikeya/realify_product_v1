import React from 'react';
import { motion } from 'framer-motion';

const TONE = {
  good: 'text-emerald-600 dark:text-emerald-400',
  bad: 'text-red-600 dark:text-red-400',
  neutral: 'text-gray-900 dark:text-white',
};

/** Right-aligned bubble for what the user asked. */
const UserMessage = ({ text }) => (
  <div className="flex justify-end">
    <div className="max-w-[80%] rounded-2xl bg-gray-100 dark:bg-slate-800 px-4 py-2.5 text-[14px] text-gray-900 dark:text-slate-100">
      {text}
    </div>
  </div>
);

/** Left-aligned answer: headline, prose, metric row, supporting points. */
const AssistantMessage = ({ reply }) => (
  <div className="space-y-4">
    <h3 className="text-[17px] font-bold text-gray-900 dark:text-white leading-snug">
      {reply.headline}
    </h3>

    <p className="text-[14px] leading-relaxed text-gray-700 dark:text-slate-300">
      {reply.body}
    </p>

    <div className="grid grid-cols-3 gap-3">
      {reply.metrics.map((m) => (
        <div
          key={m.label}
          className="rounded-xl border border-gray-100 dark:border-slate-800 bg-gray-50/60 dark:bg-slate-800/40 px-3 py-2.5"
        >
          <div className="text-[9.5px] font-bold uppercase tracking-widest text-gray-400 dark:text-slate-500 mb-1">
            {m.label}
          </div>
          <div className={`text-[16px] font-bold ${TONE[m.tone] || TONE.neutral}`}>
            {m.value}
          </div>
        </div>
      ))}
    </div>

    <ul className="space-y-2.5">
      {reply.bullets.map((b) => (
        <li key={b} className="flex items-start gap-2.5">
          <i className="fa-solid fa-check mt-1 text-[10px] text-blue-600 dark:text-blue-400 flex-shrink-0" />
          <span className="text-[13.5px] leading-relaxed text-gray-700 dark:text-slate-300">{b}</span>
        </li>
      ))}
    </ul>

    <p className="text-[13.5px] font-medium text-gray-500 dark:text-slate-400 pt-1">
      {reply.followUp}
    </p>
  </div>
);

const AnalysisMessage = ({ message }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
  >
    {message.role === 'user'
      ? <UserMessage text={message.text} />
      : <AssistantMessage reply={message.reply} />}
  </motion.div>
);

export default AnalysisMessage;
