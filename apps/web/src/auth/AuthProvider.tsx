import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { clearResearchDrafts } from '../research-drafts';
import { clearAIQuestion } from '../ai/draft';
import { api, ApiError, parseSession } from '../management-api';
import type { Session } from '../management-api';
import { authRevision, advanceAuthRevision, authMessages } from './lifecycle';

type Auth = {
  session: Session | null;
  setSession: (session: Session | null) => void;
  expire: () => void;
  loading: boolean;
  unavailable: boolean;
  refresh: () => Promise<void>;
  mfaRequired: boolean;
  stepUpOpen: boolean;
  requestMfa: () => void;
  dismissMfa: () => void;
  notice: string;
  announce: (message: string) => void;
};
const Context = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, update] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);
  const current = useRef<Session | null>(null);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [stepUpOpen, setStepUpOpen] = useState(false);
  const [notice, announce] = useState('');
  const setSession = useCallback((value: Session | null) => {
    if (
      !value ||
      value.session_id !== current.current?.session_id ||
      value.csrf_token !== current.current?.csrf_token
    ) {
      advanceAuthRevision();
      setMfaRequired(false);
      setStepUpOpen(false);
      announce('');
    }
    current.current = value;
    if (value === null) {
      clearResearchDrafts();
      clearAIQuestion();
    }
    update(value);
    setUnavailable(false);
  }, []);
  const expire = useCallback(() => setSession(null), [setSession]);
  const refresh = useCallback(async () => {
    const revision = authRevision();
    try {
      const value = parseSession(await api('/auth/me'));
      if (revision === authRevision()) setSession(value);
    } catch (error) {
      if (revision === authRevision()) {
        if (error instanceof ApiError && error.status === 401) expire();
        else setUnavailable(true);
      }
    } finally {
      setLoading(false);
    }
  }, [setSession, expire]);
  const requestMfa = useCallback(() => {
    if (current.current?.state === 'FULL') {
      setMfaRequired(true);
      setStepUpOpen(true);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const onExpired = (event: Event) => {
      expire();
      if ((event as CustomEvent).detail === 'SESSION_EXPIRED')
        announce(authMessages.SESSION_EXPIRED);
    };
    const onRefresh = () => {
      void refresh();
    };
    const onFocus = () => {
      if (current.current?.state === 'FULL') void refresh();
    };
    window.addEventListener('research-session-expired', onExpired);
    window.addEventListener('research-mfa-required', requestMfa);
    window.addEventListener('research-session-refresh', onRefresh);
    window.addEventListener('focus', onFocus);
    return () => {
      window.removeEventListener('research-session-expired', onExpired);
      window.removeEventListener('research-mfa-required', requestMfa);
      window.removeEventListener('research-session-refresh', onRefresh);
      window.removeEventListener('focus', onFocus);
    };
  }, [refresh, expire, requestMfa]);
  return (
    <Context
      value={{
        session,
        setSession,
        expire,
        loading,
        unavailable,
        refresh,
        mfaRequired,
        stepUpOpen,
        requestMfa,
        dismissMfa: () => setStepUpOpen(false),
        notice,
        announce,
      }}
    >
      {children}
    </Context>
  );
}

export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error('AuthProvider required');
  return value;
}
