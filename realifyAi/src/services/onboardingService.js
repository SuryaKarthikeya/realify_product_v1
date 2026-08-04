import { identityClient } from '@/services/httpClient';
import { API_PATHS } from '@/services/endpoints';
import { downloadFile } from '@/utils/downloadFile';

/**
 * Builds a multipart form from raw File objects. The backend (report_ingest /
 * onboard.py) iterates every multipart field looking for a filename — it
 * doesn't care about field names — so every file goes under the same 'files'
 * key. Do NOT set a Content-Type header when sending this: the browser must
 * generate the multipart boundary itself, which axios only does when it owns
 * the header.
 */
const buildFilesForm = (files, extra = {}) => {
  const form = new FormData();
  files.forEach((file) => form.append('files', file));
  Object.entries(extra).forEach(([key, value]) => {
    if (value !== undefined && value !== null) form.append(key, value);
  });
  return form;
};

/**
 * Recognizes dropped files WITHOUT persisting anything: per-file report
 * type, row/month counts, and any same-type overlaps or conflicts. This
 * drives the live "green-check" recognition checklist while the user is
 * still deciding what to upload.
 */
export const identifyReports = async (files) => {
  const { data } = await identityClient.post(API_PATHS.ONBOARDING.IDENTIFY, buildFilesForm(files));
  return data;
};

/**
 * Commits the dropped files through the report-aware ingestion engine:
 * detects channels, dedups against any previous upload, runs the pipeline
 * synchronously, and marks the tenant provisioned. Resolves only once the
 * dashboard is actually ready — no status polling needed here, unlike the
 * synthetic-data onboarding path (/api/onboard + /api/onboard/status).
 */
export const commitReports = async (files, country) => {
  const { data } = await identityClient.post(
    API_PATHS.ONBOARDING.COMMIT_REPORTS,
    buildFilesForm(files, { country })
  );
  return data; // { ok, provisioned, skus_written }
};

/**
 * The engine-backed channel + report catalog — the same checklist the real
 * upload uses, just without any files identified yet. Drives the checklist's
 * pre-upload empty state so it shows real report types instead of a blank
 * list until the first drop.
 */
export const getIngestCatalog = async () => {
  const { data } = await identityClient.get(API_PATHS.ONBOARDING.CATALOG);
  return data; // { channels: [{ channel, label, active, reports }] }
};

/** Fetches and immediately downloads the COGS CSV template for the tenant's currency. */
export const downloadCogsTemplate = async () => {
  const { data } = await identityClient.get(API_PATHS.ONBOARDING.COGS_TEMPLATE, {
    responseType: 'text',
  });
  downloadFile(data, 'realify_cogs_template.csv', 'text/csv;charset=utf-8;');
  return true;
};
