import { useState } from 'react';

// Generic "open with payload / close" state for a single modal — replaces the
// `const [x, setX] = useState(null)` + `setX(payload)` / `setX(null)` pattern
// repeated across every KPIDetailModal usage (`isOpen={!!x}`, `stat={x}`).
const useModalToggle = (initialData = null) => {
  const [data, setData] = useState(initialData);

  const open = (payload) => setData(payload);
  const close = () => setData(null);

  return { data, isOpen: !!data, open, close };
};

export default useModalToggle;
