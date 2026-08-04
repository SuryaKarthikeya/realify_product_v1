import { useNavigate } from "react-router-dom";
import { roleLandingRoutes } from "@/config/RoleLandingRoutes";
import { ROUTES } from "@/constants/routes";

const Unauthorized = () => {
  const navigate = useNavigate();
  const role = localStorage.getItem("userRole");
  const landingRoute = roleLandingRoutes[role] || ROUTES.WORKSPACE;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#030712] px-4">
      <div className="text-center max-w-sm">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mx-auto mb-6">
          <i className="fa-solid fa-shield-xmark text-2xl text-red-500 dark:text-red-400" />
        </div>

        {/* Heading */}
        <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
          Access Denied
        </h1>
        <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">
          You don&apos;t have permission to view this page.
          <br />
          Contact your admin if you think this is a mistake.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => navigate(landingRoute)}
            className="w-full sm:w-auto px-6 py-2.5 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl text-sm font-semibold hover:bg-gray-700 dark:hover:bg-slate-200 transition-all"
          >
            Back to Dashboard
          </button>
          <button
            onClick={() => navigate(-1)}
            className="w-full sm:w-auto px-6 py-2.5 border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-300 rounded-xl text-sm font-semibold hover:bg-gray-50 dark:hover:bg-slate-800 transition-all"
          >
            Go Back
          </button>
        </div>

        {/* Role badge */}
        {role && (
          <p className="mt-5 text-xs text-gray-400 dark:text-slate-500">
            Signed in as <span className="font-medium capitalize">{role.replace(/-/g, " ")}</span>
          </p>
        )}
      </div>
    </div>
  );
};

export default Unauthorized;
