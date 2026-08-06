import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const TONE = {
  good: 'text-emerald-600 dark:text-emerald-400',
  bad: 'text-red-600 dark:text-red-400',
  neutral: 'text-gray-900 dark:text-white',
};

/** Grows the box with its contents, so a longer edit never scrolls inside itself. */
const fitToContent = (el) => {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight}px`;
};

/**
 * Right-aligned bubble for what the user asked, editable in place.
 *
 * Submitting re-asks the question from that point in the conversation — see
 * `handleEditMessage` on the page for what happens to the turns below it.
 */
const UserMessage = ({ text, onEdit, isBusy }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(text);
  const areaRef = useRef(null);

  /* The whole point is to add to the question, so open with the caret at the end
     of it rather than selecting the text (which the next keystroke would wipe). */
  useEffect(() => {
    if (!editing) return;
    const el = areaRef.current;
    if (!el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
    fitToContent(el);
  }, [editing]);

  const cancel = () => {
    setDraft(text);
    setEditing(false);
  };

  const submit = () => {
    const next = draft.trim();
    setEditing(false);
    /* Unchanged text would re-run the same question for the same answer and
       throw away the replies below it for nothing. */
    if (!next || next === text) {
      setDraft(text);
      return;
    }
    onEdit(next);
  };

  if (editing) {
    return (
      <div className="flex justify-end">
        <div className="w-full max-w-[85%] rounded-2xl bg-gray-100 dark:bg-slate-800 px-3.5 py-3">
          <textarea
            ref={areaRef}
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value);
              fitToContent(e.target);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
              if (e.key === 'Escape') cancel();
            }}
            rows="1"
            aria-label="Edit your question"
            className="w-full resize-none bg-transparent border-none outline-none focus:ring-0 p-0 text-[14px] leading-relaxed text-gray-900 dark:text-slate-100"
          />

          <div className="flex items-center justify-end gap-2 mt-2.5">
            <button
              onClick={cancel}
              className="px-3 py-1.5 rounded-lg text-[12.5px] font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-200/70 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={submit}
              disabled={!draft.trim() || isBusy}
              className="px-3 py-1.5 rounded-lg text-[12.5px] font-bold bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group flex justify-end items-end gap-1.5">
      <button
        onClick={() => setEditing(true)}
        disabled={isBusy}
        aria-label="Edit this question"
        title="Edit"
        className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity flex-shrink-0 disabled:opacity-0"
      >
        <i className="fa-solid fa-pen text-[11px]" />
      </button>

      <div className="max-w-[80%] rounded-2xl bg-gray-100 dark:bg-slate-800 px-4 py-2.5 text-[14px] text-gray-900 dark:text-slate-100 whitespace-pre-wrap">
        {text}
      </div>
    </div>
  );
};

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

const AnalysisMessage = ({ message, onEdit, isBusy }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
  >
    {message.role === 'user'
      ? <UserMessage text={message.text} onEdit={onEdit} isBusy={isBusy} />
      : <AssistantMessage reply={message.reply} />}
  </motion.div>
);

export default AnalysisMessage;
