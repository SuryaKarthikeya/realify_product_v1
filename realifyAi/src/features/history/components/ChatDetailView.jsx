import React, { useState } from 'react';

const ActionBtn = ({ icon, label, active = false, onClick }) => (
  <div className="relative group">
    <button
      onClick={onClick}
      className={`w-6 h-6 flex items-center justify-center rounded-md transition-colors ${
        active
          ? 'text-blue-500 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
          : 'text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800'
      }`}
    >
      <i className={`${icon} text-[10px]`}></i>
    </button>
    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-1.5 py-0.5 text-[9px] font-medium bg-gray-900 dark:bg-slate-700 text-white rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
      {label}
    </span>
  </div>
);

const ChatDetailView = ({ chat, _onBack }) => {
  const [liked, setLiked] = useState(null);
  const [aiCopied, setAiCopied] = useState(false);
  const [userCopied, setUserCopied] = useState(false);

  const copy = (text, setter) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setter(true);
    setTimeout(() => setter(false), 1500);
  };

  return (
    <div className="flex flex-col gap-6 pb-4">

      {/* User message bubble + inline actions */}
      <div className="flex flex-col items-end gap-1.5">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl rounded-tr-sm px-5 py-3.5 max-w-lg shadow-sm">
          <p className="text-sm font-semibold text-gray-800 dark:text-slate-100 leading-relaxed">
            {chat.title}
          </p>
        </div>
        <div className="flex items-center gap-0.5 pr-0.5">
          {chat.date && (
            <span className="text-[10px] text-gray-400 dark:text-slate-600 mr-2 select-none">
              {chat.date}
            </span>
          )}
          <ActionBtn icon="fa-solid fa-rotate-right" label="Retry" />
          <ActionBtn icon="fa-solid fa-pen" label="Edit" />
          <ActionBtn
            icon={userCopied ? 'fa-solid fa-check' : 'fa-regular fa-copy'}
            label={userCopied ? 'Copied!' : 'Copy'}
            active={userCopied}
            onClick={() => copy(chat.title, setUserCopied)}
          />
        </div>
      </div>

      {/* AI response */}
      <div className="flex flex-col gap-2">

        <div className="flex items-center gap-1.5 text-[11px] text-gray-400 dark:text-slate-500">
          <i className="fa-regular fa-eye text-[9px]"></i>
          <span>Viewed a file, searched the web...</span>
        </div>

        <p className="text-sm text-gray-500 dark:text-slate-400 mb-1">
          Now let me fetch more details and assets from the site:
        </p>
        {chat.richContent ? (
          <div className="space-y-4">
            {chat.richContent.map((block, i) => {
              if (block.type === 'paragraph') {
                return (
                  <p key={i} className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">
                    {block.text}
                  </p>
                );
              }
              return (
                <div key={i}>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-slate-100 mb-2">
                    {block.heading}
                  </h4>
                  <ul className="space-y-1.5 ml-1">
                    {block.bullets.map((bullet, j) => (
                      <li key={j} className="flex items-start gap-2.5 text-sm text-gray-700 dark:text-slate-300 leading-relaxed">
                        <span className="mt-2 w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-slate-500 flex-shrink-0" />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">
            {chat.description}
          </p>
        )}

        {(chat.messages || chat.files || chat.charts) && (
          <div className="mt-1 flex items-center gap-4 text-xs text-gray-400 dark:text-slate-500 flex-wrap">
            {chat.messages && (
              <span className="flex items-center gap-1.5">
                <i className="fa-solid fa-message text-[9px]"></i>
                {chat.messages} messages
              </span>
            )}
            {chat.files && (
              <span className="flex items-center gap-1.5">
                <i className="fa-solid fa-file text-[9px]"></i>
                {chat.files} files
              </span>
            )}
            {chat.charts && (
              <span className="flex items-center gap-1.5">
                <i className="fa-solid fa-chart-line text-[9px]"></i>
                {chat.charts} charts
              </span>
            )}
          </div>
        )}

        {/* AI response actions */}
        <div className="flex items-center gap-0.5 mt-2 -ml-0.5">
          <ActionBtn
            icon={liked === 'up' ? 'fa-solid fa-thumbs-up' : 'fa-regular fa-thumbs-up'}
            label="Good response"
            active={liked === 'up'}
            onClick={() => setLiked(liked === 'up' ? null : 'up')}
          />
          <ActionBtn
            icon={liked === 'down' ? 'fa-solid fa-thumbs-down' : 'fa-regular fa-thumbs-down'}
            label="Bad response"
            active={liked === 'down'}
            onClick={() => setLiked(liked === 'down' ? null : 'down')}
          />
          <ActionBtn
            icon={aiCopied ? 'fa-solid fa-check' : 'fa-regular fa-copy'}
            label={aiCopied ? 'Copied!' : 'Copy'}
            active={aiCopied}
            onClick={() => copy(chat.description, setAiCopied)}
          />
          <ActionBtn icon="fa-solid fa-rotate" label="Regenerate" />
        </div>
      </div>
    </div>
  );
};

export default ChatDetailView;
