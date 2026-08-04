import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { roleLandingRoutes } from "@/config/RoleLandingRoutes";
import { useAuthStore } from "@/store/useAuthStore";
import fullLogoLight from "@/assets/fulllogo_Lightv2.png";
import fullLogoDark from "@/assets/fulllogo_Dark.png";

function InviteLoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { inviteLogin } = useAuthStore();

  const invitedRole = searchParams.get("role");
  const [form, setForm] = useState({
    email: searchParams.get("email") || "",
    firstName: "",
    lastName: "",
    password: "",
    confirmPassword: "",
    agreed: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const getStrength = (pass) => {
    let s = 0;
    if (pass.length >= 8) s++;
    if (/[a-z]/.test(pass) && /[A-Z]/.test(pass)) s++;
    if (/[0-9]/.test(pass)) s++;
    if (/[^a-zA-Z0-9]/.test(pass)) s++;
    return s;
  };

  const strengthColors = ["bg-gray-200", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"];
  const strengthTexts = ["Weak", "Weak", "Fair", "Good", "Strong"];
  const strength = getStrength(form.password);

  const validate = () => {
    const errs = {};
    if (!form.email.trim()) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = "Enter a valid email address";
    if (!form.firstName.trim()) errs.firstName = "First name is required";
    if (!form.password) errs.password = "Password is required";
    else if (form.password.length < 8) errs.password = "Password must be at least 8 characters";
    if (!form.confirmPassword) errs.confirmPassword = "Please confirm your password";
    else if (form.password !== form.confirmPassword) errs.confirmPassword = "Passwords do not match";
    if (!form.agreed) errs.agreed = "You must agree to continue";
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    // Store role then authenticate — order matters so ProtectedRoute sees both.
    localStorage.setItem("userRole", invitedRole || "viewer");
    inviteLogin({
      email: form.email,
      name: `${form.firstName} ${form.lastName}`.trim(),
      role: invitedRole || "viewer",
    });

    navigate(roleLandingRoutes[invitedRole] || ROUTES.WORKSPACE);
  };

  const handleChange = (field) => (e) => {
    const value = field === "agreed" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const inputClass = (field) =>
    `w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-1 transition text-sm ${errors[field]
      ? "border-red-400 focus:border-red-500 focus:ring-red-400"
      : "border-gray-300 focus:border-gray-900 focus:ring-gray-900"
    }`;

  return (
    <div className="h-screen flex font-sans overflow-hidden">
      {/* ── Left brand panel ── */}
      <div className="hidden lg:flex w-[380px] flex-shrink-0 bg-gray-900 flex-col justify-between px-10 py-8">
        <img src={fullLogoLight} alt="Realify" className="h-9 object-contain object-left" />

        <div>
          <h2 className="text-3xl font-bold text-white leading-snug mb-4">
            Welcome to<br />Realify Intel
          </h2>

          <div className="mt-6 space-y-4">
            {[
              { icon: "fa-chart-line", label: "Sales Intelligence" },
              { icon: "fa-boxes-stacked", label: "Inventory Tracking" },
              { icon: "fa-bullseye", label: "Ads Performance" },
            ].map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <i className={`fa-solid ${icon} text-cb-400 text-xs`} />
                </div>
                <span className="text-sm text-gray-300">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-gray-600">© 2024 Realify. All rights reserved.</p>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center bg-slate-50 overflow-y-auto py-6 px-4">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex justify-center mb-5 lg:hidden">
            <img src={fullLogoDark} alt="Realify" className="h-8 object-contain" />
          </div>

          <div className="mb-5">
            <h1 className="text-2xl font-bold text-gray-900">Login Page</h1>
            <p className="text-sm text-gray-500 mt-1">Complete your profile to access your dashboard</p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  First Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.firstName}
                  onChange={handleChange("firstName")}
                  placeholder="John"
                  className={inputClass("firstName")}
                />
                {errors.firstName && <p className="text-xs text-red-500 mt-1">{errors.firstName}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Last Name</label>
                <input
                  type="text"
                  value={form.lastName}
                  onChange={handleChange("lastName")}
                  placeholder="Doe"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={form.email}
                onChange={handleChange("email")}
                placeholder="you@company.com"
                className={inputClass("email")}
              />
              {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={handleChange("password")}
                  placeholder="Create a strong password"
                  className={`${inputClass("password")} pr-12`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <i className={`fa-solid ${showPassword ? "fa-eye-slash" : "fa-eye"}`} />
                </button>
              </div>
              {form.password && (
                <div className="mt-2">
                  <div className="flex space-x-1 mb-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`flex-1 h-1 rounded transition-colors duration-300 ${i <= strength ? strengthColors[strength] : "bg-gray-200"
                          }`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-gray-500">Password strength: {strengthTexts[strength]}</p>
                </div>
              )}
              {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password}</p>}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Confirm Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={form.confirmPassword}
                  onChange={handleChange("confirmPassword")}
                  placeholder="Re-enter your password"
                  className={`${inputClass("confirmPassword")} pr-12`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <i className={`fa-solid ${showConfirmPassword ? "fa-eye-slash" : "fa-eye"}`} />
                </button>
              </div>
              {form.confirmPassword && !errors.confirmPassword && (
                <p className={`text-xs mt-1 ${form.password === form.confirmPassword ? "text-green-600" : "text-red-500"}`}>
                  {form.password === form.confirmPassword ? "Passwords match" : "Passwords do not match"}
                </p>
              )}
              {errors.confirmPassword && (
                <p className="text-xs text-red-500 mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            {/* I Agree */}
            <div>
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="agreed"
                  checked={form.agreed}
                  onChange={handleChange("agreed")}
                  className="mt-0.5 w-4 h-4 accent-gray-900 border-gray-300 rounded focus:ring-gray-900 cursor-pointer"
                />
                <label htmlFor="agreed" className="text-sm text-gray-600 cursor-pointer">
                  I agree to the{" "}
                  <Link
                    to={ROUTES.TERMS_OF_SERVICE}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cb-600 hover:underline font-medium"
                  >
                    Terms of Service
                  </Link>
                  {" "}and{" "}
                  <Link
                    to={ROUTES.PRIVACY_POLICY}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cb-600 hover:underline font-medium"
                  >
                    Privacy Policy
                  </Link>
                </label>
              </div>
              {errors.agreed && (
                <p className="text-xs text-red-500 mt-1 ml-7">{errors.agreed}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="w-full py-3.5 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 active:bg-gray-950 transition text-sm mt-2"
            >
              Login <i className="fa-solid fa-arrow-right ml-2" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default InviteLoginPage;
