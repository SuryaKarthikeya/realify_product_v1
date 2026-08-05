import { useEffect, useRef, useState } from "react";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";
import { useAuthStore } from "@/store/useAuthStore";
import Sidebar from "@/features/onboarding/components/Sidebar";
import Step1Auth from "@/features/onboarding/components/steps/Step1Auth";
import Step2Business from "@/features/onboarding/components/steps/Step2Business";
import Step3Marketplace from "@/features/onboarding/components/steps/Step3Marketplace";
import Step4Dashboard from "@/features/onboarding/components/steps/Step4Dashboard";
import Step5Connect from "@/features/onboarding/components/steps/Step5Connect";
import ConnectionModal from "@/features/onboarding/components/modals/ConnectionModal";
import SigninModal from "@/features/onboarding/components/modals/SigninModal";
import { motion, AnimatePresence } from "framer-motion";
import { ROUTES } from '@/constants/routes';
import { ONBOARDING_FAQS } from "@/features/onboarding/data/faqData";

function OnboardingLayout() {
  const { step, setStep, activeModal, addConnectedMarketplace } = useOnboardingStore();
  const checkSession = useAuthStore((s) => s.checkSession);

  // Handle redirect params from OAuth callback and from Stripe Checkout
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const stepParam = urlParams.get('step');
    const statusParam = urlParams.get('status');
    const shopParam = urlParams.get('shop');
    const billingParam = urlParams.get('billing');

    if (statusParam === 'connected' && shopParam) {
      const platform = urlParams.get('platform') || 'shopify';

      // 🔹 Store connection data for future API calls
      localStorage.setItem('active_shop', shopParam);
      localStorage.setItem('active_platform', platform);

      // Keep legacy keys for backward compatibility if needed
      localStorage.setItem(`${platform}_shop`, shopParam);
      localStorage.setItem(`${platform}_status`, 'connected');

      addConnectedMarketplace(platform);

      if (stepParam) {
        setStep(parseInt(stepParam));
      }
      // Clean up URL without refreshing
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Signup (Step 1) redirects to Stripe Checkout; Checkout hands control
    // back here via success/cancel URL. On success the session cookie
    // already survived the round trip (set at signup, before Checkout even
    // started) — reconcile the store against it and resume where signup
    // left off, at Business Details.
    if (billingParam === 'success') {
      checkSession();
      setStep(2);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (billingParam === 'cancelled') {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [addConnectedMarketplace, setStep, checkSession]);

  const mainRef = useRef(null);

  useEffect(() => {
    mainRef.current?.scrollTo(0, 0);
  }, [step]);

  const renderStep = () => {
    switch (step) {
      case 1: return <Step1Auth />;
      case 2: return <Step2Business />;
      case 3: return <Step3Marketplace />;
      case 4: return <Step4Dashboard />;
      default: return <Step1Auth />;
    }
  };

  const progress = (step / 4) * 100;

  return (
    <div className="h-screen font-sans selection:bg-gray-200 selection:text-brand overflow-hidden">
      <div className="fixed top-0 left-0 w-full h-1.5 bg-gray-100 z-[60]">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
          className="h-full bg-brand shadow-[0_0_10px_rgba(56,56,56,0.5)]"
        />
      </div>

      <div className="flex flex-col sm:flex-row h-full pt-1.5">
        <Sidebar />

        <main ref={mainRef} className="flex-1 bg-white h-full flex flex-col px-5 py-6 sm:px-12 sm:py-6 lg:px-20 lg:py-14 overflow-y-auto custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="flex-1"
            >
              {renderStep()}
            </motion.div>
          </AnimatePresence>
          <FAQSection />
        </main>
      </div>

      <AnimatePresence>
        {activeModal === "connection" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ConnectionModal />
          </motion.div>
        )}
        {activeModal === "signin" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <SigninModal />
          </motion.div>
        )}
      </AnimatePresence>

      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes fade-in {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .anim-fade-in {
            animation: fade-in 0.5s ease-out forwards;
          }
          .anim-scale-up {
            animation: scale-up 0.3s ease-out forwards;
          }
          @keyframes scale-up {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
          }
          .custom-scrollbar::-webkit-scrollbar,
          .sidebar-scrollbar::-webkit-scrollbar {
            width: 6px;
          }
          .custom-scrollbar::-webkit-scrollbar-track,
          .sidebar-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
          }
          .custom-scrollbar:hover::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.2);
          }
          .sidebar-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
          }
          .sidebar-scrollbar:hover::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
          }
        `}} />
    </div>
  );
}

const ONBOARDING_STEPS = [
  { num: 1, title: "Create your Account", desc: "Sign up with email, phone, or social login to get started on your intelligence journey." },
  { num: 2, title: "Business Profile", desc: "Tell us about your store, revenue scale, and marketplace channels to personalize your experience." },
  { num: 3, title: "Connect your Data", desc: "Upload reports or set up with a guided wizard to start seeing real insights immediately." },
  { num: 4, title: "Welcome to your Workspace", desc: "Your command center is ready with powerful tools and AI-driven insights." },
];

const FAQSection = () => {
  const showFAQ = useOnboardingStore(s => s.showFAQ);
  const [openFAQs, setOpenFAQs] = useState({});
  const toggleFAQ = (i) => setOpenFAQs(prev => ({ ...prev, [i]: !prev[i] }));

  if (!showFAQ) return null;

  return (
    <div id="faq-section" className="w-full bg-[#F4F7FB] py-5 px-4 mt-6 flex flex-col items-center border-t border-gray-200">
      <div className="max-w-3xl w-full">
        {/* Eyebrow carries the section label, so it leads at a readable size and
            the headline sits a step below it rather than shouting. */}
        <div className="text-center mb-5">
          <div className="flex justify-center mb-5">
            <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3.5 py-1.5 text-[15px] font-bold uppercase tracking-[0.18em] text-blue-600 ring-1 ring-inset ring-blue-100">
              <i className="fa-regular fa-circle-question text-[14px]" />
              FAQ
            </span>
          </div>
          <h2 className="text-[22px] sm:text-[24px] font-bold text-gray-900 mb-3 tracking-tight">
            Questions? Answers.
          </h2>
          <p className="mx-auto max-w-xl text-[14px] leading-relaxed text-gray-500">
            What Realify does, how it works, and how to try it before you commit your data.
          </p>
        </div>
        
        <div className="w-full flex flex-col border-t border-gray-200/60">
          {ONBOARDING_FAQS.map((faq, i) => (
            <div key={i} className="border-b border-gray-200/60">
              <button 
                 onClick={() => toggleFAQ(i)}
                 className="w-full flex items-center justify-between py-5 text-left group"
              >
                <span className="text-[14.5px] font-bold text-gray-900 pr-6">{faq.q}</span>
                <span className="text-blue-600 font-bold text-2xl flex-shrink-0 opacity-80 group-hover:opacity-100 transition-opacity leading-none">
                  {openFAQs[i] ? '-' : '+'}
                </span>
              </button>
              <div className={`overflow-hidden transition-all duration-300 ${openFAQs[i] ? 'max-h-[800px] opacity-100 pb-5' : 'max-h-0 opacity-0'}`}>
                <p className="text-[14.5px] text-gray-600 leading-relaxed whitespace-pre-line">
                  {faq.a}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};



export default OnboardingLayout;
