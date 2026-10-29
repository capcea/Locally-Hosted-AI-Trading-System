import { ShieldCheck, Wallet } from 'lucide-react';
import type { RecordItem } from '../management-api';
import { Link } from '../navigation/history';
import { CardTitle, EmptyState, StatusPill } from './components';

export function AccountsOverview({
  accounts,
  ready,
  failed,
  selected,
  choose,
}: {
  accounts: RecordItem[];
  ready: boolean;
  failed: boolean;
  selected: string;
  choose: (id: string) => void;
}) {
  const account = accounts.find((a) => a.id === selected),
    data = account?.data;
  return (
    <div className="v1-account-overview" aria-label="Prezentarea conturilor">
      <section className="panel">
        <CardTitle title="Conturi configurate" icon={Wallet} />
        <ul className="v1-account-list">
          {accounts.map((a) => (
            <li key={a.id}>
              <button
                className="secondary-button"
                aria-pressed={selected === a.id}
                onClick={() => choose(a.id)}
              >
                <span>
                  <strong>{a.data.name}</strong>
                  <small>Configurație SIMULATED</small>
                </span>
              </button>
            </li>
          ))}
        </ul>
        {!accounts.length && (
          <p>
            {failed
              ? 'UNAVAILABLE · lista nu poate fi citită complet.'
              : ready
                ? 'Niciun cont în lista citită. Configurează primul cont mai jos.'
                : 'UNKNOWN · citim conturile permise.'}
          </p>
        )}
      </section>
      <section className="panel">
        <CardTitle title="Contextul contului" icon={ShieldCheck} />
        {data?.kind === 'accounts' ? (
          <>
            <strong>{data.name}</strong>
            <StatusPill>SIMULATED / DENY_ALL</StatusPill>
            <dl className="v1-facts">
              <div>
                <dt>Capital declarat pentru simulare</dt>
                <dd>
                  {data.initial_capital} {data.currency}
                </dd>
              </div>
              <div>
                <dt>Originea înregistrării</dt>
                <dd>{data.source}</dd>
              </div>
              <div>
                <dt>Program asociat</dt>
                <dd>{data.program_id ?? 'Cont fără program asociat'}</dd>
              </div>
            </dl>
            <p>
              Acestea sunt metadate declarate. Nu confirmă un sold de broker, limite aplicate sau o
              politică verificată.
            </p>
            <Link className="primary-button" href={`/conturi/${selected}/siguranta`}>
              Revizuiește limitele și cele trei comenzi de siguranță
            </Link>
          </>
        ) : (
          <EmptyState title="Alege un cont pentru detalii">
            Conturile, limitele și politicile au scopuri separate. Mai jos poți administra
            configurațiile permise rolului tău.
          </EmptyState>
        )}
      </section>
    </div>
  );
}
