import { useState } from 'react';
import { signup as signupRequest } from '@/services/authService';
import { useAuthStore } from '@/store/useAuthStore';

/**
 * Creates the account and syncs the auth store — the account is already
 * signed in server-side (session cookie set) before Stripe Checkout even
 * starts. Local {loading, error} state, mirroring useShopProfile.js.
 *
 * Callers must redirect the browser to the returned checkout_url; there is
 * no card-less signup path on the backend today.
 */
export const useSignup = () => {
  const setUser = useAuthStore((s) => s.setUser);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const signup = async ({ name, email, password, confirmPassword }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await signupRequest({ name, email, password, confirmPassword });
      setUser({ email, name });
      return data; // { ok, checkout_url }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { signup, loading, error };
};
