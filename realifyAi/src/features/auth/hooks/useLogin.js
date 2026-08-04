import { useState } from 'react';
import { login as loginRequest } from '@/services/authService';
import { useAuthStore } from '@/store/useAuthStore';

/**
 * Signs the user in and syncs the auth store on success. Local
 * {loading, error} state, mirroring useShopProfile.js — this codebase has no
 * global request-state manager.
 */
export const useLogin = () => {
  const setUser = useAuthStore((s) => s.setUser);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const data = await loginRequest(email, password);
      setUser({ email });
      return data; // { ok, provisioned, redirect? }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { login, loading, error };
};
