import { useEffect, useState } from 'react';
import { ai } from './api';
import type { Role } from './api';
import type { Readiness, ReadinessObservation } from './readiness';

export function useInferenceReadiness(role: Role, category: string) {
  const [observation, setObservation] = useState<ReadinessObservation | null>(null);
  const [tick, setTick] = useState(Date.now);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let alive = true,
      sequence = 0;
    const load = async () => {
      const current = ++sequence;
      try {
        const value = await ai<Readiness>(
          `/inference-readiness?role=${encodeURIComponent(role)}&category=${encodeURIComponent(category)}`,
        );
        if (alive && current === sequence)
          setObservation({ role, category, value, received: Date.now() });
      } catch {
        if (alive && current === sequence) setObservation(null);
      }
    };
    void load();
    const poll = window.setInterval(() => void load(), 10000);
    const timer = window.setInterval(() => setTick(Date.now()), 1000);
    return () => {
      alive = false;
      sequence++;
      window.clearInterval(poll);
      window.clearInterval(timer);
    };
  }, [role, category, revision]);
  return { observation, now: tick, refreshReadiness: () => setRevision((value) => value + 1) };
}
