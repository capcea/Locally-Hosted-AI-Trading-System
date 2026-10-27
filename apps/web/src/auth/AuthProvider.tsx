import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { clearResearchDrafts } from '../research-drafts';
import { api, ApiError, parseSession } from '../management-api';
import type { Session } from '../management-api';

type Auth = {
  session: Session | null;
  setSession: (session: Session | null) => void;
  expire: () => void;
  loading: boolean;
  unavailable: boolean;
  refresh: () => Promise<void>;
};
const Context = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, update] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);
  const setSession = useCallback((value: Session | null) => {
    if (value === null) clearResearchDrafts();
    update(value);
    setUnavailable(false);
  }, []);
  const expire = useCallback(() => setSession(null), [setSession]);
  const refresh = useCallback(async () => {
    try {
      setSession(parseSession(await api('/auth/me')));
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) expire();
      else setUnavailable(true);
    } finally {
      setLoading(false);
    }
  }, [setSession, expire]);
  useEffect(() => {
    void refresh();
    const onExpired = () => expire();
    window.addEventListener('research-session-expired', onExpired);
    return () => window.removeEventListener('research-session-expired', onExpired);
  }, [refresh, expire]);
  return (
    <Context value={{ session, setSession, expire, loading, unavailable, refresh }}>
      {children}
    </Context>
  );
}

export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error('AuthProvider required');
  return value;
}
