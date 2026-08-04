import axios from 'axios';
import { storage } from '@/utils/storage';
import { toApiError } from '@/utils/apiError';

/**
 * The axios instances for the app.
 *
 * Nothing outside src/services imports these — pages and components go
 * through a service module, which keeps request shapes in one layer.
 *
 * Two instances, not one, because the backend mounts two distinct surfaces:
 *   - apiClient      -> /api/v1  the frozen partner card-data contract
 *   - identityClient -> /api     login, signup, session, onboarding — these
 *                                 routes are unversioned and never exist
 *                                 under /api/v1.
 * Both carry the session cookie (withCredentials) since realify-mc auths via
 * a signed httpOnly cookie (Starlette SessionMiddleware), not a bearer token
 * — there is nothing for the client to store or attach by hand.
 */

/**
 * Dev with no explicit VITE_BACKEND_URL: stay relative and let vite.config.js's
 * /api proxy forward to the backend — local dev then needs no CORS setup at
 * all, since every request looks same-origin to the browser. Any explicit
 * VITE_BACKEND_URL (staging, a prod build) talks directly to that origin
 * instead and relies on the backend's CORS configuration.
 */
const configuredBackendUrl = import.meta.env.VITE_BACKEND_URL;
const backendUrl = (
  configuredBackendUrl || (import.meta.env.DEV ? "" : "http://localhost:8001")
).replace(/\/+$/, "");

// Deliberately no 'Content-Type' here: axios sets it per-request based on the
// payload — 'application/json' for a plain object, 'multipart/form-data;
// boundary=...' for a FormData. A hardcoded default would win over axios's
// own multipart boundary on file-upload requests (identify/commit), which
// silently breaks the upload — the backend would parse it as an empty body.
const sharedHeaders = {
  'ngrok-skip-browser-warning': 'true',
  'Bypass-Tunnel-Reminder': 'true',
};

/** Normalizes every rejection into an ApiError so callers handle one error shape. */
const attachErrorInterceptor = (instance) => {
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      const apiError = toApiError(error);
      console.error(`[API Error] ${apiError.status ?? 'network'}: ${apiError.message}`);
      return Promise.reject(apiError);
    }
  );
};

const apiClient = axios.create({
  baseURL: `${backendUrl}/api/v1`,
  headers: sharedHeaders,
  withCredentials: true,
});

// Request interceptor: auto-append the active shop/platform to every card-data call.
apiClient.interceptors.request.use(
  (config) => {
    const shop = storage.getActiveShop();
    const platform = storage.getActivePlatform();

    if (shop) {
      config.params = {
        shop,
        platform,
        ...config.params,
      };
    }

    return config;
  },
  (error) => Promise.reject(error)
);
attachErrorInterceptor(apiClient);

/**
 * Identity + onboarding surface (login, signup, /me, CSV upload). Skips the
 * shop/platform request interceptor above — that's a card-data concern,
 * meaningless before a tenant/session even exists.
 */
export const identityClient = axios.create({
  baseURL: `${backendUrl}/api`,
  headers: sharedHeaders,
  withCredentials: true,
});
attachErrorInterceptor(identityClient);

export default apiClient;
