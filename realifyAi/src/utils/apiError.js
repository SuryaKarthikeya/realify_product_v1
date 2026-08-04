/**
 * Normalized shape for every failure the API layer can produce, so callers
 * only ever handle one error type — never a raw AxiosError vs. a thrown
 * string vs. a network exception.
 */
export class ApiError extends Error {
  constructor(message, status = null, cause = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.cause = cause;
  }
}

/**
 * Converts any axios rejection into an ApiError. The backend consistently
 * replies with { ok: false, error: "..." } on failure, so that's the primary
 * message source; network/timeout failures (no response at all) get a
 * human-readable fallback instead of a raw axios message.
 */
export const toApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    const message = (data && (data.error || data.message)) || `Request failed with status ${status}`;
    return new ApiError(message, status, error);
  }
  if (error.request) {
    return new ApiError('Could not reach the server. Check your connection and try again.', null, error);
  }
  return new ApiError(error.message || 'Something went wrong.', null, error);
};
