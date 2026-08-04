/**
 * Public API of the Workspace feature — the application's primary surface.
 *
 * Workspace presents five marketplace domains (Sales, Margin, Cash, Inventory,
 * Ads) in two view modes: AI View and Dashboard View. Route targets are
 * resolved directly from `pages/` by the router so each keeps its own chunk;
 * everything else crossing into Workspace comes through this file.
 */
export {
  DOMAIN_SEGMENTS,
  DEFAULT_DOMAIN,
  isDomainSegment,
  isWorkspacePath,
  workspacePath,
  dashboardPath,
  toDomainKey,
  WORKSPACE_PATHS,
} from '@/features/workspace/workspaceRoutes';
