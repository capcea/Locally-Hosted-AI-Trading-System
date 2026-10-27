import { useEffect, useState } from 'react';
import { api, ApiError } from './management-api';
import type { RecordPage, Session } from './management-api';
import type { components } from './generated/api';

type Status = components['schemas']['AccountStatus'];
export default function RiskBanner({ onOpen }: { onOpen: () => void }) {
  const [states, setStates] = useState<Status[]>([]);
  const [authenticated, setAuthenticated] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let current = true;
    async function check() {
      try {
        const session = await api<Session>('/auth/me');
        if (session.state !== 'FULL') return;
        const accounts = await api<RecordPage>('/records/accounts?limit=100');
        const next = await Promise.all(
          accounts.items.map((a) => api<Status>(`/risk/accounts/${a.id}/status`)),
        );
        if (current) {
          setStates(next);
          setAuthenticated(true);
          setUnavailable(false);
        }
      } catch (error) {
        if (!current) return;
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false);
          setStates([]);
        } else setUnavailable(true);
      }
    }
    void check();
    const timer = setInterval(() => {
      void check();
    }, 10000);
    return () => {
      current = false;
      clearInterval(timer);
    };
  }, []);
  if (!authenticated) return null;
  const stopped = states.filter(
    (s) =>
      s.manual_stop ||
      s.automatic_stop ||
      !s.configured ||
      !s.monitor_at ||
      Date.now() - Date.parse(s.monitor_at) > 30000,
  ).length;
  return (
    <aside className="risk-global-banner" aria-label="Siguranță risc globală">
      <strong>
        {unavailable
          ? 'Starea riscului este indisponibilă'
          : `${stopped} conturi cu intrări oprite`}
      </strong>
      <span>Verificare obligatorie la fiecare ordin simulat. Execuție externă: DENY_ALL.</span>
      <button className="secondary-button" onClick={onOpen}>
        Deschide controlul riscului
      </button>
    </aside>
  );
}
