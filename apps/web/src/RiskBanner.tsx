import { useEffect, useState } from 'react';
import type { components } from './generated/api';
import type { RecordItem } from './management-api';
import { api } from './management-api';
import { useAuth } from './auth/AuthProvider';
import { allRecords } from './records';
import { Link } from './navigation/history';
import { Shield } from 'lucide-react';

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
export function safetyOverview({
  failed,
  checked,
  count,
  issues,
}: {
  failed: boolean;
  checked: number | null;
  count: number;
  issues: number;
}) {
  if (failed) return 'UNAVAILABLE · acoperirea conturilor nu poate fi verificată';
  if (checked === null) return 'UNKNOWN · verificăm siguranța conturilor';
  if (count === 0) return 'Niciun cont în lista citită';
  const scope = count === 1 ? '1 cont citit' : `${count} conturi citite`;
  if (issues > 0)
    return `${issues === 1 ? 'Un cont necesită' : `${issues} conturi necesită`} verificare · ${scope}`;
  return `${scope} · verificare la fiecare ordin simulat`;
}
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
  const stopped = rows.filter((r) => r.status?.manual_stop || r.status?.automatic_stop);
  return (
    <aside
      className="risk-global-banner"
      aria-label="Siguranță risc globală"
      data-attention={failed || unavailable || checked === null || issues.length > 0}
    >
      <Shield size={20} aria-hidden="true" className="risk-banner-icon" />
      <div className="risk-banner-copy">
        <strong>
          {safetyOverview({
            failed: failed || unavailable,
            checked,
            count: rows.length,
            issues: issues.length,
          })}
        </strong>
        <p>
          {checked !== null
            ? `Citire: ${new Date(checked).toLocaleTimeString('ro-RO')}.`
            : 'Nu presupunem că lipsa datelor înseamnă siguranță.'}
        </p>
        {stopped.length > 0 && (
          <p className="risk-stop-warning">
            Oprire în ultima stare citită: {stopped.length}{' '}
            {stopped.length === 1 ? 'cont' : 'conturi'}. Verifică starea fiecărui cont.
          </p>
        )}
        {!failed && !unavailable && checked !== null && !rows.length && (
          <Link href="/conturi">Configurează un cont pentru simulare</Link>
        )}
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
