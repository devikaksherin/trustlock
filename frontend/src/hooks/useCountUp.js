import { useState, useEffect } from 'react';

export function useCountUp(target, { duration = 900, enabled = true } = {}) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!enabled || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setCount(target);
      return;
    }

    let start = null;
    let animationFrame;
    const initialCount = 0;

    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = timestamp - start;
      const ratio = Math.min(progress / duration, 1);
      const easedRatio = easeOutCubic(ratio);
      
      setCount(Math.floor(initialCount + (target - initialCount) * easedRatio));

      if (progress < duration) {
        animationFrame = requestAnimationFrame(step);
      } else {
        setCount(target);
      }
    };

    animationFrame = requestAnimationFrame(step);

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [target, duration, enabled]);

  return count;
}
