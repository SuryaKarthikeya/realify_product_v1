import { useState } from "react";
import { useOnboardingStore } from "@/features/onboarding/store/useOnboardingStore";

// `min` is the lower bound of each bucket, so a typed figure can find its range.
const gmvRanges = [
  { label: 'Less than $100K', min: 0 },
  { label: '$100K – $500K', min: 100000 },
  { label: '$500K – $1M', min: 500000 },
  { label: '$1M – $5M', min: 1000000 },
  { label: '$5M – $10M', min: 5000000 },
  { label: '$10M+', min: 10000000 },
];

const rangeForAmount = (amount) =>
  gmvRanges.reduce((match, range) => (amount >= range.min ? range : match), gmvRanges[0]);

const initialFocusItems = [
  { id: 'margin', label: 'Margin Optimization', desc: 'Focusing on profitability and unit economics' },
  { id: 'inventory', label: 'Inventory Velocity', desc: 'Improving turnover rates and stock management' },
  { id: 'expansion', label: 'Market Expansion', desc: 'Launching new products or entering regions' },
];

function Step2Business() {
  const { setStep, formValues, updateFormValues } = useOnboardingStore();
  const [showGmvRanges, setShowGmvRanges] = useState(false);
  const [focusItems, setFocusItems] = useState(initialFocusItems);
  const [draggedId, setDraggedId] = useState(null);

  const gmvInputDisplay = formValues.annualGmv
    ? Number(formValues.annualGmv).toLocaleString('en-US')
    : '';

  // Typing an exact figure selects the range it falls in.
  const handleGmvInput = (e) => {
    const digits = e.target.value.replace(/\D/g, '').slice(0, 15);
    if (!digits) {
      updateFormValues({ annualGmv: '', gmvRange: '' });
      return;
    }
    updateFormValues({ annualGmv: digits, gmvRange: rangeForAmount(Number(digits)).label });
  };

  // Picking a range snaps the exact figure to that range's lower bound so the
  // two controls never disagree.
  const handleGmvRange = (range) => {
    updateFormValues({ annualGmv: String(range.min), gmvRange: range.label });
  };

  const handleDragStart = (e, id) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
  };
  const handleDragOver = (e, id) => {
    e.preventDefault();
    if (!draggedId || draggedId === id) return;
    const from = focusItems.findIndex((f) => f.id === draggedId);
    const to = focusItems.findIndex((f) => f.id === id);
    if (from === -1 || to === -1) return;
    const newItems = [...focusItems];
    const [dragged] = newItems.splice(from, 1);
    newItems.splice(to, 0, dragged);
    setFocusItems(newItems);
  };
  const handleDragEnd = () => setDraggedId(null);

  return (
    <div className="max-w-lg mx-auto anim-fade-in">
      <div className="mb-5">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Business Details</h2>
        <p className="text-gray-500 text-sm leading-relaxed">
          Map your ecosystem. We need to understand your current scale and where your primary growth levers reside.
        </p>
      </div>

      <div className="space-y-5">
        {/* Identity & Naming */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
              <i className="fa-solid fa-user text-gray-500 text-[10px]"></i>
            </div>
            <h3 className="font-semibold text-gray-800 text-sm">Identity & Naming</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Store Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formValues.storeName}
                onChange={(e) => updateFormValues({ storeName: e.target.value })}
                placeholder="e.g. Acme Global Holdings"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Phone Number <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="tel"
                  value={formValues.phone || ''}
                  onChange={(e) => updateFormValues({ phone: e.target.value })}
                  placeholder="+1 (000) 000-0000"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
                />
                <button
                  disabled={!formValues.phone}
                  className="px-4 py-3 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white"
                >
                  Verify
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Business Details */}
        {/* <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
              <i className="fa-solid fa-building text-gray-500 text-[10px]"></i>
            </div>
            <h3 className="font-semibold text-gray-800 text-sm">Business Details</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Legal Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formValues.legalName || ''}
                onChange={(e) => updateFormValues({ legalName: e.target.value })}
                placeholder="e.g. Acme Global Holdings"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Business Address <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formValues.businessAddress || ''}
                onChange={(e) => updateFormValues({ businessAddress: e.target.value })}
                placeholder="Business address"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Tax ID IGST / PAN (Depending On Region) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formValues.taxId || ''}
                onChange={(e) => updateFormValues({ taxId: e.target.value })}
                placeholder="Tax ID / IGST / PAN (depending on region)"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition text-sm"
              />
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
              <p className="text-xs text-red-600 font-medium">Note: These Fields Are Mandatory Before Payouts</p>
            </div>
          </div>
        </div> */}

        {/* Annual GMV — exact figure, with an opt-in range picker */}
        <div>
          <div className="flex items-start gap-2 mb-3">
            <div className="w-7 h-7 rounded-2xl bg-gray-100 flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-chart-simple text-gray-500 text-xs"></i>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-1.5">
                Annual GMV
                <i
                  className="fa-regular fa-circle-question text-gray-400 text-[11px]"
                  title="Gross merchandise value — total sales across all your channels over the last 12 months."
                ></i>
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Enter your approximate annual gross merchandise value.
              </p>
            </div>
          </div>

          <div className="relative">
            <input
              type="text"
              inputMode="numeric"
              value={gmvInputDisplay}
              onChange={handleGmvInput}
              placeholder="e.g. 5,000,000"
              className="w-full pl-4 pr-4 py-3 border border-gray-300 rounded-xl focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-800 transition text-sm font-medium text-gray-900"
            />
          </div>

            <button
              type="button"
              onClick={() => setShowGmvRanges((prev) => !prev)}
              className="flex items-center gap-2.5 text-xs font-medium text-gray-400 hover:text-blue-700 transition mt-2"
            >
              <i className="fa-regular fa-circle-question text-sm"></i>
              {showGmvRanges
                ? 'Hide ranges'
                : "Don't know your Annual GMV? Choose a range instead"}
            </button>

          {showGmvRanges && (
            <div className="anim-fade-in">
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 border-t border-gray-200" />
                <span className="text-xs font-medium text-gray-400">OR</span>
                <div className="flex-1 border-t border-gray-200" />
              </div>
              <div className="flex items-start gap-2.5 mb-3">
                <i className="fa-regular fa-circle-question text-indigo-600 text-sm mt-0.5"></i>
                <div>
                  <h4 className="font-semibold text-gray-900 text-sm">Choose a range instead</h4>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Select the range that best represents your annual gross merchandise value.
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {gmvRanges.map((range) => {
                  const isSelected = formValues.gmvRange === range.label;
                  return (
                    <button
                      key={range.label}
                      type="button"
                      onClick={() => handleGmvRange(range)}
                      className={`flex items-center gap-2.5 px-3 py-3 border rounded-xl text-left transition ${
                        isSelected
                          ? 'border-indigo-600 ring-1 ring-indigo-600 bg-white'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <span
                        className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                          isSelected ? 'border-indigo-600' : 'border-gray-300'
                        }`}
                      >
                        {isSelected && <span className="w-2 h-2 rounded-full bg-indigo-600" />}
                      </span>
                      <span className="text-sm text-gray-800">{range.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Strategic Focus — Draggable */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
              <i className="fa-solid fa-bullseye text-gray-500 text-[10px]"></i>
            </div>
            <h3 className="font-semibold text-gray-800 text-sm">Strategic Focus</h3>
          </div>
          <div className="flex flex-col gap-2">
            {focusItems.map((item, index) => (
              <div
                key={item.id}
                draggable
                onDragStart={(e) => handleDragStart(e, item.id)}
                onDragOver={(e) => handleDragOver(e, item.id)}
                onDragEnd={handleDragEnd}
                className={`flex items-center justify-between px-4 py-3 rounded-xl border transition select-none ${
                  draggedId === item.id
                    ? 'border-gray-300 bg-gray-100 opacity-60 cursor-grabbing'
                    : 'border-gray-200 bg-white hover:bg-gray-50 cursor-grab'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${index === 0 ? 'bg-gray-300' : 'bg-gray-900'}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{item.label}</p>
                    <p className="text-xs text-gray-400">{item.desc}</p>
                  </div>
                </div>
                <span className="text-[9px] font-bold text-gray-400 tracking-widest uppercase bg-gray-100 px-2 py-1 rounded ml-3 flex-shrink-0">
                  Priority {index + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom nav */}
      <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={() => setStep(1)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition font-medium"
        >
          <i className="fa-solid fa-arrow-left text-xs"></i> Back
        </button>
        <button
          onClick={() => setStep(3)}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm"
        >
          Continue<i className="fa-solid fa-arrow-right text-xs"></i>
        </button>
      </div>
    </div>
  );
}

export default Step2Business;
