import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { notificationsData } from '@/features/notifications/data/notificationsData';
import { NOTIFICATION_STATUS_CONFIG } from '@/utils/statusColors';

const FILTERS = ['All', 'Unread', 'Errors', 'Done'];

const StatusBadge = ({ status, size = 'sm' }) => {
  const cfg = NOTIFICATION_STATUS_CONFIG[status] || NOTIFICATION_STATUS_CONFIG['Processing'];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-bold border ${cfg.badge} ${
      size === 'sm' ? 'px-2.5 py-0.5 text-[10px]' : 'px-3 py-1 text-[11px]'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
      {status}
    </span>
  );
};

const NotificationsPage = () => {
  const location = useLocation();
  const initialId = location.state?.selectedId ?? notificationsData[0].id;

  const [selectedId, setSelectedId] = useState(initialId);
  const [activeFilter, setActiveFilter] = useState('All');
  // Mobile: list and detail are separate full-width screens instead of side-by-side panes.
  // If we arrived with an explicit selection (e.g. tapped a notification in the header
  // drawer), skip straight to the detail screen instead of showing the list first.
  // Desktop is unaffected — it always renders both panes regardless of this flag.
  const [mobileShowDetail, setMobileShowDetail] = useState(!!location.state?.selectedId);

  const filteredNotifications = notificationsData.filter(n => {
    if (activeFilter === 'Unread') return n.unread;
    if (activeFilter === 'Errors') return n.status === 'Needs Review';
    if (activeFilter === 'Done')   return n.status === 'Completed';
    return true;
  });

  const selected = notificationsData.find(n => n.id === selectedId);

  return (
    <DashboardLayout
      title="Notifications"
      subtitle="Get updates on every task"
      showTabs={false}
      filters={null}
      noPadding={true}
      showAIPrompt={false}
    >
      <div className="flex h-full bg-white dark:bg-slate-900">

        {/* ── Left panel: notification list ─────────────────────────────── */}
        <div className={`${mobileShowDetail ? 'hidden sm:flex' : 'flex'} w-full sm:w-72 sm:flex-shrink-0 flex-col border-r border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900`}>

          {/* Panel header */}
          <div className="px-4 pt-2.5 pb-2.5 border-b border-gray-200 dark:border-slate-800 flex-shrink-0">
            {/* Row 1: mark-all-read icon pinned right */}
            <div className="flex justify-end mb-1.5">
              <button
                title="Mark all read"
                className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                <i className="fa-solid fa-check-double text-[11px]" />
              </button>
            </div>
            {/* Row 2: filter pills */}
            <div className="flex gap-1 flex-wrap">
              {FILTERS.map(f => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-colors ${
                    activeFilter === f
                      ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-500 hover:bg-gray-200 dark:hover:bg-slate-700 hover:text-gray-700 dark:hover:text-slate-400'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-slate-800/60">
            {filteredNotifications.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-gray-400 dark:text-slate-600 text-sm">
                No notifications
              </div>
            ) : (
              filteredNotifications.map(n => {
                const isSelected = selectedId === n.id;
                return (
                  <div
                    key={n.id}
                    onClick={() => { setSelectedId(n.id); setMobileShowDetail(true); }}
                    className={`px-4 py-3.5 cursor-pointer transition-colors border-l-2 ${
                      isSelected
                        ? 'bg-gray-50 dark:bg-slate-800 border-l-gray-900 dark:border-l-slate-300'
                        : 'border-l-transparent hover:bg-gray-50 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-[13px] font-semibold leading-snug truncate ${
                        isSelected ? 'text-gray-900 dark:text-white' : 'text-gray-800 dark:text-slate-200'
                      }`}>
                        {n.title}
                      </p>
                      {n.unread && (
                        <span className="w-2 h-2 bg-gray-700 dark:bg-slate-300 rounded-full flex-shrink-0 mt-1" />
                      )}
                    </div>
                    <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5 mb-1.5">
                      {n.actor} · {n.time}
                    </p>
                    <StatusBadge status={n.status} size="sm" />
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ── Right panel: detail view ───────────────────────────────────── */}
        {selected ? (
          <div className={`${mobileShowDetail ? 'block' : 'hidden'} sm:block flex-1 overflow-y-auto p-4 sm:p-6 bg-gray-50 dark:bg-slate-950`}>

            {/* Mobile-only: back to the notification list */}
            <button
              onClick={() => setMobileShowDetail(false)}
              className="sm:hidden mb-4 flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors"
            >
              <i className="fa-solid fa-arrow-left text-[10px]" />
            </button>

            {/* Notification header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="w-10 h-10 bg-gray-100 dark:bg-slate-800 rounded-xl flex items-center justify-center flex-shrink-0 border border-gray-200 dark:border-slate-700">
                <i className="fa-regular fa-file-lines text-gray-600 dark:text-slate-400 text-base" />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white leading-tight">{selected.title}</h1>
                <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">
                  {selected.actor} · {selected.fullTime}
                </p>
                <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                  <StatusBadge status={selected.status} size="md" />
                  {selected.priority !== 'Normal' && (
                    <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-500/30">
                      {selected.priority}
                    </span>
                  )}
                  <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 border border-gray-200 dark:border-slate-600">
                    {selected.type}
                  </span>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="mb-5">
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Description</p>
              <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">{selected.description}</p>
            </div>

            {/* File */}
            {selected.file && (
              <div className="flex items-center justify-between p-3.5 bg-white dark:bg-slate-800/60 rounded-xl border border-gray-200 dark:border-slate-700 mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-gray-100 dark:bg-slate-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <i className="fa-regular fa-file-lines text-gray-500 dark:text-slate-400 text-sm" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-800 dark:text-slate-200">{selected.file.name}</p>
                    <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">{selected.file.size} · {selected.file.rows}</p>
                  </div>
                </div>
                <button className="text-[11px] text-gray-600 dark:text-slate-400 font-semibold flex items-center gap-1.5 hover:text-gray-900 dark:hover:text-slate-200 transition-colors">
                  <i className="fa-solid fa-arrow-down-to-line text-[10px]" />
                  Download
                </button>
              </div>
            )}

            {/* Progress */}
            {selected.progress > 0 && (
              <div className="mb-5">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">Progress</p>
                  <span className="text-xs font-bold text-gray-700 dark:text-slate-300">{selected.progress}%</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-slate-800 rounded-full overflow-hidden border border-gray-200 dark:border-slate-700">
                  <div
                    className="h-full bg-gray-700 dark:bg-slate-300 rounded-full transition-all duration-500"
                    style={{ width: `${selected.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Tags */}
            {selected.tags?.length > 0 && (
              <div className="mb-5">
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {selected.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-500 dark:text-slate-400 text-[11px] font-semibold rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Comments */}
            <div className="mb-6">
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3">
                Comments{selected.comments.length > 0 ? ` (${selected.comments.length})` : ''}
              </p>
              {selected.comments.length === 0 ? (
                <p className="text-sm text-gray-400 dark:text-slate-600">No comments yet.</p>
              ) : (
                <div className="space-y-3">
                  {selected.comments.map((c, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-7 h-7 bg-gray-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0 border border-gray-300 dark:border-slate-600">
                        <span className="text-[10px] font-bold text-gray-600 dark:text-slate-300">{c.initials}</span>
                      </div>
                      <div className="flex-1 min-w-0 bg-white dark:bg-slate-800/50 rounded-xl p-3 border border-gray-100 dark:border-slate-700/50">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-[11px] font-bold text-gray-800 dark:text-slate-200">{c.author}</p>
                          <p className="text-[10px] text-gray-400 dark:text-slate-600">{c.time}</p>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed">{c.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* CTA */}
            <button className="w-full py-3 bg-gray-900 dark:bg-slate-100 hover:bg-gray-700 dark:hover:bg-slate-200 active:scale-[0.99] text-white dark:text-gray-900 text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-sm">
              <i className="fa-solid fa-eye text-sm" />
              View Pipeline
            </button>
          </div>
        ) : (
          <div className={`${mobileShowDetail ? 'flex' : 'hidden'} sm:flex flex-1 items-center justify-center bg-gray-50 dark:bg-slate-950`}>
            <p className="text-gray-400 dark:text-slate-600 text-sm">Select a notification to view details</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default NotificationsPage;
