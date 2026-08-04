import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { ROUTES } from '@/constants/routes';
import { rolePermissions } from "@/config/RolePermission";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  // Default to "admin" so existing authenticated users without a role aren't locked out.
  const role = localStorage.getItem("userRole") || "admin";
  const userAllowedRoutes = rolePermissions[role] || [];

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.ONBOARDING} state={{ from: location }} replace />;
  }

  // Use startsWith so sub-routes like /intel/sales match the base /intel permission.
  const hasAccess = userAllowedRoutes.some(
    (allowed) =>
      location.pathname === allowed ||
      location.pathname.startsWith(allowed + '/')
  );

  if (!hasAccess) {
    return <Navigate to={ROUTES.UNAUTHORIZED} replace />;
  }

  return children;
};

export default ProtectedRoute;
