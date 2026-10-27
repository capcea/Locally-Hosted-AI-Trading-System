import { useEffect, useState } from 'react';
import type { components } from './generated/api';
import type { RecordItem } from './management-api';
import { api } from './management-api';
import { useAuth } from './auth/AuthProvider';
import { allRecords } from './records';
import { Link } from './navigation/history';

type Status = components['schemas']['AccountStatus'];
export function safetyLabel(status: Status | null, now: number, failed = false) {
  const stopped = status?.manual_stop || status?.automatic_stop;
  if (failed)
    return `${stopped ? 'Ultima stare: intrări simulate oprite · ' : ''}UNAVAILABLE · nu putem verifica`;
  if (!status) return 'UNKNOWN · stare necunoscută';
  const age = status.monitor_at ? now - Date.parse(status.monitor_at) : NaN;
  if (!Number.isFinite(age) || age < 0 || age > 30000)
    return `${status.manual_stop || status.automatic_stop ? 'Intrări simulate oprite · ' : ''}STALE · monitor absent sau depășit`;
  if (status.manual_stop || status.automatic_stop) return 'Intrări simulate oprite';
  if (!status.configured) return 'Configurare incompletă';
  if (!status.data_verified || !status.ledger_verified)
    return 'UNKNOWN · date sau registru de risc neverificat';
  return 'Verificare obligatorie la fiecare ordin simulat';
}
type Row = { account: RecordItem; status: Status | null; observed: number; failed: boolean };
export default function RiskBanner() {
  const { session, unavailable } = useAuth();
  const [rows, setRows] = useState<Row[]>([]);
  const [failed, setFailed] = useState(false);
  const [checked, setChecked] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (session?.state !== 'FULL') return;
    let active = true;
    let running = false;
    const read = async () => {
      if (running) return;
      running = true;
      try {
        const accounts = await allRecords('accounts');
        const next = await Promise.all(
          accounts.map(async (account): Promise<Row> => {
            try {
              return {
                account,
                status: await api<Status>(`/risk/accounts/${account.id}/status`),
                observed: Date.now(),
                failed: false,
              };
            } catch {
              return { account, status: null, observed: Date.now(), failed: true };
            }
          }),
        );
        if (active) {
          setRows((old) =>
            next.map((row) =>
              row.failed
                ? {
                    ...row,
                    status: old.find((r) => r.account.id === row.account.id)?.status ?? null,
                    observed: old.find((r) => r.account.id === row.account.id)?.observed ?? 0,
                  }
                : row,
            ),
          );
          setFailed(false);
          setChecked(Date.now());
        }
      } catch {
        if (active) setFailed(true);
      } finally {
        running = false;
      }
    };
    void read();
    const poll = setInterval(() => void read(), 10000);
    const age = setInterval(() => setNow(Date.now()), 1000);
    return () => {
      active = false;
      clearInterval(poll);
      clearInterval(age);
    };
  }, [session?.state, session?.user.id]);
  if (session?.state !== 'FULL') return null;
  const issues = rows.filter(
    (r) =>
      safetyLabel(r.status, now, r.failed) !== 'Verificare obligatorie la fiecare ordin simulat',
  );
  return (
    <aside className="risk-global-banner" aria-label="Siguranță risc globală">
      <div>
        <strong>
          {failed || unavailable
            ? 'UNAVAILABLE · acoperirea conturilor nu poate fi verificată'
            : checked === null
              ? 'UNKNOWN · verificăm siguranța conturilor'
              : `${issues.length} conturi necesită verificare din ${rows.length} conturi citite`}
        </strong>
        <p>
          SIMULATED / DENY_ALL · Ordine externe blocate.{' '}
          {checked
            ? `Citire: ${new Date(checked).toLocaleTimeString('ro-RO')}.`
            : 'Nu presupunem că lipsa datelor înseamnă siguranță.'}
        </p>
      </div>
      <Link className="secondary-button" href="/conturi/siguranta">
        Siguranță și oprirea intrărilor
      </Link>
      {rows.length > 0 && (
        <details>
          <summary>Starea fiecărui cont</summary>
          <ul>
            {rows.map((r) => (
              <li key={r.account.id}>
                <Link href={`/conturi/${r.account.id}/siguranta`}>{r.account.data.name}</Link> ·{' '}
                {safetyLabel(r.status, now, r.failed || failed || unavailable)} · monitor:{' '}
                {r.status?.monitor_at ?? 'necunoscut'}
              </li>
            ))}
          </ul>
        </details>
      )}
    </aside>
  );
}
