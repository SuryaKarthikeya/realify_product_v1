/**
 * Public API of the History feature.
 *
 * The app shell (sidebar) surfaces recent chats, so that data is exported here
 * rather than deep-imported. Everything else under features/history/ is
 * internal and may be refactored freely.
 */
export { historyItems } from '@/features/history/data/historyData';
