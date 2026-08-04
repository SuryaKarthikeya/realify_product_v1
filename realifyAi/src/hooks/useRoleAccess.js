import { rolePermissions } from "@/config/RolePermission";
import { roleLandingRoutes } from "@/config/RoleLandingRoutes";
import { ROUTES } from "@/constants/routes";

/**
 * Returns role-based access helpers for the current user.
 *
 * Usage:
 *   const { role, canAccess, landingRoute, isAdmin } = useRoleAccess();
 */
const useRoleAccess = () => {
  const role = localStorage.getItem("userRole") || "admin";
  const allowedRoutes = rolePermissions[role] || [];
  const landingRoute = roleLandingRoutes[role] || ROUTES.WORKSPACE;

  /**
   * Returns true if the current role is allowed to access the given path.
   * Supports prefix matching: /intel grants access to /intel/sales, etc.
   */
  const canAccess = (path) => {
    if (!path) return false;
    return allowedRoutes.some(
      (allowed) =>
        path === allowed || path.startsWith(allowed + "/")
    );
  };

  /**
   * Returns true if the role has an explicit permission entry for the given path
   * (exact match only — useful for sidebar visibility checks).
   */
  const hasPermission = (path) => allowedRoutes.includes(path);

  return {
    role,
    allowedRoutes,
    landingRoute,
    canAccess,
    hasPermission,
    isAdmin:            role === "admin",
    isAnalyst:          role === "analyst",
    isViewer:           role === "viewer",
    isInventoryPlanner: role === "inventory-planner",
    isSalesManager:     role === "sales-manager",
  };
};

export default useRoleAccess;
