import { ShieldCheck } from 'lucide-react';
import type { components } from '../generated/api';
import { safetyLabel } from '../RiskBanner';
import { Link } from '../navigation/history';
import { CardTitle, EmptyState } from './components';
import { useOwnedRead } from './data';

export function AccountSafety({ accountId }: { accountId: string }) {
  const read = useOwnedRead<components['schemas']['AccountStatus']>(
    accountId ? `/risk/accounts/${encodeURIComponent(accountId)}/status` : null,
    10000,
  );
  return (
    <section className="panel v1-safety-card" aria-label="Siguranța contului selectat">
      <CardTitle title="Siguranță și limite" icon={ShieldCheck} />
      {!accountId ? (
        <EmptyState title="Alege un cont" href="/conturi/siguranta" action="Verifică siguranța">
          UNKNOWN · limitele și riscul sunt specifice fiecărui cont. Nu afișăm o medie între
          conturi.
        </EmptyState>
      ) : (
        <>
          <p>
            <strong>{safetyLabel(read.data ?? read.lastKnown, Date.now(), read.failed)}</strong>
          </p>
          <dl className="v1-facts">
            <div>
              <dt>Până la limita zilnică · ultima observație</dt>
              <dd>
                {read.data?.daily_headroom ?? 'UNKNOWN'} {read.data?.currency}
              </dd>
            </div>
            <div>
              <dt>Până la limita totală · ultima observație</dt>
              <dd>
                {read.data?.total_headroom ?? 'UNKNOWN'} {read.data?.currency}
              </dd>
            </div>
            <div>
              <dt>Risc deja alocat</dt>
              <dd>
                {read.data?.values?.reserved_risk == null
                  ? 'UNKNOWN'
                  : String(read.data.values.reserved_risk)}{' '}
                {read.data?.currency}
              </dd>
            </div>
          </dl>
          <p>
            Observație monitor: {read.data?.monitor_at ?? 'necunoscută'}. Sumele observate nu
            înlocuiesc verificarea la fiecare ordin simulat.
          </p>
          <Link href={`/conturi/${accountId}/siguranta`}>
            Verifică limitele și oprirea contului →
          </Link>
        </>
      )}
    </section>
  );
}
