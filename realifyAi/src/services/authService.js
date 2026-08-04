import { identityClient } from '@/services/httpClient';
import { API_PATHS } from '@/services/endpoints';

/**
 * Signs in with email/password. The backend sets the session cookie on
 * success (Set-Cookie, httpOnly) — the response body only carries
 * onboarding-relevant flags, never a token for us to store.
 */
export const login = async (email, password) => {
  const { data } = await identityClient.post(API_PATHS.AUTH.LOGIN, { email, password });
  return data; // { ok, provisioned, redirect? }
};

/**
 * Public front-door signup (POST /api/billing/signup). Creates the account,
 * sets the session cookie, and starts a Stripe Checkout session in the same
 * call — there is no card-less signup path on the backend today. The caller
 * must redirect the browser to `checkout_url` on success; the account
 * already exists and is signed in before checkout completes.
 */
export const signup = async ({ name, email, password, confirmPassword }) => {
  const { data } = await identityClient.post(API_PATHS.AUTH.SIGNUP, {
    name,
    email,
    password,
    confirmPassword,
  });
  return data; // { ok, checkout_url }
};

export const logout = async () => {
  const { data } = await identityClient.post(API_PATHS.AUTH.LOGOUT);
  return data;
};

/**
 * Reads the current session. Deliberately never throws for "not logged in"
 * — the backend answers { authed: false } for that case rather than a 401,
 * so callers can treat this as a plain state read.
 */
export const getMe = async () => {
  const { data } = await identityClient.get(API_PATHS.AUTH.ME);
  return data;
};
