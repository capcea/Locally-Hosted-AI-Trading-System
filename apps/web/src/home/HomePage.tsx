import { useEffect, useState } from 'react';
import type { Overview } from '../api';
import { readinessSummary } from '../api';
import { api } from '../management-api';
import { useAuth } from '../auth/AuthProvider';
import { Link } from '../navigation/history';
import { progressPath, resultPath } from '../navigation/routes';

export type JobSummary = {
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
export default function HomePage({
  overview,
  stale,
  refresh,
}: {
  overview: Overview | null;
  stale: boolean;
  refresh: () => void;
}) {
  const { session } = useAuth();
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (session?.state !== 'FULL') return;
    let current = true;
    let running = false;
    const load = async () => {
      if (running) return;
      running = true;
      try {
        const j = await api<JobSummary[]>('/research/experiments?limit=100');
        if (current) {
          setJobs(j);
          setFailed(false);
        }
      } catch {
        if (current) setFailed(true);
      } finally {
        running = false;
      }
    };
    void load();
    const timer = setInterval(() => void load(), 5000);
    return () => {
      current = false;
      clearInterval(timer);
    };
  }, [session?.user.id, session?.state]);
  const active = jobs?.filter((j) => ['QUEUED', 'RUNNING', 'RETRY'].includes(j.job.state));
  const complete = jobs?.filter((j) => j.job.state === 'SUCCEEDED');
  const attention = jobs?.filter((j) => j.job.state === 'FAILED');
  const readiness = overview ? readinessSummary(overview.services) : null;
  const available =
    !stale && readiness && readiness.total > 0 && readiness.healthy === readiness.total;
  return (
    <div className="home-content">
      <section className="hero-task panel">
        <span className="eyebrow">Cercetare cu dovezi</span>
        <h2>
          {session?.state === 'FULL'
            ? 'Următorul test începe cu date și limite revizuite.'
            : 'Înțelege o strategie înainte să iei o decizie.'}
        </h2>
        <p>
          Testează pe date istorice, urmărește riscul simulat și citește rezultatele cu limitele
          lor. Fără ordine reale și fără promisiuni de profit.
        </p>
        <Link
          className="primary-button"
          href={
            session?.state !== 'FULL'
              ? '/autentificare'
              : active?.length
                ? progressPath(active[0].id)
                : complete?.length
                  ? resultPath(complete[0].id)
                  : '/testeaza/nou'
          }
        >
          {session?.state !== 'FULL'
            ? 'Autentifică-te'
            : active?.length
              ? 'Vezi progresul'
              : complete?.length
                ? 'Vezi ultimul rezultat'
                : 'Testează o strategie'}
        </Link>
      </section>
      <section className="panel" aria-label="Disponibilitatea platformei">
        <h2>Funcționează platforma?</h2>
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
          Starea infrastructurii nu acordă permisiune de tranzacționare. Starea procesului de calcul
          nu este confirmată de acest rezumat.
        </p>
        <button className="secondary-button" onClick={refresh}>
          Actualizează starea publică
        </button>{' '}
        <Link href="/setari/diagnostic">Vezi diagnostic</Link>
      </section>
      {session?.state === 'FULL' ? (
        <>
          {failed && (
            <p role="alert" className="error-banner">
              UNKNOWN · nu putem reîncărca activitatea. Informațiile anterioare nu confirmă ce
              rulează acum.
            </p>
          )}
          <div className="overview-columns">
            <section className="panel" aria-label="Activitate reală">
              <h2>Ce se întâmplă acum?</h2>
              {jobs === null ? (
                <p role="status">Verificăm testele înregistrate…</p>
              ) : active?.length ? (
                <ul>
                  {active.map((j) => (
                    <li key={j.id}>
                      <Link href={progressPath(j.id)}>{j.name}</Link> · {j.job.state} ·{' '}
                      {j.job.progress}% raportat
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  {jobs.length === 100
                    ? 'Niciun test activ în ultimele 100 de înregistrări. Vezi istoricul pentru paginile anterioare.'
                    : 'Nu rulează teste în înregistrările citite.'}
                </p>
              )}
              <Link href="/testeaza/activitate">Vezi activitatea testelor</Link>
            </section>
            <section className="panel" aria-label="Rezultate recente">
              <h2>Ce rezultate pot citi?</h2>
              {complete?.length ? (
                <ul>
                  {complete.slice(0, 3).map((j) => (
                    <li key={j.id}>
                      <Link href={resultPath(j.id)}>{j.name}</Link> · execuție simulată · {j.phase}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  {jobs === null
                    ? 'Rezultatele nu sunt încă verificate.'
                    : 'Nu există rezultate finalizate în pagina citită.'}
                </p>
              )}
              <Link href="/rezultate">Toate rezultatele</Link>
            </section>
          </div>
          <section className="panel">
            <h2>Ce necesită atenție?</h2>
            <p>
              {failed
                ? 'Nu putem verifica activitatea.'
                : attention?.length
                  ? `${attention.length} teste oprite din cauza unei probleme în pagina citită.`
                  : jobs === null
                    ? 'Verificăm activitatea.'
                    : 'Nu sunt raportate teste eșuate în pagina citită. Verifică separat siguranța fiecărui cont.'}
            </p>
            <Link href="/conturi/siguranta">Verifică siguranța și eventualele opriri</Link>
          </section>
        </>
      ) : (
        <section className="panel">
          <h2>Ce urmează?</h2>
          <p>
            După autentificarea în doi pași poți vedea doar conturile și testele permise identității
            tale. Nu afișăm rezultate sau solduri presupuse.
          </p>
        </section>
      )}
    </div>
  );
}
