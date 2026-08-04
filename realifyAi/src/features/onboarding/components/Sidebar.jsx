import { Fragment } from "react";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";
import fullLogoDark from "@/assets/fulllogo_Dark.png";

const steps = [
  {
    num: 1,
    title: "Create your Account",
    desc: "Sign up with email, phone, or social login to get started on your intelligence journey.",
  },
  {
    num: 2,
    title: "Business Profile",
    desc: "Tell us about your store, revenue scale, and marketplace channels to personalize your experience.",
  },
  {
    num: 3,
    title: "Connect your Data",
    desc: "Upload reports or set up with a guided wizard to start seeing real insights immediately.",
  },
  {
    num: 4,
    title: "Welcome to your Dashboard",
    desc: "Your command center is ready with powerful tools and AI-driven insights.",
  },
];

function Sidebar() {
  const currentStep = useOnboardingStore((s) => s.step);
  const setStep = useOnboardingStore((s) => s.setStep);
  const setShowFAQ = useOnboardingStore((s) => s.setShowFAQ);

  const completedCount = Math.max(currentStep - 1, 0);

  const handleFAQClick = () => {
    setShowFAQ(true);
    setTimeout(() => {
      document.getElementById('faq-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <>
      {/* MOBILE — compact logo + horizontal step indicator (hidden sm and up) */}
      <div className="sm:hidden px-5 pt-5 pb-4 border-b border-gray-100">
        <img src={fullLogoDark} alt="Realify" className="h-6 object-contain mb-5" />
        <p className="text-center text-xs font-semibold text-gray-400 tracking-wide mb-3">
          Step {currentStep} of {steps.length}
        </p>
        <div className="flex items-center">
          {steps.map((step, index) => {
            const isActive = currentStep === step.num;
            const isCompleted = currentStep > step.num;
            return (
              <Fragment key={step.num}>
                <div
                  onClick={() => isCompleted && setStep(step.num)}
                  className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-semibold transition-colors ${isActive
                      ? 'bg-gray-900 text-white'
                      : isCompleted
                        ? 'bg-emerald-500 text-white cursor-pointer'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                >
                  {isCompleted
                    ? <i className="fa-solid fa-check text-[10px]" />
                    : step.num}
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-px mx-1.5 ${isCompleted ? 'bg-emerald-300' : 'bg-gray-200'}`} />
                )}
              </Fragment>
            );
          })}
        </div>
      </div>

      {/* DESKTOP/TABLET — full sidebar with step descriptions (unchanged, hidden below sm) */}
      <div className="hidden sm:flex w-[380px] min-w-[260px] bg-white border-r border-gray-200 px-8 py-6 flex-col justify-between h-full overflow-y-auto custom-scrollbar">
        <div>
          {/* Logo */}
          <div className="mb-6">
            <img src={fullLogoDark} alt="Realify" className="h-8 object-contain" />
          </div>

          {/* Progress text */}
          <p className="text-sm text-gray-500 mb-5">
            {completedCount} Out of 5 Steps Completed.
          </p>

          {/* Steps */}
          <div className="flex flex-col">
            {steps.map((step, index) => {
              const isActive = currentStep === step.num;
              const isCompleted = currentStep > step.num;

              return (
                <div key={step.num} className="flex gap-3">
                  {/* Left: circle + connector */}
                  <div className="flex flex-col items-center">
                    <div
                      onClick={() => isCompleted && setStep(step.num)}
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-semibold transition-colors ${isActive
                          ? 'bg-gray-900 text-white'
                          : isCompleted
                            ? 'bg-emerald-500 text-white cursor-pointer'
                            : 'bg-gray-100 text-gray-400'
                        }`}
                    >
                      {isCompleted
                        ? <i className="fa-solid fa-check text-xs" />
                        : step.num}
                    </div>
                    {index < steps.length - 1 && (
                      <div className={`w-px flex-1 my-1 ${isCompleted ? 'bg-emerald-300' : 'bg-gray-200'}`} style={{ minHeight: '24px' }} />
                    )}
                  </div>

                  {/* Right: text content */}
                  <div
                    className={`flex-1 mb-5 rounded-xl transition-colors ${isActive ? 'bg-gray-50 px-3 py-2' : 'pt-1'
                      }`}
                  >
                    <h3 className={`font-semibold text-sm leading-tight ${isActive ? 'text-gray-900' : isCompleted ? 'text-gray-600' : 'text-gray-400'
                      }`}>
                      {step.title}
                    </h3>
                    <p className={`text-xs leading-relaxed mt-1 ${isActive ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Support */}
        <div className="mt-5 pt-6 border-t border-gray-100">
          <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3">SUPPORT</p>
          <button onClick={handleFAQClick} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors text-left">
            <span>Need help ? <span className="text-blue-600 hover:underline">Our FAQs can help</span></span>
          </button>
        </div>
      </div>
    </>
  );
}

export default Sidebar;
