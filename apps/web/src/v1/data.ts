import { useEffect, useState } from 'react';
import { api } from '../management-api';
import { useAuth } from '../auth/AuthProvider';

/** Read-only, same-origin, owner-bound display state. A failed refresh never leaves a green stale value. */
export function useOwnedRead<T>(path: string | null, pollMs = 0) {
  const { session } = useAuth();
  const owner = session?.state === 'FULL' ? session.user.id : '';
  const key = `${owner}:${path ?? ''}`;
  const [state, setState] = useState<{
    key: string;
    data: T | null;
    lastKnown: T | null;
    failed: boolean;
  }>({ key: '', data: null, lastKnown: null, failed: false });
  useEffect(() => {
    if (!owner || !path) return;
    let alive = true,
      pending = false;
    const load = async () => {
      if (pending) return;
      pending = true;
      try {
        const data = await api<T>(path);
        if (alive) setState({ key, data, lastKnown: data, failed: false });
      } catch {
        if (alive)
          setState((previous) => ({
            key,
            data: null,
            lastKnown: previous.key === key ? previous.lastKnown : null,
            failed: true,
          }));
      } finally {
        pending = false;
      }
    };
    void load();
    const timer = pollMs ? setInterval(() => void load(), pollMs) : undefined;
    const refresh = () => {
      void load();
    };
    window.addEventListener('research-display-refresh', refresh);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener('research-display-refresh', refresh);
    };
  }, [owner, path, pollMs, key]);
  const current = owner && path && state.key === key;
  return {
    data: current ? state.data : null,
    lastKnown: current ? state.lastKnown : null,
    failed: Boolean(current && state.failed),
    loading: Boolean(owner && path && (!current || (!state.data && !state.failed))),
  };
}

export type ResearchJob = {
  id: string;
  name: string;
  strategy: string;
  phase: string;
  engine: string;
  created_at?: string;
  job: {
    state: string;
    progress: number;
    attempts: number;
    error: string | null;
    cancel_requested?: boolean;
  };
  result: unknown;
};
export type ReviewedStrategy = {
  id: string;
  version: string;
  digest: string;
  entry: string;
  exit: string;
  assumptions: string;
  parameters: unknown;
};

const families: Record<string, string> = {
  EMA_TREND: 'Trend',
  MA_CROSS: 'Trend',
  DONCHIAN: 'Breakout',
  ATR_BREAKOUT: 'Breakout',
  BOLLINGER: 'Mean Reversion',
  RSI: 'Mean Reversion',
  OPENING_RANGE: 'Sesiune',
  SESSION_MOMENTUM: 'Sesiune',
};
export const strategyFamily = (id: string) => families[id] ?? 'Altele';
export const strategyDescriptions: Record<string, string> = {
  EMA_TREND: 'Urmărește direcția prețului cu o medie exponențială.',
  MA_CROSS: 'Compară o medie rapidă cu una lentă, pe observații deja disponibile.',
  DONCHIAN: 'Caută depășirea intervalului recent al prețului.',
  BOLLINGER: 'Testează revenirea spre medie după o abatere de preț.',
  RSI: 'Testează revenirea după mișcări accentuate ale prețului.',
  ATR_BREAKOUT: 'Caută mișcări care depășesc variația recentă.',
  OPENING_RANGE: 'Testează depășirea intervalului de la deschiderea sesiunii.',
  SESSION_MOMENTUM: 'Urmărește direcția mișcării în sesiunea configurată.',
};
export function filterExperiments(
  jobs: ResearchJob[],
  query: string,
  state: string,
  phase: string,
) {
  const q = query.trim().toLocaleLowerCase('ro-RO');
  return jobs.filter(
    (j) =>
      (!q || `${j.name} ${j.id} ${j.strategy}`.toLocaleLowerCase('ro-RO').includes(q)) &&
      (!state || j.job.state === state) &&
      (!phase || j.phase === phase),
  );
}
