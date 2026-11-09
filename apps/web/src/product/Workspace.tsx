import { useState } from 'react';
import type { components } from '../generated/api';
import type { RecordItem, Session } from '../management-api';
import { api, safeError } from '../management-api';
import { Link, navigate } from '../navigation/history';
import { useOwnedRead } from '../v1/data';
import { Evidence } from '../ui/Controls';
import { AccountSafety } from '../v1/AccountSafety';
import { strategyLabels, jobLabels } from '../copy/ro';
import './workspace.css';
import AIChat from '../ai/AIChat';

type Candidate = {
  id: string;
  experiment_id: string;
  account_id: string;
  name: string;
  strategy: string;
  strategy_digest: string;
  limitations: string[];
  external_execution_authorized: false;
};
type Library = { items: Candidate[]; has_more: boolean; unavailable_count: number };
type Selection = {
  selection: null | {
    id: string;
    revision: number;
    available: boolean;
    candidate: Candidate | null;
    reason: string | null;
  };
  mode: 'SIMULATED';
};
type Job = {
  id: string;
  name: string;
  strategy: string;
  created_at: string;
  job: { state: string; progress: number; error: string | null } | null;
};
type AIStatus = { configured: boolean; worker_state: string; worker_expires_at: string | null };

export function LabOverview({ session }: { session?: Session } = {}) {
  const jobs = useOwnedRead<Job[]>('/research/experiments?limit=100', 10000);
  return (
    <div className="workspace-page lab-workspace">
      <header className="workspace-intro lab-intro">
        <span className="workspace-eyebrow">STRATEGY LAB · CERCETARE CU AI</span>
        <h2>De la o idee la o strategie testată</h2>
        <p>
          Spune-i modelului ce vrei să descopere. Revizuiești ideea, pregătești testul și compari
          dovezile.
        </p>
        <nav className="lab-flow" aria-label="Fluxul Strategy Lab">
          <Link href="/strategy-lab" aria-current="page">
            1. Idei cu AI
          </Link>
          <Link href="/strategy-lab/testeaza">2. Pregătește testul</Link>
          <Link href="/strategy-lab/rezultate">3. Citește rezultatele</Link>
          <Link href="/strategy-lab/biblioteca">Biblioteca validată</Link>
        </nav>
      </header>
      {session && <AIChat session={session} workspace />}
      <details className="panel lab-activity">
        <summary>Testele și rezultatele tale</summary>
        {jobs.failed ? (
          <p role="alert">Nu putem citi testele. Lista indisponibilă nu înseamnă că este goală.</p>
        ) : jobs.data ? (
          <>
            <p>{jobs.data.length} înregistrări în pagina citită (maximum 100).</p>
            {jobs.data.slice(0, 5).map((job) => (
              <div className="workspace-row" key={job.id}>
                <Link
                  href={
                    job.job?.state === 'SUCCEEDED'
                      ? `/rezultate/${job.id}`
                      : `/testeaza/${job.id}/progres`
                  }
                >
                  {job.name}
                </Link>
                <span>
                  {job.job ? (jobLabels[job.job.state] ?? job.job.state) : 'Rezultat necunoscut'}
                </span>
              </div>
            ))}
            {!jobs.data.length && (
              <p>Încă nu ai teste salvate. Începe prin a discuta o idee cu modelul.</p>
            )}
          </>
        ) : (
          <p role="status">Citim testele…</p>
        )}
        <div className="workspace-links">
          <Link href="/testeaza/activitate">Toată activitatea testelor</Link>
          <Link href="/strategy-lab/rezultate">Vezi rezultatele</Link>
          <Link href="/rezultate/compara">Compară două teste</Link>
        </div>
      </details>
      <details className="panel">
        <summary>Configurare manuală și instrumente avansate</summary>
        <div className="workspace-links">
          <Link href="/strategy-lab/idei">Deschide asistentul separat</Link>
          <Link href="/testeaza/strategii">Strategii de bază revizuite</Link>
          <Link href="/strategy-lab/testeaza">Test manual și parametri avansați</Link>
          <Link href="/testeaza/campanii">Cercetare cu AI în campanii limitate</Link>
          <Link href="/testeaza/date">Date istorice și calitate</Link>
          <Link href="/testeaza/date/import">Importă date</Link>
          <Link href="/testeaza/evaluare-finala">Evaluare finală protejată</Link>
          <Link href="/setari/ai">Modelul și autorizarea</Link>
        </div>
        <p>
          AI propune; motorul existent testează numai strategiile revizuite. O idee care cere logică
          nouă rămâne o propunere până când există o implementare revizuită.
        </p>
        <p>
          Rezultatele și biblioteca folosesc dovezile stocate, fără promovare automată. Antrenarea
          și validarea unui model specializat nu sunt încă implementate.
        </p>
      </details>
    </div>
  );
}

export function ValidatedLibrary() {
  const [page, setPage] = useState(0);
  const read = useOwnedRead<Library>(`/workspace/library?offset=${page * 20}&limit=20`, 15000);
  return (
    <section className="panel" aria-label="Biblioteca validată">
      <h2>Strategii cu dovezi pentru cercetare</h2>
      <p>
        Intră aici numai candidații confirmați prin evaluarea serverului: date admise, rezultate
        complete după costuri, validare cronologică și incertitudine analizată. Randamentul pozitiv
        singur nu este suficient.
      </p>
      {read.failed ? (
        <p role="alert">
          Nu putem verifica biblioteca acum. Reîncarcă pagina sau verifică serviciile în Settings.
        </p>
      ) : !read.data ? (
        <p role="status">Verificăm biblioteca…</p>
      ) : (
        <>
          {!read.data.items.length && (
            <div className="workspace-empty">
              <h3>Nicio strategie validată în această pagină</h3>
              <p>
                Modelele de bază și răspunsurile AI sunt puncte de pornire. Întâi trebuie testate pe
                date suficiente.
              </p>
              <Link className="primary-button" href="/strategy-lab/testeaza">
                Testează o strategie
              </Link>
            </div>
          )}
          {read.data.unavailable_count > 0 && (
            <p role="alert">
              {read.data.unavailable_count} înregistrări nu pot fi revalidate. Nu le prezentăm drept
              disponibile.
            </p>
          )}
          {read.data.items.map((item) => (
            <article className="workspace-library-card" key={item.id}>
              <h3>{item.name}</h3>
              <p>
                {strategyLabels[item.strategy] ?? item.strategy} · candidat de cercetare · fără
                ordine externe.
              </p>
              <Link href={`/rezultate/${item.experiment_id}`}>Rezultat și dovezi</Link>
              <Link href="/">Configurează contul în Trading Dashboard</Link>
              <Evidence title="Versiune, limite și proveniență" value={item} />
            </article>
          ))}
          <div className="workspace-actions">
            <button disabled={!page} onClick={() => setPage((p) => p - 1)}>
              Pagina anterioară
            </button>
            <button disabled={!read.data.has_more} onClick={() => setPage((p) => p + 1)}>
              Pagina următoare
            </button>
          </div>
        </>
      )}
    </section>
  );
}

export function TradingDashboard({
  session,
  accounts,
  accountId,
  accountsReady,
  accountsFailed,
  choose,
}: {
  session: Session;
  accounts: RecordItem[];
  accountId: string;
  accountsReady: boolean;
  accountsFailed: boolean;
  choose: (id: string) => void;
}) {
  const risk = useOwnedRead<components['schemas']['AccountStatus']>(
    accountId ? `/risk/accounts/${accountId}/status` : null,
    10000,
  );
  const activity = useOwnedRead<Job[]>('/research/experiments?limit=100', 10000);
  const ai = useOwnedRead<AIStatus>('/ai/status', 10000);
  const aiActivity = useOwnedRead<{ id: string; kind: string; state: string }[]>(
    '/ai/requests',
    4000,
  );
  const [candidatePage, setCandidatePage] = useState(0);
  const library = useOwnedRead<Library>(
    accountId
      ? `/workspace/library?limit=50&offset=${candidatePage * 50}&account_id=${accountId}`
      : null,
    15000,
  );
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [chosen, setChosen] = useState('');
  const [simulationKey, setSimulationKey] = useState<string | null>(null);
  const selectionRefresh = useOwnedRead<Selection>(
    accountId ? `/workspace/accounts/${accountId}/strategy?read=${revision}` : null,
    10000,
  );
  const current = selectionRefresh.data;
  const status = risk.data;
  const fresh =
    status?.monitor_at &&
    Date.now() - Date.parse(status.monitor_at) >= 0 &&
    Date.now() - Date.parse(status.monitor_at) < 30000 &&
    status.data_verified &&
    status.ledger_verified;
  const values = fresh ? status?.values : null;
  const account = accounts.find((item) => item.id === accountId);
  const running = (activity.data ?? []).filter((item) =>
    ['QUEUED', 'RUNNING', 'RETRY'].includes(item.job?.state ?? 'UNKNOWN'),
  );
  const worker =
    ai.data?.worker_state === 'OBSERVED_RECENTLY' &&
    Date.parse(ai.data.worker_expires_at ?? '') > Date.now();
  const candidates = (library.data?.items ?? []).filter((item) => item.account_id === accountId);
  const chosenCandidate = candidates.find((item) => item.id === chosen);
  async function save() {
    if (!accountId || !chosenCandidate || busy || library.failed || library.loading) return;
    setBusy(true);
    setError('');
    try {
      await api(`/workspace/accounts/${accountId}/strategy`, {
        method: 'POST',
        csrf: session.csrf_token,
        body: { decision_id: chosen },
      });
      setRevision((r) => r + 1);
      setSimulationKey(null);
    } catch (failure) {
      setError(safeError(failure));
    } finally {
      setBusy(false);
    }
  }
  async function simulate() {
    if (!accountId || busy || !current?.selection?.available) return;
    const key = simulationKey ?? crypto.randomUUID().replaceAll('-', '');
    setSimulationKey(key);
    setBusy(true);
    setError('');
    try {
      const job = await api<{ id: string }>(`/workspace/accounts/${accountId}/simulate`, {
        method: 'POST',
        csrf: session.csrf_token,
        body: { key, acknowledged_historical_simulation: true },
      });
      setSimulationKey(null);
      navigate(`/testeaza/${job.id}/progres`);
    } catch (failure) {
      setError(safeError(failure));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="workspace-page" role="region" aria-label="Trading Dashboard">
      <section className="panel workspace-intro">
        <span className="workspace-eyebrow">CONT → STRATEGIE → REZULTATE</span>
        <h2>Conturile și activitatea ta, într-un singur loc</h2>
        <p>
          Alege contul, urmărește rezultatele disponibile și verifică strategia selectată. În
          această versiune execuția este simulată; traderul continuu conectat la broker nu este
          implementat.
        </p>
        <Link
          className="primary-button"
          href={accounts.length ? '/strategy-lab' : '/setari/conturi'}
        >
          {accounts.length ? 'Dezvoltă sau testează o strategie' : 'Adaugă primul cont'}
        </Link>
      </section>
      <div className="workspace-grid">
        <section className="panel">
          <h3>Contul selectat</h3>
          <label>
            Alege contul
            <select
              aria-label="Contul pentru trading"
              value={accountId}
              disabled={busy}
              onChange={(event) => {
                choose(event.target.value);
                setChosen('');
                setCandidatePage(0);
                setSimulationKey(null);
              }}
            >
              <option value="">
                {accountsFailed
                  ? 'Lista conturilor nu este disponibilă'
                  : !accountsReady
                    ? 'Citim conturile…'
                    : 'Alege un cont'}
              </option>
              {accounts.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.data.name}
                </option>
              ))}
            </select>
          </label>
          <p>
            {account
              ? `${account.data.name} · capital configurat pentru simulare`
              : 'Sumele sunt specifice unui cont; nu agregăm conturi și monede diferite.'}
          </p>
          <Link href="/setari/conturi">Gestionează conturile</Link>
        </section>
        <section className="panel workspace-feed" aria-label="Ce face AI-ul acum">
          <h3>Ce face sistemul acum</h3>
          {activity.failed ? (
            <p role="alert">Activitatea nu poate fi verificată.</p>
          ) : running.length ? (
            <>
              <p>{running.length} teste în curs în pagina citită.</p>
              {running.slice(0, 3).map((job) => (
                <div className="workspace-row" key={job.id}>
                  <Link href={`/testeaza/${job.id}/progres`}>{job.name}</Link>
                  <span>
                    {job.job ? (jobLabels[job.job.state] ?? job.job.state) : 'Rezultat necunoscut'}
                  </span>
                </div>
              ))}
            </>
          ) : (
            <p>
              {activity.data ? 'Nu există teste în curs în pagina citită.' : 'Citim activitatea…'}
            </p>
          )}
          {activity.data?.some((job) => !job.job) && (
            <p role="alert">Unele teste nu au o stare de procesare confirmată.</p>
          )}
          {(aiActivity.data ?? [])
            .filter(
              (job) => job.kind === 'INFER' && ['QUEUED', 'RUNNING', 'RETRY'].includes(job.state),
            )
            .map((job) => (
              <p key={job.id}>
                <Link href={`/testeaza/ai/${job.id}`}>
                  Analiză AI: {jobLabels[job.state] ?? job.state}
                </Link>
              </p>
            ))}
          <p>
            Worker AI: {worker ? 'heartbeat recent confirmat' : 'disponibilitate neconfirmată'}.
            Acest statut nu înseamnă că un model tranzacționează.
          </p>
          <Link href="/strategy-lab/idei">Lucrează cu modelul</Link>
        </section>
      </div>
      <section className="workspace-metrics" aria-label="Statistici ale contului simulat">
        {[
          ['PnL realizat', values?.realized_pnl],
          ['PnL deschis', values?.unrealized_pnl],
          ['Capital simulat', values?.equity],
          ['Poziții deschise', values?.position_count],
        ].map(([label, value]) => (
          <div className="panel" key={String(label)}>
            <span>{label}</span>
            <strong>
              {value == null ? '—' : String(value)}{' '}
              {value != null && label !== 'Poziții deschise' ? status?.currency : ''}
            </strong>
            <small>
              {fresh ? 'Ultima observație verificată · SIMULATED' : 'Date curente neconfirmate'}
            </small>
          </div>
        ))}
      </section>
      <div className="workspace-grid">
        <section className="panel">
          <h3>Strategia contului</h3>
          {selectionRefresh.failed ? (
            <p role="alert">
              Nu putem citi strategia contului. Reîncarcă starea înainte de a continua.
            </p>
          ) : selectionRefresh.loading ? (
            <p role="status">Citim selecția contului…</p>
          ) : current?.selection?.available ? (
            <>
              <p>{current.selection.candidate?.name}</p>
              <p>
                Selecție salvată · versiunea {current.selection.revision}. Configurarea nu activează
                ordine reale.
              </p>
            </>
          ) : (
            <p>
              {current?.selection
                ? 'Dovezile strategiei selectate nu mai pot fi confirmate.'
                : 'Nicio strategie validată selectată.'}
            </p>
          )}
          <label>
            Strategii validate pentru acest cont
            <select
              aria-label="Strategia validată a contului"
              value={chosen}
              onChange={(event) => setChosen(event.target.value)}
              disabled={!candidates.length || busy}
            >
              <option value="">
                {library.failed
                  ? 'Biblioteca nu poate fi citită'
                  : !accountId
                    ? 'Alege mai întâi un cont'
                    : library.loading
                      ? 'Citim strategiile…'
                      : candidates.length
                        ? 'Alege strategia'
                        : 'Nicio strategie disponibilă în această pagină'}
              </option>
              {candidates.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          {library.data?.has_more && (
            <p>Există și alte strategii pentru acest cont. Continuă în pagina următoare.</p>
          )}
          {accountId && (
            <div className="workspace-actions" aria-label="Paginile strategiilor contului">
              <button
                disabled={busy || !candidatePage}
                onClick={() => {
                  setChosen('');
                  setCandidatePage((p) => p - 1);
                }}
              >
                Strategii anterioare
              </button>
              <span>Pagina {candidatePage + 1}</span>
              <button
                disabled={busy || library.loading || !library.data?.has_more}
                onClick={() => {
                  setChosen('');
                  setCandidatePage((p) => p + 1);
                }}
              >
                Strategii următoare
              </button>
            </div>
          )}
          {(library.data?.unavailable_count ?? 0) > 0 && (
            <p role="alert">
              Unele dovezi nu pot fi revalidate; acei candidați nu pot fi selectați.
            </p>
          )}
          <button
            disabled={
              busy ||
              !chosenCandidate ||
              library.failed ||
              library.loading ||
              session.user.role !== 'OWNER'
            }
            onClick={() => void save()}
          >
            Salvează strategia contului
          </button>
          <p>
            Simularea folosește perioada și datele istorice fixate și trece din nou prin validările
            de cercetare și risc.
          </p>
          <button
            className="primary-button"
            disabled={busy || !current?.selection?.available || session.user.role !== 'OWNER'}
            onClick={() => void simulate()}
          >
            Pornește simularea istorică
          </button>
          {!current?.selection?.available && (
            <p>
              Butonul devine disponibil după selectarea unui candidat cu dovezi suficiente pentru
              acest cont.
            </p>
          )}
          <p>Trading automat la broker: indisponibil în această versiune · SIMULATED / DENY_ALL.</p>
          {error && <p role="alert">{error}</p>}
          <Link href="/strategy-lab/biblioteca">Vezi biblioteca și criteriile</Link>
        </section>
        <AccountSafety accountId={accountId} />
      </div>
    </div>
  );
}
