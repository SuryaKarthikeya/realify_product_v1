import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';

const JOKES = [
  { text: 'I told my wife she should embrace her mistakes. She gave me a hug.', emphasis: 'embrace' },
  { text: "I told my warehouse a joke about inventory. It didn't stock up on laughs.", emphasis: 'stock up' },
  { text: 'Why did the golfer bring two pairs of pants? In case he got a hole in one.', emphasis: 'hole in one' },
  { text: 'How do you catch a squirrel? Climb a tree and act like a nut!', emphasis: 'act like a nut' },
];

const ROTATE_MS = 3500;

/** Splits a joke around its emphasis so only that phrase is bolded. */
const renderJoke = ({ text, emphasis }) => {
  const at = emphasis ? text.indexOf(emphasis) : -1;
  if (at === -1) return text;
  return (
    <>
      {text.slice(0, at)}
      <span className="font-bold text-gray-900">{emphasis}</span>
      {text.slice(at + emphasis.length)}
    </>
  );
};

const DadJokeCard = () => {
  const [index, setIndex] = useState(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const timer = setTimeout(() => setIndex((i) => (i + 1) % JOKES.length), ROTATE_MS);
    return () => clearTimeout(timer);
  }, [index]);

  return (
    <motion.aside
      initial={{ opacity: 0, y: reduceMotion ? 0 : 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="w-full rounded-2xl border border-gray-100 bg-white shadow-sm px-6 py-5 text-center"
    >
      <p className="text-[10.5px] font-mono font-medium uppercase tracking-[0.15em] text-gray-400">
        <span aria-hidden="true">✳</span> While that uploads… a dad joke
      </p>

      <div className="mt-2.5 min-h-[44px] flex items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.p
            key={index}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="text-[15px] leading-relaxed text-gray-700"
          >
            {renderJoke(JOKES[index])}
          </motion.p>
        </AnimatePresence>
      </div>

      <button
        type="button"
        onClick={() => setIndex((i) => (i + 1) % JOKES.length)}
        className="mt-3 px-4 py-2 rounded-xl bg-blue-50 text-[13px] font-bold text-blue-700 hover:bg-blue-100 transition-colors"
      >
        Another one <span aria-hidden="true">→</span>
      </button>
    </motion.aside>
  );
};

export default DadJokeCard;
