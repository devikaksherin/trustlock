import { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react';
import { getHealth } from '../services/api';

const BackendStatusContext = createContext(null);

export function BackendStatusProvider({ children }) {
  const [state, setState] = useState("checking");
  const [reason, setReason] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [epoch, setEpoch] = useState(0);

  const stateRef = useRef(state);
  stateRef.current = state;
  const epochRef = useRef(epoch);
  epochRef.current = epoch;

  const checkHealth = useCallback(async () => {
    const controller = new AbortController();
    // getHealth now manages its own 5000ms timeout
    const result = await getHealth(controller.signal);
    
    // Only increment epoch if we're recovering from a bad state
    if (result.state === "online" && (stateRef.current === "offline" || stateRef.current === "degraded" || stateRef.current === "checking")) {
        if (stateRef.current !== "checking") {
           setEpoch(epochRef.current + 1);
        }
    }

    setState(result.state);
    setReason(result.reason);
    setLastChecked(new Date());
    
    return result.state;
  }, []);

  useEffect(() => {
    checkHealth();

    let timeoutId;
    const scheduleNext = (currentState) => {
      const interval = (currentState === "online") ? 10000 : 3000;
      timeoutId = setTimeout(async () => {
        if (!document.hidden || currentState !== "online") {
          const nextState = await checkHealth();
          scheduleNext(nextState);
        } else {
          scheduleNext(currentState);
        }
      }, interval);
    };

    scheduleNext(stateRef.current);

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkHealth();
      }
    };

    const handleFocus = () => {
        if (!document.hidden) {
            checkHealth();
        }
    }

    const handleOnline = () => {
      checkHealth();
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", handleFocus);
    window.addEventListener("online", handleOnline);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("online", handleOnline);
    };
  }, [checkHealth]);

  const value = {
    state,
    reason,
    lastChecked,
    retry: checkHealth,
    epoch
  };

  return (
    <BackendStatusContext.Provider value={value}>
      {children}
    </BackendStatusContext.Provider>
  );
}

export function useBackendStatus() {
  return useContext(BackendStatusContext);
}
