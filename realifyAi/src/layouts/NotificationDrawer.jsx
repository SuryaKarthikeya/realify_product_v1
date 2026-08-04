import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsData } from '@/features/notifications';
import { NOTIFICATION_STATUS_CONFIG } from '@/utils/statusColors';

const FILTERS = ['All', 'Errors', 'Analysis', 'Assigned'];

const NotificationDrawer = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState('All');

  const unreadCount = notificationsData.filter(n => n.unread).length;

  const filtered = notificationsData.filter(n => {
    if (activeFilter === 'Errors')   return n.status === 'Needs Review';
    if (activeFilter === 'Analysis') return n.type === 'Analysis';
    if (activeFilter === 'Assigned') return n.type === 'Task';
    return true;
  });

  const handleItemClick = (id) => {
    onClose();
    navigate('/notifications', { state: { selectedId: id } });
  };

  const handleViewAll = () => {
    onClose();
    navigate('/notifications');
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 dark:bg-black/40 backdrop-blur-sm z-[60]"
          onClick={onClose}
        />
      )}

      <div
        className={`fixed right-0 top-0 h-screen w-full sm:w-96 bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800 shadow-2xl z-[70] flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 dark:border-slate-800 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 flex items-center gap-2">
              Notifications
              {unreadCount > 0 && (
                <span className="w-5 h-5 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-[10px] font-bold rounded-full flex items-center justify-center leading-none">
                  {unreadCount}
                </span>
              )}
            </h3>
            <div className="flex items-center gap-3">
              <button
                title="Mark all read"
                className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                <i className="fa-solid fa-check-double text-xs" />
              </button>
              <button
                onClick={onClose}
                className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition-colors"
              >
                <i className="fa-solid fa-xmark text-sm" />
              </button>
            </div>
          </div>

          {/* Filter pills */}
          <div className="flex gap-1.5 flex-wrap">
            {FILTERS.map(f => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                  activeFilter === f
                    ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                    : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Notification list */}
        <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-slate-800/60">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-sm text-gray-400 dark:text-slate-600">
              No notifications
            </div>
          ) : (
            filtered.map(n => {
              const cfg = NOTIFICATION_STATUS_CONFIG[n.status] || NOTIFICATION_STATUS_CONFIG['Processing'];
              return (
                <div
                  key={n.id}
                  onClick={() => handleItemClick(n.id)}
                  className={`px-5 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors ${
                    n.unread ? 'bg-gray-50/80 dark:bg-slate-800/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-500 dark:text-slate-400 mb-0.5">
                        <span className="font-semibold text-gray-800 dark:text-slate-200">{n.actor}</span>{' '}
                        {n.action}
                      </p>
                      <p className="text-sm font-bold text-gray-900 dark:text-slate-100 truncate">
                        {n.title}
                      </p>
                      {n.file && (
                        <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5 flex items-center gap-1 truncate">
                          <i className="fa-regular fa-file-lines text-[10px] flex-shrink-0" />
                          <span className="truncate">{n.file.name}</span>
                          <span className="flex-shrink-0 mx-0.5">·</span>
                          <span className="flex-shrink-0">{n.time}</span>
                        </p>
                      )}
                      <div className="mt-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${cfg.badge}`}>
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                          {n.status}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5 flex-shrink-0 pt-0.5">
                      {n.unread && (
                        <span className="w-2 h-2 bg-gray-700 dark:bg-slate-300 rounded-full" />
                      )}
                      <i className="fa-solid fa-chevron-right text-[10px] text-gray-300 dark:text-slate-600 mt-1" />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 border-t border-gray-200 dark:border-slate-800 p-4">
          <button
            onClick={handleViewAll}
            className="w-full text-sm font-semibold text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-slate-100 transition-colors flex items-center justify-center gap-1.5"
          >
            View all notifications
            <i className="fa-solid fa-arrow-right text-xs" />
          </button>
        </div>
      </div>
    </>
  );
};

export default NotificationDrawer;
