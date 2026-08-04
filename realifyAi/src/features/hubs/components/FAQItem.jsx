import { memo } from 'react';

const FAQItem = memo(({ faq, isOpen, onToggle }) => (
  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-2xl overflow-hidden shadow-sm">
    <button
      onClick={onToggle}
      className="w-full px-6 py-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
    >
      <div className="flex items-start gap-4 text-left flex-1">
        <i className="fa-solid fa-circle-question text-blue-600 text-xl mt-0.5 flex-shrink-0" />
        <span className="font-semibold text-gray-900 dark:text-white text-lg">{faq.q}</span>
      </div>
      <i
        className={`fa-solid fa-chevron-down text-gray-400 flex-shrink-0 ml-3 transition-transform duration-300 ${
          isOpen ? 'rotate-180' : ''
        }`}
      />
    </button>

    <div className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-96' : 'max-h-0'}`}>
      <div className="px-6 pb-5">
        <div className="ml-10 text-gray-600 dark:text-slate-400 leading-relaxed">
          <p className="mb-3">{faq.a}</p>
          <button className="mt-2 px-4 py-2 bg-brand text-white text-sm font-medium rounded-lg hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 transition">
            {faq.btn}
          </button>
        </div>
      </div>
    </div>
  </div>
));

FAQItem.displayName = 'FAQItem';

export default FAQItem;
