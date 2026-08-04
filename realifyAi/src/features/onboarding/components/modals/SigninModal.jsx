import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";
import { useLogin } from "@/features/auth/hooks/useLogin";
import { ROUTES } from "@/constants/routes";

function SigninModal() {
  const { setActiveModal } = useOnboardingStore();
  const { login, loading, error: loginError } = useLogin();
  const navigate = useNavigate();
  const [tab, setTab] = useState("email");
  const [mode, setMode] = useState("login"); // login, forgot, otp-verify
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await login(email, password);
      setActiveModal(null);
      if (data.redirect) {
        // Agency members land on the (non-SPA) console — a full navigation,
        // not a router push.
        window.location.href = data.redirect;
        return;
      }
      navigate(data.provisioned ? ROUTES.REVENUE : ROUTES.ONBOARDING);
    } catch {
      // loginError from the hook already surfaces the message below.
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
      <div className="bg-white rounded-2xl max-w-[500px] w-full p-6 shadow-2xl anim-scale-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-2xl font-bold text-gray-900">
            {mode === 'login' ? 'Sign In to Realify' : mode === 'forgot' ? 'Reset Password' : 'Verify Code'}
          </h3>
          <button onClick={() => setActiveModal(null)} className="text-gray-400 hover:text-gray-600 transition text-2xl">
            <i className="fa-solid fa-times"></i>
          </button>
        </div>

        {mode === 'login' && (
          <div className="anim-fade-in space-y-6">
            <div className="grid grid-cols-2 gap-4 mb-6">
              <button className="flex items-center justify-center px-6 py-3 border-2 border-gray-300 rounded-xl hover:border-brand hover:bg-brand-subtle/10 transition font-medium text-gray-700">
                <i className="fa-brands fa-google text-xl mr-3 text-red-500"></i> Google
              </button>
              <button className="flex items-center justify-center px-6 py-3 border-2 border-gray-300 rounded-xl hover:border-brand hover:bg-brand-subtle/10 transition font-medium text-gray-700">
                <i className="fa-brands fa-apple text-xl mr-3 text-gray-900"></i> Apple
              </button>
            </div>

            <div className="flex items-center">
              <div className="flex-1 border-t border-gray-300"></div>
              <span className="px-4 text-gray-400 text-sm">or continue with</span>
              <div className="flex-1 border-t border-gray-300"></div>
            </div>

            <div className="flex space-x-3">
              <button 
                onClick={() => setTab("email")}
                className={`flex-1 py-3 rounded-lg font-medium transition ${tab === 'email' ? 'bg-brand text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                <i className="fa-solid fa-envelope mr-2"></i>Email
              </button>
              <button 
                onClick={() => setTab("otp")}
                className={`flex-1 py-3 rounded-lg font-medium transition ${tab === 'otp' ? 'bg-brand text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                <i className="fa-solid fa-mobile-screen mr-2"></i>OTP
              </button>
            </div>

            {tab === 'email' ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    required
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      required
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition"
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                      <i className={`fa-solid ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center cursor-pointer">
                    <input type="checkbox" className="w-4 h-4 text-brand border-gray-300 rounded" />
                    <span className="ml-2 text-gray-600">Remember me</span>
                  </label>
                  <button type="button" onClick={() => setMode('forgot')} className="text-brand font-medium hover:underline">Forgot password?</button>
                </div>
                {loginError && (
                  <p className="text-sm text-red-500 text-center -mt-1">{loginError}</p>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 bg-brand text-white font-bold rounded-xl shadow-lg hover:bg-brand-hover transition disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><i className="fa-solid fa-circle-notch fa-spin mr-2"></i>Signing in...</>
                  ) : (
                    <>Sign In <i className="fa-solid fa-arrow-right ml-2"></i></>
                  )}
                </button>
              </form>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email or Phone</label>
                  <input type="text" placeholder="Enter email or phone number" className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition" />
                </div>
                <button onClick={() => setMode('otp-verify')} className="w-full py-4 bg-brand text-white font-bold rounded-xl shadow-lg hover:bg-brand-hover transition">
                  Send OTP <i className="fa-solid fa-paper-plane ml-2"></i>
                </button>
              </div>
            )}
          </div>
        )}

        {mode === 'forgot' && (
          <div className="anim-fade-in text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-6">
              <i className="fa-solid fa-key text-2xl text-brand"></i>
            </div>
            <p className="text-gray-600 mb-5">Enter your email and we'll send you reset instructions</p>
            <div className="text-left mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
              <input type="email" placeholder="you@company.com" className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition" />
            </div>
            <button onClick={() => setMode('login')} className="w-full py-4 bg-brand text-white font-bold rounded-xl shadow-lg mb-4 hover:bg-brand-hover transition">
              Send Reset Link <i className="fa-solid fa-paper-plane ml-2"></i>
            </button>
            <button onClick={() => setMode('login')} className="text-gray-500 font-medium hover:text-gray-700">
              <i className="fa-solid fa-arrow-left mr-2"></i>Back to Sign In
            </button>
          </div>
        )}

        {mode === 'otp-verify' && (
          <div className="anim-fade-in text-center">
             <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-6">
              <i className="fa-solid fa-mobile-screen text-2xl text-green-600"></i>
            </div>
            <p className="text-gray-600 mb-5">We sent a 6-digit code to your contact</p>
            <div className="flex justify-center mb-5">
              <input 
                type="text" 
                maxLength="6" 
                placeholder="000000"
                className="w-full max-w-[200px] text-center text-3xl tracking-[10px] font-bold py-4 border-2 border-gray-300 rounded-xl focus:border-brand outline-none" 
              />
            </div>
            <button onClick={handleLogin} className="w-full py-4 bg-brand text-white font-bold rounded-xl shadow-lg mb-4 hover:bg-brand-hover transition">
              Verify & Sign In <i className="fa-solid fa-check ml-2"></i>
            </button>
            <button onClick={() => setMode('login')} className="text-gray-500 font-medium hover:text-gray-700">
              <i className="fa-solid fa-arrow-left mr-2"></i>Back to Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default SigninModal;
