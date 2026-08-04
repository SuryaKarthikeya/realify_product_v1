import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";

function ConnectionModal() {
  const { currentMarketplace, setActiveModal, addConnectedMarketplace } = useOnboardingStore();
  const [step, setStep] = useState(1);
  const [syncProgress, setSyncProgress] = useState(0);
  const [shopName, setShopName] = useState("");

  useEffect(() => {
    if (step === 5) {
      const interval = setInterval(() => {
        setSyncProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 10;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [step]);

  if (!currentMarketplace) return null;

  const handleGrantPermissions = () => {
    setStep(4);
    // Simulate connection steps
    setTimeout(() => {
      setStep(5);
    }, 3000);
  };

  const handleShopifyConnect = () => {
    if (!shopName) return;

    let sanitizedShop = shopName.trim();
    try {
      if (sanitizedShop.includes('://')) {
        const url = new URL(sanitizedShop);
        sanitizedShop = url.hostname;
      } else {
        sanitizedShop = sanitizedShop.split('/')[0];
      }
    } catch {
      sanitizedShop = sanitizedShop.replace(/^https?:\/\//, '').replace(/\/+$/, '');
    }

    const backendUrl = (import.meta.env.VITE_BACKEND_URL || "http://localhost:8000").replace(/\/+$/, "");
    window.location.href = `${backendUrl}/api/v1/auth/shopify?shop=${sanitizedShop}`;
  };

  const handleWooCommerceConnect = () => {
    if (!shopName) return;
    
    let sanitizedShop = shopName.trim();
    if (!sanitizedShop.startsWith('http')) {
      sanitizedShop = `https://${sanitizedShop}`;
    }

    const backendUrl = (import.meta.env.VITE_BACKEND_URL || "http://localhost:8000").replace(/\/+$/, "");
    window.location.href = `${backendUrl}/api/v1/auth/woocommerce?shop_url=${encodeURIComponent(sanitizedShop)}`;
  };

  const handleFinish = () => {
    addConnectedMarketplace(currentMarketplace.id);
    setActiveModal(null);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
      <div className="bg-white rounded-2xl max-w-[600px] w-full p-6 shadow-2xl anim-scale-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-2xl font-bold text-gray-900">Connect {currentMarketplace.name}</h3>
          <button onClick={() => setActiveModal(null)} className="text-gray-400 hover:text-gray-600 transition text-2xl">
            <i className="fa-solid fa-times"></i>
          </button>
        </div>

        {step === 1 && (
          <div className="anim-fade-in text-center">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 ${currentMarketplace.color}`}>
              <i className={`${currentMarketplace.icon} text-4xl ${currentMarketplace.iconColor}`}></i>
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-2">Connect to {currentMarketplace.name}</h4>
            <p className="text-gray-600 mb-5">We'll securely connect to your account to sync data</p>

            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 mb-5 text-left">
              <div className="flex items-start">
                <i className="fa-solid fa-shield-halved text-blue-600 text-xl mr-3 mt-1"></i>
                <div>
                  <h5 className="font-semibold text-gray-900 mb-1">Secure Connection</h5>
                  <p className="text-sm text-gray-700">We use industry-standard OAuth 2.0 encryption. We never store your password.</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setStep(2)}
              className="w-full py-4 bg-brand text-white font-semibold rounded-xl hover:bg-brand-hover transition shadow-lg"
            >
              Continue to Authorization <i className="fa-solid fa-arrow-right ml-2"></i>
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="anim-fade-in">
            <div className="text-center mb-5">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                <i className={currentMarketplace.id === 'shopify' ? "fa-brands fa-shopify text-2xl text-green-600" : currentMarketplace.id === 'woocommerce' ? "fa-brands fa-wordpress text-2xl text-purple-600" : "fa-solid fa-key text-2xl text-indigo-600"}></i>
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-2">
                {['shopify', 'woocommerce'].includes(currentMarketplace.id) ? "Enter Store URL" : "Enter Your Credentials"}
              </h4>
              <p className="text-gray-600">
                {['shopify', 'woocommerce'].includes(currentMarketplace.id) ? `Enter your ${currentMarketplace.name} store URL to continue` : "Sign in to authorize Realify to access your data"}
              </p>
            </div>

            {['shopify', 'woocommerce'].includes(currentMarketplace.id) ? (
              <div className="space-y-4 mb-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Store URL</label>
                  <input
                    type="text"
                    value={shopName}
                    onChange={(e) => setShopName(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition"
                    placeholder={currentMarketplace.id === 'shopify' ? "your-store.myshopify.com" : "https://your-woocommerce-store.com"}
                  />
                  <p className="mt-2 text-xs text-gray-500 italic">
                    {currentMarketplace.id === 'shopify' ? "Example: my-store.myshopify.com" : "Example: https://mystore.com"}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4 mb-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email or Username</label>
                  <input type="text" className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition" placeholder="Enter your email" />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                  <input type="password" className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-brand outline-none transition" placeholder="Enter your password" />
                </div>
              </div>
            )}

            <button
              onClick={
                currentMarketplace.id === 'shopify' ? handleShopifyConnect : 
                currentMarketplace.id === 'woocommerce' ? handleWooCommerceConnect : 
                () => setStep(3)
              }
              disabled={['shopify', 'woocommerce'].includes(currentMarketplace.id) && !shopName}
              className="w-full py-4 bg-brand text-white font-semibold rounded-xl hover:bg-brand-hover transition mb-3 shadow-lg disabled:opacity-50"
            >
              {['shopify', 'woocommerce'].includes(currentMarketplace.id) ? "Connect Store" : "Authorize Access"} <i className="fa-solid fa-arrow-right ml-2"></i>
            </button>
            <button onClick={() => setStep(1)} className="w-full py-3 text-gray-500 hover:text-gray-700 font-medium transition">
              <i className="fa-solid fa-arrow-left mr-2"></i>Back
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="anim-fade-in">
            <div className="text-center mb-5">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <i className="fa-solid fa-lock text-2xl text-purple-600"></i>
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-2">Grant Permissions</h4>
              <p className="text-gray-600">Realify needs access to the following data</p>
            </div>

            <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-5 mb-5 space-y-4">
              {[
                { title: "Read Sales Data", desc: "Access order history and revenue metrics" },
                { title: "Read Product Information", desc: "Access SKU details and inventory levels" },
                { title: "Read Performance Metrics", desc: "Access analytics and reporting data" },
              ].map((p, i) => (
                <div key={i} className="flex items-start">
                  <i className="fa-solid fa-circle-check text-green-600 mt-1 mr-3"></i>
                  <div>
                    <div className="font-semibold text-gray-900">{p.title}</div>
                    <div className="text-xs text-gray-600">{p.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleGrantPermissions}
              className="w-full py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition mb-3 shadow-lg"
            >
              Grant Access <i className="fa-solid fa-arrow-right ml-2"></i>
            </button>
            <button onClick={() => setStep(2)} className="w-full py-3 text-gray-500 hover:text-gray-700 font-medium transition">
              <i className="fa-solid fa-arrow-left mr-2"></i>Back
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="anim-fade-in text-center py-5">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-amber-50 rounded-full mb-6">
              <i className="fa-solid fa-spinner fa-spin text-4xl text-amber-500"></i>
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-2">Connecting...</h4>
            <p className="text-gray-600 mb-6">Please wait while we establish a secure connection</p>

            <div className="space-y-3 text-left">
              {[
                { label: "Authenticating credentials", status: "done" },
                { label: "Verifying permissions", status: "loading" },
                { label: "Syncing initial data", status: "pending" },
              ].map((s, i) => (
                <div key={i} className={`flex items-center justify-between p-4 bg-gray-50 rounded-xl ${s.status === 'pending' ? 'opacity-40' : ''}`}>
                  <span className="text-sm font-medium text-gray-700">{s.label}</span>
                  {s.status === 'done' ? <i className="fa-solid fa-circle-check text-green-600"></i> : s.status === 'loading' ? <i className="fa-solid fa-spinner fa-spin text-brand"></i> : <i className="fa-solid fa-clock text-gray-400"></i>}
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="anim-fade-in text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6 shadow-inner">
              <i className="fa-solid fa-check text-4xl text-green-600"></i>
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-2">Successfully Connected!</h4>
            <p className="text-gray-600 mb-5">Your {currentMarketplace.name} account is now syncing</p>

            <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 mb-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Initial sync progress</span>
                <span className="text-sm font-bold text-green-600">{syncProgress}%</span>
              </div>
              <div className="w-full bg-green-200 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-green-600 h-full transition-all duration-300"
                  style={{ width: `${syncProgress}%` }}
                ></div>
              </div>
            </div>

            <button
              onClick={handleFinish}
              className="w-full py-4 bg-brand text-white font-semibold rounded-xl hover:bg-brand-hover transition shadow-lg"
            >
              Done <i className="fa-solid fa-check ml-2"></i>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ConnectionModal;
