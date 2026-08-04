import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const usePinnedChatsStore = create(
  persist(
    (set, get) => ({
      pinnedIds: [],
      isPinned: (id) => get().pinnedIds.includes(id),
      togglePinned: (id) => set((state) => ({
        pinnedIds: state.pinnedIds.includes(id)
          ? state.pinnedIds.filter((x) => x !== id)
          : [...state.pinnedIds, id],
      })),
    }),
    { name: 'realify-pinned-chats' }
  )
);
