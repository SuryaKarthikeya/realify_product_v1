import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useActionStore = create(
  persist(
    (set) => ({
      executedMap: {
        'sales-item-0':     'Jun 26, 2026 09:30',
        'sales-item-1':     'Jun 26, 2026 13:15',
        'inventory-item-0': 'Jun 25, 2026 11:42',
        'margin-item-2':    'Jun 25, 2026 15:20',
        'ads-item-1':       'Jun 26, 2026 08:45',
      },
      execute:  (id, date) => set((state) => ({ executedMap: { ...state.executedMap, [id]: date } })),
      rollBack: (id) => set((state) => { const n = { ...state.executedMap }; delete n[id]; return { executedMap: n }; }),
    }),
    { name: 'realify-action-store' }
  )
);
