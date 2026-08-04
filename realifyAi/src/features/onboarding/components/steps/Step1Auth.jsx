import { useState } from "react";
import { Link } from "react-router-dom";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";
import { useSignup } from "@/features/onboarding/hooks/useSignup";
import { ROUTES } from "@/constants/routes";

function Step1Auth() {
  const setActiveModal = useOnboardingStore((s) => s.setActiveModal);
  const formValues = useOnboardingStore((s) => s.formValues);
  const updateFormValues = useOnboardingStore((s) => s.updateFormValues);
  const { signup, loading, error: signupError } = useSignup();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [formError, setFormError] = useState("");

  const getStrength = (pass) => {
    let strength = 0;
    if (pass.length >= 8) strength++;
    if (/[a-z]/.test(pass) && /[A-Z]/.test(pass)) strength++;
    if (/[0-9]/.test(pass)) strength++;
    if (/[^a-zA-Z0-9]/.test(pass)) strength++;
    return strength;
  };

  const strength = getStrength(password);
  const strengthColors = ["bg-gray-200", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"];
  const strengthTexts = ["Weak", "Weak", "Fair", "Good", "Strong"];

  const handleSignup = async () => {
    setFormError("");

    if (!formValues.firstName.trim() || !formValues.lastName.trim() || !formValues.email.trim()) {
      setFormError("First name, last name and email are required.");
      return;
    }
    if (password.length < 6) {
      setFormError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }
    if (!agreedToTerms) {
      setFormError("Please agree to the Terms of Service and Privacy Policy.");
      return;
    }

    try {
      // The account is created and signed in (session cookie set) before
      // Checkout even starts — Stripe hands control back to this SPA via
      // the success/cancel URL, which OnboardingLayout picks up to resume
      // onboarding at Step 2.
      const data = await signup({
        name: `${formValues.firstName.trim()} ${formValues.lastName.trim()}`,
        email: formValues.email.trim(),
        password,
        confirmPassword,
      });
      window.location.href = data.checkout_url;
    } catch {
      // signupError from the hook already surfaces the message below.
    }
  };

  return (
    <div className="max-w-lg mx-auto anim-fade-in">
      <div className="mb-5 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Create Your Account</h2>
        <p className="text-gray-500">Choose your preferred sign-up method to get started</p>
      </div>

      <div className="space-y-5">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">First Name</label>
                <input
                  type="text"
                  placeholder="John"
                  value={formValues.firstName}
                  onChange={(e) => updateFormValues({ firstName: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Last Name</label>
                <input
                  type="text"
                  placeholder="Doe"
                  value={formValues.lastName}
                  onChange={(e) => updateFormValues({ lastName: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
              <input
                type="email"
                placeholder="you@company.com"
                value={formValues.email}
                onChange={(e) => updateFormValues({ email: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
                <button
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <i className={`fa-solid ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                </button>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                <div className="flex space-x-1 mb-1">
                  {[1, 2, 3, 4].map(idx => (
                    <div key={idx} className={`flex-1 h-1 rounded transition-colors duration-300 ${idx <= strength ? strengthColors[strength] : 'bg-gray-200'}`}></div>
                  ))}
                </div>
                Password strength: {strengthTexts[strength]}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm Password</label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
                <button
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <i className={`fa-solid ${showConfirmPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                </button>
              </div>
              {confirmPassword && (
                <p className={`text-xs mt-1 ${password === confirmPassword ? 'text-green-600' : 'text-red-500'}`}>
                  {password === confirmPassword ? 'Passwords match' : 'Passwords do not match'}
                </p>
              )}
            </div>

            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="terms"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                className="mt-0.5 w-4 h-4 text-gray-900 border-gray-300 rounded focus:ring-gray-900"
              />
              <label htmlFor="terms" className="text-sm text-gray-600">
                I agree to the{' '}
                <Link to={ROUTES.TERMS_OF_SERVICE} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">Terms of Service</Link>
                {' '}and{' '}
                <Link to={ROUTES.PRIVACY_POLICY} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">Privacy Policy</Link>
              </label>
            </div>

            {(formError || signupError) && (
              <p className="text-sm text-red-500 text-center">{formError || signupError}</p>
            )}

            <button
              onClick={handleSignup}
              disabled={loading}
              className="w-full py-3.5 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><i className="fa-solid fa-circle-notch fa-spin mr-2"></i>Creating your account...</>
              ) : (
                <>Continue <i className="fa-solid fa-arrow-right ml-2"></i></>
              )}
            </button>
          </div>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 border-t border-gray-200"></div>
          <span className="text-xs text-gray-400">or continue with</span>
          <div className="flex-1 border-t border-gray-200"></div>
        </div>

        {/* Social icons */}
        <div className="flex items-center justify-center gap-6">
          <button className="w-12 h-12 flex items-center justify-center border border-gray-200 rounded-xl hover:bg-gray-50 transition">
            <i className="fa-brands fa-google text-xl text-red-500"></i>
          </button>
          <button className="w-12 h-12 flex items-center justify-center border border-gray-200 rounded-xl hover:bg-gray-50 transition">
            <i className="fa-brands fa-apple text-xl text-gray-900"></i>
          </button>
          <button className="w-12 h-12 flex items-center justify-center border border-gray-200 rounded-xl hover:bg-gray-50 transition">
            <i className="fa-brands fa-meta text-xl text-blue-600"></i>
          </button>
        </div>

        <p className="text-center text-sm text-gray-500">
          Already have an account?{' '}
          <button onClick={() => setActiveModal("signin")} className="text-gray-900 hover:underline font-semibold">Sign in</button>
        </p>
      </div>
    </div>
  );
}

export default Step1Auth;
