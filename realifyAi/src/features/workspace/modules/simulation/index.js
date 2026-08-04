/**
 * Public API of the Simulation module.
 *
 * Workspace pages embed the simulate dialog and its inline content; the route
 * target is resolved directly by the router. Everything else in this module —
 * the projection maths, the tab configuration — is internal.
 */
export { default as SimulateModal, SimulateContent } from '@/features/workspace/modules/simulation/components/SimulateModal';
