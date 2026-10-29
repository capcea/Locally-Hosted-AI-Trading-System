import { useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  CircleHelp,
  Clock,
  FlaskConical,
  Layers,
  Search,
  ShieldCheck,
  Target,
  ChartNoAxesCombined,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { strategyLabels } from '../copy/ro';
import { Evidence } from '../ui/Controls';
import { Link } from '../navigation/history';
import { CardTitle, EmptyState, Kpi, StatusPill } from './components';
import { ExperimentPreview } from './ExperimentPreview';
import { strategyDescriptions, strategyFamily } from './data';
import type { ResearchJob, ReviewedStrategy } from './data';

export function StrategyLibrary({
  strategies,
  loaded,
  blocked,
  choose,
}: {
  strategies: ReviewedStrategy[];
  loaded: boolean;
  blocked: boolean;
  choose: (id: string) => void;
}) {
  const [category, setCategory] = useState('Toate'),
    [query, setQuery] = useState('');
  const categories = [...new Set(strategies.map((s) => strategyFamily(s.id)))];
  const matches = strategies.filter(
    (s) =>
      (category === 'Toate' || strategyFamily(s.id) === category) &&
      `${s.id} ${strategyLabels[s.id] ?? ''} ${strategyDescriptions[s.id] ?? ''}`
        .toLocaleLowerCase('ro-RO')
        .includes(query.trim().toLocaleLowerCase('ro-RO')),
  );
  return (
    <div className="v1-strategies">
      <div className="v1-kpis">
        <Kpi
          label="Strategii disponibile"
          value={loaded ? strategies.length : '—'}
          help="Etaloane din registrul revizuit"
          icon={FlaskConical}
        />
        <Kpi
          label="Versiuni de bază"
          value={loaded ? new Set(strategies.map((s) => s.version)).size : '—'}
          help="Versiuni întoarse de server"
          icon={Layers}
          tone="violet"
        />
        <Kpi
          label="Familii de strategii"
          value={loaded ? categories.length : '—'}
          help="Categorii de explorare"
          icon={Target}
          tone="amber"
        />
        <Kpi
          label="Mod de utilizare"
          value="SIMULAT"
          help="Fără activare live sau garanții"
          icon={ShieldCheck}
          tone="green"
        />
      </div>
      <section className="panel">
        <CardTitle title="Strategii revizuite" icon={Layers}>
          <Link className="secondary-button" href="/testeaza/ai">
            Propune o idee <ArrowRight size={15} />
          </Link>
        </CardTitle>
        <p>
          Etaloane experimentale, nu recomandări de investiții. Versiunile și regulile exacte rămân
          inspectabile.
        </p>
        <label className="management-field">
          Caută o strategie
          <input
            aria-label="Caută o strategie"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nume sau metodă…"
          />
        </label>
        <div className="v1-filter-chips" role="group" aria-label="Categorii de strategii">
          {['Toate', ...categories].map((c) => (
            <button key={c} aria-pressed={category === c} onClick={() => setCategory(c)}>
              {c} (
              {c === 'Toate'
                ? strategies.length
                : strategies.filter((s) => strategyFamily(s.id) === c).length}
              )
            </button>
          ))}
        </div>
        {blocked && (
          <p className="notice">
            Solicitarea anterioară este incertă. Verifică activitatea înainte să schimbi strategia.
          </p>
        )}
        <div
          className="table-scroll"
          role="region"
          aria-label="Biblioteca strategiilor"
          tabIndex={0}
        >
          <table className="v1-strategy-table">
            <thead>
              <tr>
                <th scope="col">Strategie</th>
                <th scope="col">Tip</th>
                <th scope="col">Versiune</th>
                <th scope="col">Disponibilitate</th>
                <th scope="col">Acțiune</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((s) => (
                <tr key={s.id}>
                  <td>
                    <div className="v1-strategy-name">
                      <span className="v1-icon">
                        <FlaskConical size={21} />
                      </span>
                      <div>
                        <h3>{strategyLabels[s.id] ?? s.id}</h3>
                        <p>{strategyDescriptions[s.id] ?? s.assumptions}</p>
                      </div>
                    </div>
                    <Evidence title={`${s.id} · versiune și parametri`} value={s} />
                  </td>
                  <td>
                    <StatusPill>{strategyFamily(s.id)}</StatusPill>
                  </td>
                  <td>{s.version}</td>
                  <td>
                    <StatusPill>Etalon revizuit</StatusPill>
                  </td>
                  <td>
                    <button
                      className="secondary-button"
                      disabled={blocked}
                      onClick={() => choose(s.id)}
                    >
                      Testează strategia <ArrowRight size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!matches.length && (
          <EmptyState
            icon={Search}
            title={loaded ? 'Nicio strategie pentru acest filtru' : 'Citim biblioteca…'}
          >
            Dacă registrul nu poate fi verificat, nu inventăm strategii disponibile. Revizuiește
            mesajele de mai sus sau schimbă filtrul.
          </EmptyState>
        )}
        <Link href="/testeaza/nou">Alege strategia într-un test nou</Link>
      </section>
    </div>
  );
}

export function ExperimentStats({ jobs, available }: { jobs: ResearchJob[]; available: boolean }) {
  return (
    <div className="v1-kpis" aria-label="Rezumatul paginii de experimente">
      {[
        {
          label: 'Experimente citite',
          value: jobs.length,
          help: 'Pagina curentă · nu totalul istoric',
          icon: FlaskConical,
        },
        {
          label: 'În lucru',
          value: jobs.filter((j) => ['RUNNING', 'RETRY'].includes(j.job.state)).length,
          help: 'Stare raportată de server',
          icon: Clock,
          tone: 'violet' as const,
        },
        {
          label: 'În așteptare',
          value: jobs.filter((j) => j.job.state === 'QUEUED').length,
          help: 'Fără timp de finalizare estimat',
          icon: Clock,
          tone: 'amber' as const,
        },
        {
          label: 'Finalizate',
          value: jobs.filter((j) => j.job.state === 'SUCCEEDED').length,
          help: 'Anularea cerută nu înseamnă anulare confirmată',
          icon: ShieldCheck,
          tone: 'green' as const,
        },
      ].map((item) => (
        <Kpi key={item.label} {...item} value={available ? item.value : '—'} />
      ))}
    </div>
  );
}

export type ReadinessItem = {
  title: string;
  ready: boolean;
  detail: string;
  href: string;
  action: string;
};
export function BacktestReview({
  items,
  children,
}: {
  items: ReadinessItem[];
  children?: ReactNode;
}) {
  return (
    <aside className="panel v1-backtest-review" aria-label="Revizuirea testului">
      <CardTitle title="Pregătirea testului" icon={ShieldCheck} />
      <p>Alege configurația în stânga. Aici vezi ce este verificat și ce mai lipsește.</p>
      <ul className="v1-readiness">
        {items.map((item) => {
          const Icon = item.ready ? CheckCircle2 : CircleHelp;
          return (
            <li key={item.title}>
              <Icon size={19} aria-hidden="true" />
              <div>
                <strong>
                  {item.title} · {item.ready ? 'Selectat / citit' : 'Necesită verificare'}
                </strong>
                <small>{item.detail}</small>
                <Link href={item.href}>{item.action}</Link>
              </div>
            </li>
          );
        })}
      </ul>
      {children}
      <div className="v1-empty">
        <ChartNoAxesCombined size={35} aria-hidden="true" />
        <h3>Rezultatul apare după finalizare</h3>
        <p>
          Graficul, costurile și rezultatele vor proveni din experimentul stocat. Serverul verifică
          din nou datele și riscul înainte și în timpul simulării.
        </p>
      </div>
    </aside>
  );
}

export function ResultsOverview({ jobs, failed }: { jobs: ResearchJob[]; failed: boolean }) {
  const [chosen, setChosen] = useState('');
  const complete = jobs.filter((j) => j.job.state === 'SUCCEEDED');
  const selected = complete.find((j) => j.id === chosen) ?? complete[0];
  return (
    <section className="panel v1-results-landing" aria-label="Rezultate stocate selectate">
      <CardTitle title="Rezultatul unui experiment" icon={ChartNoAxesCombined}>
        <Link href="/rezultate/compara">Compară două teste →</Link>
      </CardTitle>
      <p>
        Rezultate simulate, pentru un singur test și scenariu. Nu reprezintă un portofoliu sau un
        sold de broker.
      </p>
      {!failed && selected ? (
        <>
          <label className="v1-select-inline">
            Alege experimentul
            <select
              aria-label="Alege experimentul"
              value={selected.id}
              onChange={(e) => setChosen(e.target.value)}
            >
              {complete.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.name}
                </option>
              ))}
            </select>
          </label>
          <div className="v1-results-overview">
            <ExperimentPreview key={selected.id} id={selected.id} />
            <DistributionUnavailable />
          </div>
        </>
      ) : (
        <EmptyState
          title={
            failed
              ? 'UNKNOWN · rezultatele nu pot fi verificate'
              : 'Niciun rezultat finalizat în pagina citită'
          }
          href="/testeaza/nou"
          action="Pregătește un test"
        >
          Câștigul, pierderea și curba apar numai după un test finalizat și citirea dovezilor sale.
        </EmptyState>
      )}
    </section>
  );
}
export function DistributionUnavailable() {
  return (
    <aside className="panel" aria-label="Distribuția tranzacțiilor">
      <CardTitle title="Distribuția tranzacțiilor" icon={Target} />
      <EmptyState title="Numere exacte indisponibile">
        Rezumatul curent nu expune numărul exact de tranzacții câștigătoare, pierzătoare și neutre.
        Nu reconstruim aceste numere dintr-un procent rotunjit. Consultă tranzacțiile stocate în
        raportul detaliat.
      </EmptyState>
    </aside>
  );
}
