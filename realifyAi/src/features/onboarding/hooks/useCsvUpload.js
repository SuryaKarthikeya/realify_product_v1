import { useState } from 'react';
import { identifyReports, commitReports } from '@/services/onboardingService';

/**
 * Drives the CSV upload step: identify() previews real recognition without
 * persisting anything (the live "green-check" checklist), commit() runs the
 * report-aware ingestion engine and provisions the tenant. Separate loading
 * flags per action since a user can re-identify (drop more files) while a
 * previous commit dialog is still open. Local state, mirroring
 * useShopProfile.js — no global request-state manager in this codebase.
 */
export const useCsvUpload = () => {
  const [identifying, setIdentifying] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [error, setError] = useState(null);

  const identify = async (files) => {
    setIdentifying(true);
    setError(null);
    try {
      return await identifyReports(files);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIdentifying(false);
    }
  };

  const commit = async (files, country) => {
    setCommitting(true);
    setError(null);
    try {
      return await commitReports(files, country);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setCommitting(false);
    }
  };

  return { identify, commit, identifying, committing, error };
};
