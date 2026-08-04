import React from 'react';
import { motion } from 'framer-motion';
import Modal from '@/components/overlays/Modal';

/**
 * Modal shell with a fading backdrop and a scale/slide entrance.
 *
 * Shares the `Modal` container so there is still exactly one implementation of
 * the full-screen click-catcher, but brings its own framer-motion backdrop and
 * panel — which is why dismissal is wired to the backdrop rather than the
 * container (`closeOn="none"`).
 */
const AnimatedModal = ({ isOpen, onClose, children, maxWidth = 'max-w-md' }) => (
  <Modal isOpen={isOpen} onClose={onClose} portal={false} scrim="" closeOn="none">
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
    ></motion.div>

    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 20 }}
      className={`relative w-full ${maxWidth} bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-gray-100 dark:border-slate-800`}
    >
      {children}
    </motion.div>
  </Modal>
);

export default AnimatedModal;
