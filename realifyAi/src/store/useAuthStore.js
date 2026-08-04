import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getMe, logout as logoutRequest } from '@/services/authService';

export const useAuthStore = create(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,

      /**
       * Sets the signed-in user directly. The real login/signup network
       * calls live in authService — this only syncs client state once the
       * backend has confirmed the session (a successful login/signup
       * response, or a GET /api/me read).
       */
      setUser: (user) => set({ isAuthenticated: true, user }),

      /**
       * Reconciles client state against the backend session — call this on
       * app boot and after any 401. The persisted isAuthenticated/user above
       * are only a paint hint (so the UI doesn't flash "logged out" before
       * this resolves); the session cookie's actual validity is the real
       * source of truth, since it can expire (14 days) or be revoked
       * server-side without this store knowing.
       */
      checkSession: async () => {
        try {
          const me = await getMe();
          if (me.authed) {
            set({
              isAuthenticated: true,
              user: { email: me.email, name: me.name, tenant: me.tenant, role: me.role },
            });
          } else {
            set({ isAuthenticated: false, user: null });
          }
        } catch {
          // A network hiccup shouldn't log a real session out client-side —
          // leave the persisted state as-is and let the next check retry.
        }
      },

      // Used by the invite flow: marks the user as authenticated without a
      // separate /api/me round trip — the invite-accept call already set the
      // session cookie server-side.
      inviteLogin: (user) => set({ isAuthenticated: true, user }),

      logout: async () => {
        try {
          await logoutRequest();
        } catch {
          // Best-effort — client state clears regardless; the cookie expires
          // on its own (14 days) in the worst case.
        }
        localStorage.removeItem("userRole");
        set({ isAuthenticated: false, user: null });
      },
    }),
    { name: 'auth-storage' }
  )
);
