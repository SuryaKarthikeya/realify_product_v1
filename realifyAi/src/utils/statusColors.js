// Shared by NotificationsPage and NotificationDrawer — same status set, same dot/badge colors.
// Callers needing different classes for the same status can spread and override:
// { ...NOTIFICATION_STATUS_CONFIG, Pending: { ... } }
export const NOTIFICATION_STATUS_CONFIG = {
  'Processing': {
    dot: 'bg-blue-500',
    badge: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/30',
  },
  'Completed': {
    dot: 'bg-green-500',
    badge: 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/30',
  },
  'Pending': {
    dot: 'bg-amber-500',
    badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/30',
  },
  'Needs Review': {
    dot: 'bg-red-500',
    badge: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/30',
  },
};
