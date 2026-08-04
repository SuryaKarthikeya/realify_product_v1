import React from 'react';

const HistoryItem = ({ item, onClick, onBookmark }) => {
  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl p-4 hover:shadow-md dark:hover:shadow-slate-950/50 dark:hover:bg-slate-800 dark:hover:border-slate-700 transition-all group cursor-pointer"
    >
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-[13px] font-medium text-gray-900 dark:text-slate-100 dark:group-hover:text-purple-400 mb-1 transition-colors line-clamp-1">
            {item.title}
          </h3>
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-3 line-clamp-2">
            {item.description}
          </p>
          <div className="flex items-center justify-between w-full flex-nowrap gap-1.5 text-[10px] sm:text-xs sm:w-auto sm:justify-start sm:gap-4 text-gray-400 dark:text-gray-500">
            <span className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0 whitespace-nowrap">
              <i className="fa-regular fa-clock"></i>
              {item.time}
            </span>
            {item.messages && (
              <span className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0 whitespace-nowrap">
                <i className="fa-solid fa-message"></i>
                {item.messages} messages
              </span>
            )}
            {item.files && (
              <span className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0 whitespace-nowrap">
                <i className="fa-solid fa-file"></i>
                {item.files} files
              </span>
            )}
            {item.charts && (
              <span className="flex items-center gap-1 sm:gap-1.5 flex-shrink-0 whitespace-nowrap">
                <i className="fa-solid fa-chart-line"></i>
                {item.charts} charts
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onBookmark && onBookmark(item.id);
            }}
            className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${
              item.bookmarked
                ? 'text-gray-900 dark:text-slate-100 bg-gray-100 dark:bg-slate-700'
                : 'text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700'
            }`}
          >
            <i className={`${item.bookmarked ? 'fa-solid' : 'fa-regular'} fa-bookmark`}></i>
          </button>
          <button
            onClick={(e) => e.stopPropagation()}
            className="w-8 h-8 flex items-center justify-center text-gray-400 dark:text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50 rounded-lg transition-colors"
          >
            <i className="fa-regular fa-trash-can"></i>
          </button>
        </div>
      </div>
    </div>
  );
};

export default HistoryItem;
