import { create } from 'zustand';
import { storage } from '@/utils/storage';

/**
 * Which specialists the user has graduated out of Shadow.
 *
 * A first-time visitor has graduated nobody, so the Agents page shows 0 Active
 * and no Live Now strip. Each graduation appends one id, and the strip grows
 * with it. Persisted so a refresh does not un-graduate the user's team.
 */
export const useAgentsStore = create((set) => ({
  graduatedIds: storage.getGraduatedAgents(),

  /** Idempotent — graduating the same specialist twice is a no-op. */
  graduateAgent: (id) => set((state) => {
    if (!id || state.graduatedIds.includes(id)) return state;
    const graduatedIds = [...state.graduatedIds, id];
    storage.setGraduatedAgents(graduatedIds);
    return { graduatedIds };
  }),

  resetGraduatedAgents: () => {
    storage.setGraduatedAgents([]);
    return set({ graduatedIds: [] });
  },
}));
