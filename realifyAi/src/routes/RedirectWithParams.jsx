import React from 'react';
import { Navigate, useParams, useLocation } from 'react-router-dom';

/**
 * Redirects a legacy URL to its canonical equivalent, carrying route params,
 * query string and hash across.
 *
 * `<Navigate to="/a/:id">` would send the literal `:id`, so param-bearing
 * redirects need this instead.
 */
const RedirectWithParams = ({ to }) => {
  const params = useParams();
  const { search, hash } = useLocation();
  const target = to.replace(/:(\w+)/g, (_match, key) => params[key] ?? '');
  return <Navigate to={`${target}${search}${hash}`} replace />;
};

export default RedirectWithParams;
