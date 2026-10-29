import { useState } from 'react';
import {
  Activity,
  ArrowRight,
  ChartNoAxesCombined,
  Database,
  FlaskConical,
  Layers,
  Lightbulb,
  ShieldCheck,
  Sparkles,
  Target,
} from 'lucide-react';
import type { Overview } from '../api';
import { readinessSummary } from '../api';
import { useAuth } from '../auth/AuthProvider';
import { Link } from '../navigation/history';
import { progressPath, resultPath } from '../navigation/routes';
import { jobLabels, strategyLabels } from '../copy/ro';
import { CardTitle, EmptyState, Kpi, StatusPill } from '../v1/components';
import { useOwnedRead } from '../v1/data';
import type { ResearchJob, ReviewedStrategy } from '../v1/data';
import { ExperimentPreview } from '../v1/ExperimentPreview';
import { AIQuickCard } from '../v1/AIWidgets';
import { AccountSafety } from '../v1/AccountSafety';

export type JobSummary = ResearchJob;
export default function HomePage({
  overview,
  stale,
  refresh,
  accountId = '',
}: {
  overview: Overview | null;
  stale: boolean;
  refresh: () => void;
  accountId?: string;
}) {
  const { session } = useAuth();
  const jobs = useOwnedRead<ResearchJob[]>('/research/experiments?limit=100', 5000);
  const strategies = useOwnedRead<ReviewedStrategy[]>('/research/strategies');
  const [chosen, setChosen] = useState('');
  const complete = jobs.data?.filter((j) => j.job.state === 'SUCCEEDED') ?? [];
  const active =
    jobs.data?.filter((j) => ['QUEUED', 'RUNNING', 'RETRY'].includes(j.job.state)) ?? [];
  const failed = jobs.data?.filter((j) => j.job.state === 'FAILED') ?? [];
  const selected = complete.find((j) => j.id === chosen) ?? complete[0];
  const readiness = overview ? readinessSummary(overview.services) : null;
  const full = session?.state === 'FULL';
  const available =
    !stale && readiness && readiness.total > 0 && readiness.healthy === readiness.total;
  const counted = (n: number | undefined) => (n === undefined ? '—' : String(n));
  const workflow = [
    {
      label: 'Date',
      description: 'Istoric admis și origine verificabilă',
      href: '/testeaza/date',
      icon: Database,
    },
    {
      label: 'Strategie',
      description: 'Alege un etalon revizuit',
      href: '/testeaza/strategii',
      icon: Lightbulb,
    },
    {
      label: 'Risc',
      description: 'Revizuiește limitele contului',
      href: '/conturi/siguranta',
      icon: ShieldCheck,
    },
    {
      label: 'Testare',
      description: 'Simulare pe date istorice',
      href: '/testeaza/nou',
      icon: FlaskConical,
    },
    {
      label: 'Rezultate',
      description: 'Citește rezultatul și limitele',
      href: '/rezultate',
      icon: ChartNoAxesCombined,
    },
    {
      label: 'AI',
      description: 'Propuneri și critică, fără autoritate',
      href: '/testeaza/ai',
      icon: Sparkles,
    },
  ];
  return (
    <div className="home-content v1-home">
      <div className="v1-kpis">
        <Kpi
          label="Experimente citite"
          value={counted(jobs.data?.length)}
          help={
            jobs.failed
              ? 'UNKNOWN · istoricul nu poate fi citit'
              : full
                ? 'Pagina recentă · maximum 100'
                : 'Autentifică-te pentru testele tale'
          }
          icon={FlaskConical}
        />
        <Kpi
          label="Strategii de bază"
          value={counted(strategies.data?.length)}
          help="Bibliotecă revizuită, fără strategii live"
          icon={Layers}
          tone="violet"
        />
        <Kpi
          label="Teste finalizate"
          value={jobs.data ? complete.length : '—'}
          help="În pagina citită · nu un scor de succes"
          icon={ChartNoAxesCombined}
          tone="green"
        />
        <Kpi
          label="Risc și siguranță"
          value={accountId ? 'Pe cont' : 'UNKNOWN'}
          help={
            accountId ? 'Vezi observația și limitele mai jos' : 'Alege un cont pentru verificare'
          }
          icon={ShieldCheck}
          tone="amber"
          valueKind="status"
        />
      </div>
      {jobs.failed && (
        <p className="error-banner" role="alert">
          UNKNOWN · activitatea nu poate fi reîncărcată. Nu presupunem că testele s-au încheiat sau
          că lipsesc.
        </p>
      )}
      <div className="v1-home-grid">
        <div className="v1-home-main">
          <section className="panel v1-home-performance" aria-label="Rezultate recente">
            <CardTitle title="Performanța experimentului selectat" icon={ChartNoAxesCombined} />
            {selected ? (
              <>
                <label className="v1-select-inline">
                  Experiment finalizat
                  <select
                    aria-label="Experiment finalizat"
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
                <ExperimentPreview key={selected.id} id={selected.id} compact />
              </>
            ) : (
              <EmptyState
                title={
                  jobs.loading ? 'Citim experimentele tale…' : 'Primul rezultat începe cu un test'
                }
                icon={ChartNoAxesCombined}
                href={full ? '/testeaza/nou' : '/autentificare'}
                action={full ? 'Testează o strategie' : 'Autentifică-te'}
              >
                Nu afișăm rezultate sau solduri presupuse. Curba va reprezenta un singur experiment
                finalizat, cu costuri și date fixate.
              </EmptyState>
            )}
          </section>
          <div className="v1-home-secondary">
            <section className="panel v1-home-recent" aria-label="Activitate reală">
              <CardTitle title="Experimente recente" icon={FlaskConical}>
                <Link href="/testeaza/activitate">
                  Vezi toate <ArrowRight size={15} aria-hidden="true" />
                </Link>
              </CardTitle>
              {jobs.data?.length ? (
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Experimente recente stocate"
                  tabIndex={0}
                >
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Experiment</th>
                        <th scope="col">Strategie</th>
                        <th scope="col">Stare</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.data.slice(0, 5).map((j) => (
                        <tr key={j.id}>
                          <td>
                            <Link
                              href={
                                j.job.state === 'SUCCEEDED' ? resultPath(j.id) : progressPath(j.id)
                              }
                            >
                              {j.name}
                            </Link>
                          </td>
                          <td>{strategyLabels[j.strategy] ?? j.strategy}</td>
                          <td>
                            <StatusPill>
                              {j.job.cancel_requested &&
                              ['QUEUED', 'RUNNING', 'RETRY'].includes(j.job.state)
                                ? 'Anulare solicitată'
                                : (jobLabels[j.job.state] ?? 'UNKNOWN')}
                            </StatusPill>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState
                  title={jobs.loading ? 'Verificăm activitatea…' : 'Niciun experiment de afișat'}
                  icon={FlaskConical}
                >
                  După primul test, istoricul și rezultatele sale apar aici.{' '}
                  {full
                    ? 'Nu rulează teste în înregistrările citite.'
                    : 'Sunt necesare parola și MFA pentru datele tale.'}
                </EmptyState>
              )}
              {active.length > 0 && (
                <p>
                  {active.length} teste active în pagina citită. Procentele și confirmarea anulării
                  sunt în progresul fiecărui test.
                </p>
              )}
              {jobs.data?.length === 100 && (
                <p>
                  Lista este limitată la 100 înregistrări. Verifică și paginile mai vechi din
                  istoric.
                </p>
              )}
            </section>
            <AccountSafety accountId={accountId} />
          </div>
        </div>
        <div className="v1-home-aside">
          <AIQuickCard />
          <section className="panel v1-home-next" aria-label="Următoarele acțiuni">
            <CardTitle title="Următoarele acțiuni" icon={Target} />
            <ul className="v1-next-links">
              {active[0] && (
                <li>
                  <Link href={progressPath(active[0].id)}>
                    <Activity size={17} />
                    Urmărește {active[0].name}
                    <ArrowRight size={15} />
                  </Link>
                </li>
              )}
              {selected && (
                <li>
                  <Link href={resultPath(selected.id)}>
                    <ChartNoAxesCombined size={17} />
                    Citește ultimul rezultat
                    <ArrowRight size={15} />
                  </Link>
                </li>
              )}
              {failed.length > 0 && (
                <li>
                  <Link href="/testeaza/activitate">
                    <Activity size={17} />
                    Verifică {failed.length} teste eșuate din pagina citită
                    <ArrowRight size={15} />
                  </Link>
                </li>
              )}
              <li>
                <Link href="/testeaza/date/import">
                  <Database size={17} />
                  Verifică sau adaugă date istorice
                  <ArrowRight size={15} />
                </Link>
              </li>
              <li>
                <Link href="/setari/ai">
                  <Sparkles size={17} />
                  Revizuiește modelele AI
                  <ArrowRight size={15} />
                </Link>
              </li>
              <li>
                <Link href={full ? '/testeaza/nou' : '/autentificare'}>
                  <FlaskConical size={17} />
                  {full ? 'Pregătește un test nou' : 'Autentificare în doi pași'}
                  <ArrowRight size={15} />
                </Link>
              </li>
            </ul>
            <details aria-label="Disponibilitatea platformei">
              <summary>Funcționează platforma?</summary>
              <p>
                <strong>
                  {stale || !overview
                    ? 'UNKNOWN · nu putem verifica acum'
                    : available
                      ? 'Serviciile de bază sunt disponibile'
                      : 'Unele servicii necesită atenție'}
                </strong>
              </p>
              <p>
                Starea infrastructurii nu acordă permisiune de tranzacționare. Starea procesului de
                calcul se verifică separat.
              </p>
            </details>
            <div className="inline-actions">
              <button className="secondary-button" onClick={refresh}>
                Actualizează starea publică
              </button>
              <Link href="/setari/diagnostic">Vezi diagnostic</Link>
            </div>
          </section>
        </div>
      </div>
      <section className="panel v1-workflow" aria-label="Fluxul de cercetare">
        <CardTitle title="Fluxul de cercetare · de la idee la dovezi" icon={Layers} />
        <ol>
          {workflow.map((item, i) => {
            const Icon = item.icon;
            return (
              <li key={item.label}>
                <Link href={item.href}>
                  <span className="v1-icon">
                    <Icon size={23} aria-hidden="true" />
                  </span>
                  <span>
                    <strong>
                      {i + 1}. {item.label}
                    </strong>
                    <small>{item.description}</small>
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
        <p>
          Niciun pas nu acordă automat eligibilitate. Datele, riscul și modelele se verifică în
          fluxul lor.
        </p>
      </section>
    </div>
  );
}
