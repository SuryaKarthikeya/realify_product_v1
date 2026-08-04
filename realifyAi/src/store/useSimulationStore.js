import { create } from 'zustand';

export const useSimulationStore = create((set) => ({
  isSimulating: false,
  progress: 0,
  startSimulation: () => set({ isSimulating: true, progress: 0 }),
  setProgress: (progress) => set({ progress }),
  endSimulation: () => set({ isSimulating: false, progress: 0 }),
}));
