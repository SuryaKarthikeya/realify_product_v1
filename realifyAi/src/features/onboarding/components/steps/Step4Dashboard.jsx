import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";

function Step4Dashboard() {
  const _navigate = useNavigate();
  const { setStep: _setStep } = useOnboardingStore();
  const [showToast, setShowToast] = useState(true);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowToast(false), 4000);
    return () => clearTimeout(timer);
  }, []);

  const handleSignIn = () => _navigate(ROUTES.WORKSPACE);

  return (
    <div className="max-w-lg mx-auto anim-fade-in mt-10">
      {/* Registration Complete Toast — rendered via portal to escape framer-motion transform context */}
      {showToast && createPortal(
        <div className="fixed top-4 right-4 z-[9999] flex items-center gap-2.5 px-4 py-3 bg-green-50 border border-green-200 rounded-xl shadow-md">
          <i className="fa-solid fa-circle-check text-green-500 text-sm"></i>
          <span className="text-sm font-medium text-green-700">Registration Complete</span>
        </div>,
        document.body
      )}

      <div className="mb-5 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Your account is ready. Sign in to continue.</h2>
        <p className="text-gray-500 text-sm">Sign in to your Realify dashboard to get started</p>
      </div>

      <div className="space-y-4">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
          <input
            type="email"
            placeholder="you@company.com"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
          />
        </div>

        {/* Password */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm font-medium text-gray-700">Password</label>
            <button onClick={() => { setShowForgot(true); setForgotSent(false); }} className="text-xs text-blue-600 hover:underline font-medium">Forgot password?</button>
          </div>
          <input
            type="password"
            placeholder="••••••••"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
          />
        </div>

        {/* Sign In CTA */}
        <button
          onClick={handleSignIn}
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm"
        >
          Sign In
        </button>
      </div>

      {/* Forgot Password Modal */}
      {showForgot && createPortal(
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
          <div className="bg-white rounded-2xl max-w-[440px] w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Reset Password</h3>
              <button onClick={() => setShowForgot(false)} className="text-gray-400 hover:text-gray-600 transition text-xl">
                <i className="fa-solid fa-times"></i>
              </button>
            </div>
            {forgotSent ? (
              <div className="text-center py-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                  <i className="fa-solid fa-envelope-circle-check text-2xl text-green-600"></i>
                </div>
                <p className="font-semibold text-gray-900 mb-1">Check your inbox</p>
                <p className="text-sm text-gray-500 mb-6">We've sent password reset instructions to your email.</p>
                <button onClick={() => setShowForgot(false)} className="w-full py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm">
                  Done
                </button>
              </div>
            ) : (
              <div>
                <div className="inline-flex items-center justify-center w-14 h-14 bg-gray-100 rounded-full mb-4">
                  <i className="fa-solid fa-key text-xl text-gray-700"></i>
                </div>
                <p className="text-sm text-gray-500 mb-5">Enter your email and we'll send you reset instructions.</p>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
                  <input type="email" placeholder="you@company.com" className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm" />
                </div>
                <button onClick={() => setForgotSent(true)} className="w-full py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm mb-3">
                  Send Reset Link <i className="fa-solid fa-paper-plane ml-2"></i>
                </button>
                <button onClick={() => setShowForgot(false)} className="w-full text-sm text-gray-500 hover:text-gray-700 font-medium transition">
                  <i className="fa-solid fa-arrow-left mr-1.5"></i>Back to Sign In
                </button>
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default Step4Dashboard;
