import { useEffect, useRef } from 'react';

// Attaches a single mousedown listener only while isOpen is true.
// Calls onClose when the click lands outside ref (and extraRef if provided).
// Using a ref for onClose avoids stale-closure issues without adding it to deps.
const useClickOutside = (ref, isOpen, onClose, extraRef) => {
  const onCloseRef = useRef(onClose);
  useEffect(() => { onCloseRef.current = onClose; }); // keep in sync on every render

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      const inMain  = ref.current  && ref.current.contains(e.target);
      const inExtra = extraRef?.current && extraRef.current.contains(e.target);
      if (!inMain && !inExtra) onCloseRef.current();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps -- ref/extraRef are stable React refs; onCloseRef.current is always fresh
};

export default useClickOutside;
