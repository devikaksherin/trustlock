import { useState, useEffect, useCallback, useRef } from 'react';
import { getChallenge, verifyChallenge, friendlyMessage } from '../services/api';

export function useChallenge(initialChallengeId) {
  const [challengeId, setChallengeId] = useState(initialChallengeId || null);
  const [challenge, setChallenge] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [remainingSecs, setRemainingSecs] = useState(0);
  
  const timerRef = useRef(null);
  const expiryTimeRef = useRef(0);

  const fetchChallenge = useCallback(async (id) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getChallenge(id);
      setChallenge(data);
      if (!data.expired && data.status === 'pending') {
        expiryTimeRef.current = performance.now() + data.remaining_seconds * 1000;
        setRemainingSecs(data.remaining_seconds);
      } else {
        setRemainingSecs(0);
      }
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (challengeId) {
      fetchChallenge(challengeId);
    } else {
      setChallenge(null);
      setRemainingSecs(0);
    }
  }, [challengeId, fetchChallenge]);

  useEffect(() => {
    if (!challenge || challenge.status !== 'pending' || challenge.expired) {
      if (timerRef.current) cancelAnimationFrame(timerRef.current);
      return;
    }

    const updateTimer = () => {
      const now = performance.now();
      const left = Math.max(0, Math.ceil((expiryTimeRef.current - now) / 1000));
      setRemainingSecs(left);
      
      if (left > 0) {
        timerRef.current = requestAnimationFrame(updateTimer);
      } else {
        fetchChallenge(challengeId);
      }
    };
    
    timerRef.current = requestAnimationFrame(updateTimer);
    return () => {
      if (timerRef.current) cancelAnimationFrame(timerRef.current);
    };
  }, [challenge, challengeId, fetchChallenge]);

  const verifyLive = useCallback(async (response) => {
    if (!challengeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await verifyChallenge({ challenge_id: challengeId, response });
      setChallenge(prev => ({ ...prev, ...res, remaining_seconds: remainingSecs }));
      return res;
    } catch (err) {
      setError(friendlyMessage(err));
      await fetchChallenge(challengeId);
      return null;
    } finally {
      setLoading(false);
    }
  }, [challengeId, fetchChallenge, remainingSecs]);

  const verifySim = useCallback(async (outcome) => {
    if (!challengeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await verifyChallenge({ 
        challenge_id: challengeId, 
        simulation: true, 
        simulated_outcome: outcome 
      });
      setChallenge(prev => ({ ...prev, ...res, remaining_seconds: remainingSecs }));
      return res;
    } catch (err) {
      setError(friendlyMessage(err));
      await fetchChallenge(challengeId);
      return null;
    } finally {
      setLoading(false);
    }
  }, [challengeId, fetchChallenge, remainingSecs]);

  return {
    challengeId,
    setChallengeId,
    challenge,
    loading,
    error,
    remainingSecs,
    verifyLive,
    verifySim,
    refresh: () => fetchChallenge(challengeId)
  };
}
