import React from 'react';

/** Full-screen fallback shown while a lazily-loaded route chunk downloads. */
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
    <div className="relative w-16 h-16">
      <div className="absolute top-0 left-0 w-full h-full border-4 border-brand dark:border-gray-500/20 rounded-full animate-pulse"></div>
      <div className="absolute top-0 left-0 w-full h-full border-t-4 border-brand dark:border-gray-500 rounded-full animate-spin"></div>
    </div>
  </div>
);

export default PageLoader;
