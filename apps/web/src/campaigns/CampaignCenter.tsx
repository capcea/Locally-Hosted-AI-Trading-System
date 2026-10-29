import { useRef, useState } from 'react';
import { FlaskConical } from 'lucide-react';
import { api, ApiError, safeError } from '../management-api';
import { useAuth } from '../auth/AuthProvider';
import { Link, navigate, useRoute } from '../navigation/history';
import { useOwnedRead } from '../v1/data';
import type { ResearchJob } from '../v1/data';
import { CardTitle, EmptyState, StatusPill } from '../v1/components';
import { Evidence } from '../ui/Controls';
import { campaignErrors, campaignStates, decisions, evaluationReasons } from './copy';

type Campaign = {
  id: string;
  digest: string;
  state: string;
  pending: string | null;
  reason: string | null;
  source: 'SYNTHETIC_FIXTURE' | 'AI_GATEWAY';
  paused: boolean;
  cancel_requested: boolean;
  cancellation_acknowledged: boolean;
  objective: {
    title: string;
    objective: string;
    budgets: Record<string, number>;
    template: unknown;
  };
  counts: {
    proposals: number;
    experiments: number;
    iterations: number;
    reserved_seconds: number;
    reserved_bytes: number;
  };
  deadline: string | null;
};
type Lineage = {
  id: string;
  sequence: number;
  kind: string;
  source: string;
  parent_id: string | null;
  payload: Record<string, unknown>;
  digest: string;
  previous_digest: string;
  created_at: string;
};

export default function CampaignCenter() {
  const { session } = useAuth();
  const route = useRoute();
  const [campaignOffset, setCampaignOffset] = useState(0);
  const campaigns = useOwnedRead<Campaign[]>(`/campaigns?offset=${campaignOffset}`, 3000);
  const selected = useOwnedRead<Campaign>(
    route.campaignId ? `/campaigns/${route.campaignId}` : null,
    2000,
  );
  const [offset, setOffset] = useState(0);
  const lineage = useOwnedRead<Lineage[]>(
    route.campaignId ? `/campaigns/${route.campaignId}/lineage?offset=${offset}` : null,
    2000,
  );
  const templates = useOwnedRead<ResearchJob[]>('/research/experiments?limit=100');
  const [title, setTitle] = useState('');
  const [question, setQuestion] = useState('');
  const [templateId, setTemplateId] = useState('');
  const [mode, setMode] = useState<'SYNTHETIC_FIXTURE' | 'AI_GATEWAY'>('SYNTHETIC_FIXTURE');
  const [phase, setPhase] = useState('DISCOVERY');
  const [domain, setDomain] = useState('');
  const [iterations, setIterations] = useState(2);
  const [experiments, setExperiments] = useState(12);
  const [proposals, setProposals] = useState(8);
  const [seconds, setSeconds] = useState(1800);
  const [ack, setAck] = useState(false);
  const [approveAck, setApproveAck] = useState(false);
  const [reviewedPlan, setReviewedPlan] = useState('');
  const [processing, setProcessing] = useState(false);
  const [remote, setRemote] = useState(false);
  const [cloudCost, setCloudCost] = useState(false);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState('');
  const key = useRef(crypto.randomUUID().replaceAll('-', ''));
  const owner = session?.state === 'FULL' && session.user.role === 'OWNER';
  const current = selected.data;
  const currentPlan = lineage.data?.filter((r) => r.kind === 'PLAN').at(-1);
  const refresh = () => window.dispatchEvent(new Event('research-display-refresh'));
  async function mutate(path: string, body: unknown) {
    if (!owner || busy || uncertain) return;
    setBusy(true);
    setError('');
    try {
      const result = await api<Campaign>(path, { method: 'POST', body, csrf: session.csrf_token });
      refresh();
      return result;
    } catch (e) {
      setError(safeError(e));
      if (!(e instanceof ApiError) || e.status >= 500) setUncertain(true);
    } finally {
      setBusy(false);
    }
  }
  async function reconcile() {
    setBusy(true);
    try {
      await api(route.campaignId ? `/campaigns/${route.campaignId}` : '/campaigns');
      setUncertain(false);
      refresh();
    } catch (e) {
      setError(safeError(e));
    } finally {
      setBusy(false);
    }
  }
  const disabled = !owner || busy || uncertain;
  const control = (action: string) => mutate(`/campaigns/${route.campaignId}/control`, { action });
  return (
    <section className="campaign-center" aria-label="Campanii de cercetare">
      <div className="panel">
        <CardTitle title="Cercetare cu limite clare" icon={FlaskConical} />
        <p>
          Pregătește ipoteze, testează numai strategii revizuite și urmărește dovezile. Fiecare
          trimitere de test sau analiză AI necesită revizuirea proprietarului și MFA recentă.
        </p>
        <p>
          <strong>
            SIMULATED / DENY_ALL · fără promovare, cod generat executabil sau ordine externe.
          </strong>
        </p>
        <nav className="inline-actions" aria-label="Pregătirea cercetării">
          <Link href="/testeaza/nou">Pregătește un test istoric</Link>
          <Link href="/testeaza/date">Verifică datele</Link>
          <Link href="/conturi/siguranta">Verifică siguranța</Link>
          <Link href="/setari/ai">Modele AI</Link>
        </nav>
        {!owner && (
          <p>
            Numai proprietarul poate crea și autoriza campanii. Rolul nu oferă acces la conturile
            altei persoane.
          </p>
        )}
        {error && (
          <p role="alert" className="error-banner">
            {error}
          </p>
        )}
        {uncertain && (
          <p role="alert">
            Nu putem confirma modificarea. Nu trimite o solicitare nouă; verifică înregistrările.
            Aceeași cheie de creare este păstrată până la confirmare.
          </p>
        )}
        <button className="secondary-button" disabled={busy} onClick={() => void reconcile()}>
          Verifică înregistrările
        </button>
      </div>
      {!route.campaignId && (
        <>
          <form
            className="panel management-form"
            aria-label="Campanie nouă"
            onSubmit={async (e) => {
              e.preventDefault();
              if (disabled || !templateId || !ack) return;
              setError('');
              try {
                const provenance = await api<{ plan: Record<string, unknown> }>(
                  `/research/experiments/${templateId}/provenance`,
                );
                const template = { ...provenance.plan, phase };
                const parameters = provenance.plan.parameters as unknown[];
                const allowed = domain.trim() ? JSON.parse(domain) : [parameters[0]];
                const row = await mutate('/campaigns', {
                  key: key.current,
                  objective: {
                    title,
                    objective: question,
                    mode,
                    template,
                    search_space: allowed,
                    budgets: {
                      candidate_proposals: proposals,
                      experiments,
                      iterations,
                      runtime_seconds: seconds,
                    },
                    acknowledged_owner_handoffs: true,
                    acknowledged_no_promotion: true,
                  },
                });
                if (row) {
                  key.current = crypto.randomUUID().replaceAll('-', '');
                  navigate(`/testeaza/campanii/${row.id}`);
                }
              } catch (e) {
                setError(safeError(e));
              }
            }}
          >
            <h2>Creează o campanie</h2>
            <label>
              Scopul cercetării
              <input
                required
                minLength={3}
                maxLength={120}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label>
              Ce vrei să verifici?
              <textarea
                required
                minLength={10}
                maxLength={2000}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
            </label>
            <label>
              Mod de cercetare
              <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
                <option value="SYNTHETIC_FIXTURE">
                  SYNTHETIC_FIXTURE · test determinist, fără inferență AI
                </option>
                <option value="AI_GATEWAY">
                  AI Gateway · necesită modele Research și Critic verificate
                </option>
              </select>
            </label>
            {mode === 'SYNTHETIC_FIXTURE' && (
              <p className="warning-banner">
                <strong>SYNTHETIC_FIXTURE</strong> · verifică infrastructura; nu demonstrează
                profitabilitate și nu produce candidați pentru paper/live.
              </p>
            )}
            <label>
              Configurație dintr-un test existent
              <select required value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
                <option value="">Alege o configurație revizuită</option>
                {templates.data
                  ?.filter((t) => t.phase !== 'FINAL_HOLDOUT')
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
              </select>
            </label>
            {!templates.data?.some((t) => t.phase !== 'FINAL_HOLDOUT') && (
              <p>
                Nu este disponibilă o configurație.{' '}
                <Link href="/testeaza/nou">Pregătește mai întâi un test istoric</Link>. Sunt
                necesare date admise, cont, simulator și politică verificată; nu le inventăm.
              </p>
            )}
            <label>
              Interval folosit
              <select
                value={phase}
                onChange={(e) => {
                  setPhase(e.target.value);
                  if (e.target.value !== 'DISCOVERY') setIterations(1);
                }}
              >
                <option value="DISCOVERY">Descoperire · în eșantion</option>
                <option value="CALIBRATION">Calibrare · o singură variantă</option>
                <option value="VALIDATION">Validare OOS · o singură variantă, fără retunare</option>
              </select>
            </label>
            <div className="research-fields">
              <label>
                Cel mult idei
                <input
                  type="number"
                  min={1}
                  max={8}
                  value={proposals}
                  onChange={(e) => setProposals(Number(e.target.value))}
                />
              </label>
              <label>
                Cel mult teste
                <input
                  type="number"
                  min={1}
                  max={12}
                  value={experiments}
                  onChange={(e) => setExperiments(Number(e.target.value))}
                />
              </label>
              <label>
                Cel mult iterații
                <input
                  type="number"
                  min={1}
                  max={phase === 'DISCOVERY' ? 2 : 1}
                  value={iterations}
                  onChange={(e) => setIterations(Number(e.target.value))}
                />
              </label>
              <label>
                Buget de timp (secunde)
                <input
                  type="number"
                  min={60}
                  max={7200}
                  value={seconds}
                  onChange={(e) => setSeconds(Number(e.target.value))}
                />
              </label>
            </div>
            <details>
              <summary>Parametri autorizați și limite exacte</summary>
              <p>
                Implicit reutilizăm parametrii testului ales. Poți autoriza cel mult opt variante
                finite, fără cod sau parametri necunoscuți. Calibrarea și validarea acceptă una
                singură. Maximum un test activ pe campanie; limitele Phase 5 rămân.
              </p>
              <label>
                Variante finite (JSON opțional)
                <textarea
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  maxLength={16000}
                />
              </label>
            </details>
            <label>
              <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
              Accept doar cercetare limitată, revizuire și MFA la trimiteri, fără promovare sau
              execuție externă.
            </label>
            <button disabled={disabled || !ack || !templateId}>Creează ciorna campaniei</button>
          </form>
          <section className="panel" aria-label="Campanii înregistrate">
            <h2>Campaniile tale</h2>
            {campaigns.failed ? (
              <p role="alert">UNKNOWN · lista nu poate fi verificată.</p>
            ) : campaigns.loading ? (
              <p role="status">Citim campaniile…</p>
            ) : !campaigns.data?.length ? (
              <EmptyState title="Nicio campanie încă">
                Începe cu o configurație revizuită. Nu există cercetare autonomă ascunsă.
              </EmptyState>
            ) : (
              <ul className="management-cards">
                {campaigns.data.map((c) => (
                  <li key={c.id}>
                    <Link href={`/testeaza/campanii/${c.id}`}>{c.objective.title}</Link> ·{' '}
                    {campaignStates[c.state] ?? 'UNKNOWN'} · {c.source}
                  </li>
                ))}
              </ul>
            )}
            <nav aria-label="Paginile campaniilor">
              <button
                type="button"
                disabled={campaignOffset === 0 || campaigns.loading}
                onClick={() => setCampaignOffset(Math.max(0, campaignOffset - 25))}
              >
                Pagina precedentă
              </button>
              <span>Pagina {Math.floor(campaignOffset / 25) + 1} · maximum 25 de înregistrări</span>
              <button
                type="button"
                disabled={campaigns.loading || campaigns.failed || campaigns.data?.length !== 25}
                onClick={() => setCampaignOffset(campaignOffset + 25)}
              >
                Pagina următoare
              </button>
            </nav>
          </section>
        </>
      )}
      {route.campaignId && (
        <>
          <Link href="/testeaza/campanii">Toate campaniile</Link>
          {selected.failed ? (
            <p role="alert">UNKNOWN · campania nu poate fi citită. Nu presupunem că s-a oprit.</p>
          ) : !current ? (
            <p role="status">Citim campania…</p>
          ) : (
            <>
              <section className="panel" aria-label="Progresul campaniei">
                <h2>{current.objective.title}</h2>
                <StatusPill>{current.source}</StatusPill>
                <h3>{campaignStates[current.state] ?? 'UNKNOWN'}</h3>
                <p>{current.objective.objective}</p>
                {current.paused && (
                  <p>
                    <strong>În pauză pentru lucru nou.</strong> Un test deja trimis poate continua.
                  </p>
                )}
                {current.cancel_requested && (
                  <p>
                    {current.cancellation_acknowledged
                      ? 'Oprirea cercetării a fost confirmată.'
                      : 'Oprire solicitată; așteptăm confirmarea lucrului activ.'}
                  </p>
                )}
                {current.reason && (
                  <p>
                    {campaignErrors[current.reason] ??
                      (current.reason === 'INSUFFICIENT_EVIDENCE'
                        ? 'Dovezi insuficiente. Campania s-a oprit fără a inventa un rezultat.'
                        : 'Verifică dovezile și configurația înainte de a continua.')}{' '}
                    <code>{current.reason}</code>
                  </p>
                )}
                <dl className="v1-facts">
                  <div>
                    <dt>Idei propuse</dt>
                    <dd>
                      {current.counts.proposals} / {current.objective.budgets.candidate_proposals}
                    </dd>
                  </div>
                  <div>
                    <dt>Teste trimise</dt>
                    <dd>
                      {current.counts.experiments} / {current.objective.budgets.experiments}
                    </dd>
                  </div>
                  <div>
                    <dt>Iterații</dt>
                    <dd>
                      {current.counts.iterations} / {current.objective.budgets.iterations}
                    </dd>
                  </div>
                </dl>
                {current.deadline && (
                  <p>
                    Autorizația expiră: <time dateTime={current.deadline}>{current.deadline}</time>.
                    Reluarea nu extinde bugetul.
                  </p>
                )}
                <Evidence title="Limite și configurație imuabilă" value={current.objective} />
                {current.state === 'DRAFT' && (
                  <button disabled={disabled} onClick={() => void control('REQUEST_APPROVAL')}>
                    Revizuiește autorizarea
                  </button>
                )}
                {current.pending === 'AUTHORIZE' && (
                  <div className="management-form">
                    <p>
                      Revizuiește contul, datele, parametrii, costurile și limitele de mai sus.
                      Autorizarea nu elimină MFA de la trimiteri.
                    </p>
                    <label>
                      <input
                        type="checkbox"
                        checked={approveAck}
                        onChange={(e) => setApproveAck(e.target.checked)}
                      />
                      Autorizez exact aceste limite, doar pentru cercetare, fără promovare.
                    </label>
                    <button
                      disabled={disabled || !approveAck}
                      onClick={() =>
                        void mutate(`/campaigns/${current.id}/approve`, {
                          expected_digest: current.digest,
                          acknowledged_bounded_research: true,
                          acknowledged_no_promotion: true,
                        })
                      }
                    >
                      Autorizează campania limitată
                    </button>
                  </div>
                )}
                {current.pending === 'SUBMIT_EXPERIMENT' && (
                  <div>
                    <p>
                      Revizuiește PLAN în istoric. Trimiterea folosește exact acel plan prin
                      verificările Phase 5 și MFA recentă.
                    </p>
                    <label>
                      <input
                        type="checkbox"
                        checked={Boolean(currentPlan && reviewedPlan === currentPlan.id)}
                        onChange={(e) =>
                          setReviewedPlan(e.target.checked && currentPlan ? currentPlan.id : '')
                        }
                      />
                      Am revizuit exact planul, datele, costurile și riscul acestui test.
                    </label>
                    <button
                      disabled={
                        disabled ||
                        current.paused ||
                        current.cancel_requested ||
                        !currentPlan ||
                        reviewedPlan !== currentPlan.id
                      }
                      onClick={() =>
                        void mutate(`/campaigns/${current.id}/submit-plan`, {
                          plan_id: currentPlan?.id,
                          expected_digest: currentPlan?.digest,
                          acknowledged_exact_plan: true,
                        })
                      }
                    >
                      Trimite testul revizuit
                    </button>
                  </div>
                )}
                {current.pending?.startsWith('REQUEST_') && current.source === 'AI_GATEWAY' && (
                  <div className="management-form">
                    <p>
                      Procesarea folosește exclusiv AI Gateway, cu modele și politici verificate.
                      Lipsa unui model nu activează fixtura.
                    </p>
                    <label>
                      <input
                        type="checkbox"
                        checked={processing}
                        onChange={(e) => setProcessing(e.target.checked)}
                      />
                      Accept procesarea contextului și păstrarea temporară a răspunsului structurat.
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={remote}
                        onChange={(e) => setRemote(e.target.checked)}
                      />
                      Permit procesarea la distanță numai dacă politica conexiunii o permite;
                      OpenRouter este cloud public.
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={cloudCost}
                        onChange={(e) => setCloudCost(e.target.checked)}
                      />
                      Aprob costul unei solicitări OpenRouter în limitele autorizate. Nu este
                      necesar pentru modele private.
                    </label>
                    <button
                      disabled={disabled || !processing}
                      onClick={() =>
                        void mutate(`/campaigns/${current.id}/gateway`, {
                          role: current.pending?.replace('REQUEST_', ''),
                          allow_remote: remote,
                          cloud_cost_acknowledged: cloudCost,
                          processing_acknowledged: true,
                          retain_structured_output: true,
                        })
                      }
                    >
                      Solicită propunerea AI revizuită
                    </button>
                  </div>
                )}
                {current.pending?.startsWith('ACCEPT_') && (
                  <button
                    disabled={disabled}
                    onClick={() => void mutate(`/campaigns/${current.id}/gateway/accept`, {})}
                  >
                    Verifică și admite propunerea structurată
                  </button>
                )}
                {!['DRAFT', 'COMPLETED', 'STOPPED', 'FAILED'].includes(current.state) && (
                  <div className="inline-actions">
                    <button
                      className="secondary-button"
                      disabled={disabled || current.cancel_requested}
                      onClick={() => void control(current.paused ? 'RESUME' : 'PAUSE')}
                    >
                      {current.paused ? 'Reautorizează reluarea' : 'Pauză pentru lucru nou'}
                    </button>
                    <button
                      className="danger-button"
                      disabled={disabled || current.cancel_requested}
                      onClick={() => void control('CANCEL')}
                    >
                      Solicită oprirea campaniei
                    </button>
                  </div>
                )}
                <p>
                  Concluziile sunt numai pentru cercetare. Nu modifică politicile de risc și nu
                  activează paper/demo/live.
                </p>
              </section>
              <section className="panel" aria-label="Istoricul cercetării">
                <h2>Ipoteză → test → dovezi → critică</h2>
                {lineage.failed && <p role="alert">UNKNOWN · istoricul nu poate fi citit.</p>}
                <ol>
                  {lineage.data?.map((item) => (
                    <li key={item.id}>
                      <h3>
                        {item.sequence}. {item.kind}
                      </h3>
                      {item.kind === 'EVALUATION' && (
                        <p>
                          <strong>
                            {decisions[String(item.payload.decision)] ?? 'Concluzie neconfirmată'}
                          </strong>
                        </p>
                      )}
                      {item.kind === 'EVALUATION' && Array.isArray(item.payload.reasons) && (
                        <ul>
                          {item.payload.reasons.map((reason, index) => (
                            <li key={index}>
                              {evaluationReasons[String(reason)] ??
                                'Verifică detaliile acestei limitări.'}
                            </li>
                          ))}
                        </ul>
                      )}
                      {item.kind === 'EVALUATION' && (
                        <p>
                          Încercările pot fi corelate. Reutilizarea perioadei de descoperire nu
                          devine validare independentă. Detaliile exacte rămân în dovezi.
                        </p>
                      )}
                      {item.kind === 'EXPERIMENT' && (
                        <Link href={`/testeaza/${String(item.payload.experiment_id)}/progres`}>
                          Deschide testul istoric asociat
                        </Link>
                      )}
                      <Evidence title="Dovezi și legături imuabile" value={item} />
                    </li>
                  ))}
                </ol>
                <div className="inline-actions">
                  <button
                    className="secondary-button"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 100))}
                  >
                    Înregistrări anterioare
                  </button>
                  <button
                    className="secondary-button"
                    disabled={!lineage.data || lineage.data.length < 100}
                    onClick={() => setOffset(offset + 100)}
                  >
                    Înregistrări următoare
                  </button>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </section>
  );
}
