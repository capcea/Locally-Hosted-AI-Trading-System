import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowUp, BrainCircuit, Clock3, MessageSquareText, Plus, Settings2 } from 'lucide-react';
import { api, safeError } from '../management-api';
import type { Session } from '../management-api';
import { Link, navigate, useRoute } from '../navigation/history';
import { Evidence } from '../ui/Controls';
import { active, ai, roleLabels, roles, stateLabels, verified } from './api';
import type { Binding, Connection, Job, Model, Role, Submission } from './api';
import { aiErrors } from './copy';
import { takeAIQuestion, takeExperimentReview } from './draft';
import { useInferenceReadiness } from './useInferenceReadiness';
import { inferenceUnavailable, observationFresh, workerObserved } from './readiness';
import { verifiedContextWindow, afterSubmissionFailure } from './submission-budget';
import './ai-chat.css';
import { ContextBudgetControl, useContextPreview } from './ContextBudget';
import type { ContextMode } from './ContextBudget';
import { researchIdea } from './research-idea';
import { offerResearchIdea } from '../research-drafts';

type ReferenceKind = 'documentation' | 'dataset' | 'experiment' | 'strategy' | 'ai_artifact';

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asStrings(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : [];
}

/** Technical discovery/probe jobs are never treated as chat replies. */
export function analysisJobs(jobs: Job[]): Job[] {
  return jobs.filter((job) => job.kind === 'INFER');
}

export function ResponseContent({
  job,
  onCritic,
  onTest,
}: {
  job: Job;
  onCritic: (job: Job) => void;
  onTest?: (job: Job) => void;
}) {
  const output = asObject(job.output);
  const missing = asStrings(asObject(output.missing_evidence).items);
  return (
    <section className="ai-chat-response" aria-label="Răspuns AI neverificat">
      <div className="ai-chat-response-heading">
        <BrainCircuit size={18} aria-hidden="true" />
        <strong>{typeof output.title === 'string' ? output.title : 'Răspuns AI'}</strong>
      </div>
      <p className="ai-chat-disclaimer">
        Propunere AI neverificată. Nu reprezintă un semnal de tranzacționare sau autorizare de
        ordine.
      </p>
      {['summary', 'hypothesis'].map(
        (key) => typeof output[key] === 'string' && <p key={key}>{output[key]}</p>,
      )}
      {[
        ['test_plan', 'Plan de testare'],
        ['objections', 'Puncte slabe'],
        ['suggested_tests', 'Teste sugerate'],
      ].map(([key, title]) => {
        const items = asStrings(output[key]);
        return items.length ? (
          <section key={key} className="ai-chat-answer-section">
            <h4>{title}</h4>
            <ul>
              {items.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null;
      })}
      {missing.length > 0 && (
        <section className="ai-chat-answer-section">
          <h4>Dovezi lipsă</h4>
          <ul>
            {missing.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </section>
      )}
      {asStrings(output.evidence_refs).length > 0 && (
        <section className="ai-chat-answer-section">
          <h4>Referințe citate (neverificate automat)</h4>
          <ul>
            {asStrings(output.evidence_refs).map((ref, index) => (
              <li key={index}>{ref}</li>
            ))}
          </ul>
        </section>
      )}
      {typeof output.candidate_source === 'string' && (
        <details className="ai-chat-details">
          <summary>Cod propus · nu a fost executat</summary>
          <pre>{output.candidate_source}</pre>
        </details>
      )}
      <div className="ai-chat-response-actions">
        {onTest && researchIdea(job) && (
          <button type="button" className="primary-button" onClick={() => onTest(job)}>
            Pregătește testul acestei idei
          </button>
        )}
        <button type="button" className="secondary-button" onClick={() => onCritic(job)}>
          Cere o critică separată
        </button>
        <details className="ai-chat-details">
          <summary>Metadate și cost</summary>
          <Evidence title="Detalii ale modelului și solicitării" value={job.metadata} />
        </details>
      </div>
    </section>
  );
}

export default function AIChat({
  session,
  workspace = false,
}: {
  session: Session;
  workspace?: boolean;
}) {
  const route = useRoute();
  const analysisHome = workspace ? '/strategy-lab' : '/testeaza/ai';
  const analysisPath = (id: string) =>
    workspace
      ? `/strategy-lab/analize/${encodeURIComponent(id)}`
      : `/testeaza/ai/${encodeURIComponent(id)}`;
  const [models, setModels] = useState<Model[]>([]);
  const [bindings, setBindings] = useState<Binding[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [question, setQuestion] = useState('');
  const [role, setRole] = useState<Role>('RESEARCH');
  const [reference, setReference] = useState('');
  const [referenceKind, setReferenceKind] = useState<ReferenceKind>('documentation');
  const [allowFallback, setAllowFallback] = useState(false);
  const [contextMode, setContextMode] = useState<ContextMode>('AUTO');
  const [preview, setPreview] = useState<{ id: string; question: string } | null>(null);
  const frozen = useRef<Submission | null>(null);
  const category = reference ? referenceKind : 'documentation';
  const { observation, now, refreshReadiness } = useInferenceReadiness(role, category);

  const refresh = useCallback(async () => {
    const reads = await Promise.allSettled([
      ai<Model[]>('/models'),
      ai<Binding[]>('/routes'),
      ai<Job[]>('/requests'),
      ai<Connection[]>('/connections'),
    ] as const);
    const [m, b, j, c] = reads;
    setModels(m.status === 'fulfilled' ? m.value : []);
    setBindings(b.status === 'fulfilled' ? b.value : []);
    setJobs(j.status === 'fulfilled' ? j.value : []);
    setConnections(c.status === 'fulfilled' ? c.value : []);
    if (reads.some((result) => result.status === 'rejected')) {
      setError('Nu am putut încărca toate informațiile AI. Verifică serviciile și reîncarcă.');
    } else {
      setError('');
    }
  }, []);

  useEffect(() => {
    let alive = true;
    void refresh().finally(() => {
      if (alive) setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [refresh]);

  useEffect(() => {
    const handoff = takeAIQuestion(session.user.id);
    if (handoff) {
      setQuestion(handoff);
      setShowNew(true);
      const experiment = takeExperimentReview(session.user.id);
      if (experiment) {
        setRole('CRITIC');
        setReferenceKind('experiment');
        setReference(experiment);
      }
    }
  }, [session.user.id]);

  const selectedId = route.jobId ?? null;
  useEffect(() => {
    if (!selectedId || jobs.some((job) => job.id === selectedId)) return;
    let alive = true;
    void ai<Job>('/requests/' + encodeURIComponent(selectedId))
      .then((job) => {
        if (alive) setJobs((previous) => [job, ...previous.filter((item) => item.id !== job.id)]);
      })
      .catch((reason: unknown) => {
        if (alive) setError(safeError(reason));
      });
    return () => {
      alive = false;
    };
  }, [selectedId, jobs]);

  const pending = jobs.some(active);
  useEffect(() => {
    if (!pending) return;
    let alive = true;
    const timer = window.setInterval(() => {
      void ai<Job[]>('/requests')
        .then((latest) => {
          if (alive) {
            setJobs((previous) => {
              const merged = new Map(previous.map((job) => [job.id, job]));
              latest.forEach((job) => merged.set(job.id, job));
              return [...merged.values()].sort((a, b) => b.created_at.localeCompare(a.created_at));
            });
          }
        })
        .catch((reason: unknown) => {
          if (alive) setError(safeError(reason));
        });
    }, 2000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [pending]);

  const analyses = analysisJobs(jobs).sort((a, b) => b.created_at.localeCompare(a.created_at));
  const selected = selectedId
    ? jobs.find((job) => job.id === selectedId)
    : showNew
      ? undefined
      : analyses[0];
  const binding = bindings.find((item) => item.role === role);
  const contextWindow = verifiedContextWindow(models, binding, allowFallback, now);
  const model = models.find((item) => item.id === binding?.model_id);
  const connection = connections.find((item) => item.id === model?.connection_id);
  const cloud = connection?.provider === 'OPENROUTER';
  const verifiedModel =
    model &&
    verified(model) &&
    observationFresh(observation, role, category, now) &&
    observation?.value.model_verified &&
    observation.value.model_id === model.id;
  const unavailable =
    session.user.role !== 'OWNER'
      ? 'Numai proprietarul autentificat poate solicita o analiză.'
      : inferenceUnavailable(observation, role, category, now) ||
        (contextWindow === null
          ? 'Capacitatea verificată a modelului nu este disponibilă. Reîncarcă registrul sau verifică modelul în Setări.'
          : null);
  const draft: Submission = {
    schema_version: 1,
    key: 'preview-no-reservation',
    question,
    role,
    context_mode: contextMode,
    references: reference
      ? [{ kind: referenceKind, id: reference }]
      : [{ kind: 'documentation', id: workspace ? 'strategy-lab-v1' : 'research-limits-v1' }],
    parameters: {
      context_tokens: contextWindow ?? 1024,
      output_tokens: 768,
      temperature: 0,
      top_p: 1,
      reasoning: 'DEFAULT',
      max_seconds: 90,
    },
    standing_authorization_id: observation?.value.standing_authorization_id ?? null,
    allow_fallback: allowFallback,
  };
  const contextPreview = useContextPreview(
    question.trim().length >= 3 && !unavailable ? (frozen.current ?? draft) : null,
    session.csrf_token,
  );
  const canSubmit =
    !busy && !loading && !unavailable && question.trim().length >= 3 && question.length <= 4000;

  function newAnalysis() {
    setShowNew(true);
    setPreview(null);
    navigate(analysisHome);
  }

  function selectAnalysis(id: string) {
    setShowNew(false);
    navigate(analysisPath(id));
  }

  function criticDraft(job: Job) {
    setRole('CRITIC');
    setReferenceKind('ai_artifact');
    setReference(job.id);
    setQuestion('Identifică afirmațiile nesusținute și dovezile lipsă din această propunere.');
    frozen.current = null;
    newAnalysis();
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    if (!frozen.current) {
      frozen.current = { ...draft, key: crypto.randomUUID().replaceAll('-', '') };
    }
    const submission = frozen.current;
    setBusy(true);
    setError('');
    try {
      const result = await api<Job>('/ai/requests', {
        method: 'POST',
        csrf: session.csrf_token,
        body: submission,
      });
      setJobs((previous) => [result, ...previous.filter((job) => job.id !== result.id)]);
      setPreview({ id: result.id, question: submission.question });
      setShowNew(false);
      navigate(analysisPath(result.id));
      setQuestion('');
      frozen.current = null;
    } catch (reason) {
      // Only deterministic pre-enqueue validation unlocks editing. Unknown outcomes keep the key.
      frozen.current = afterSubmissionFailure(frozen.current, reason);
      setError(safeError(reason));
    } finally {
      setBusy(false);
      refreshReadiness();
    }
  }

  return (
    <div
      className={'ai-chat' + (workspace ? ' lab-assistant' : '')}
      role="region"
      aria-label={workspace ? 'Asistent AI Strategy Lab' : 'AI Center'}
    >
      <header className="ai-chat-header">
        <div>
          <span className="ai-chat-eyebrow">
            {workspace ? 'IDEI · PLAN · CRITICĂ' : 'AI CENTER / RESEARCH WORKSPACE'}
          </span>
          <h2>{workspace ? 'Ce strategie vrei să cercetăm?' : 'Analizează o idee cu AI'}</h2>
          <p>Întreabă modelul, citește rezultatul și revizuiește dovezile într-un singur loc.</p>
        </div>
        <Link href="/setari/ai">
          <Settings2 size={16} aria-hidden="true" /> Configurează modele și roluri
        </Link>
      </header>
      <div className="ai-chat-layout">
        <aside className="ai-chat-history" aria-label="Istoricul analizelor">
          <div className="ai-chat-history-heading">
            <strong>Istoric analize</strong>
            <button type="button" aria-label="Analiză nouă" onClick={newAnalysis}>
              <Plus size={18} aria-hidden="true" />
            </button>
          </div>
          <button type="button" className="ai-chat-new" onClick={newAnalysis}>
            <Plus size={17} aria-hidden="true" /> Analiză nouă
          </button>
          {analyses.length ? (
            <ul className="ai-chat-history-list">
              {analyses.map((job) => (
                <li key={job.id}>
                  <button
                    type="button"
                    className={selected?.id === job.id ? 'is-selected' : ''}
                    aria-current={selected?.id === job.id ? 'page' : undefined}
                    onClick={() => selectAnalysis(job.id)}
                  >
                    <MessageSquareText size={17} aria-hidden="true" />
                    <span>
                      <strong>{roleLabels[job.role as Role] ?? 'Analiză AI'}</strong>
                      <small>{new Date(job.created_at).toLocaleString('ro-RO')}</small>
                      <small>{stateLabels[job.state]}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="ai-chat-history-empty">
              {loading
                ? 'Încărcăm analizele…'
                : 'Nicio analiză AI. Verificările de model sunt în Setări.'}
            </p>
          )}
          <div className="ai-chat-history-footer">
            <Link href="/setari/ai">Verificări, conexiuni și loguri</Link>
          </div>
        </aside>
        <section className="ai-chat-main" aria-label="Asistent de cercetare">
          <div className="ai-chat-model-bar">
            <span className={verifiedModel ? 'ai-chat-dot is-ready' : 'ai-chat-dot'} />
            <span>
              <strong>{verifiedModel ? model.name : 'Niciun model confirmat disponibil'}</strong>
              <small>
                {cloud ? 'OpenRouter · procesare cloud' : 'Model privat / local'} · Worker:{' '}
                {workerObserved(observation, role, category, now)
                  ? 'observat recent'
                  : 'necunoscut'}
              </small>
            </span>
            <span className="ai-chat-safety">SIMULATED / DENY_ALL</span>
          </div>
          {observation?.value.budget?.monthly_reserved_usd !== undefined && (
            <p className="ai-chat-hint">
              Rezervat conservator: {observation.value.budget.daily_reserved_usd} /{' '}
              {observation.value.budget.daily_limit_usd} USD astăzi ·{' '}
              {observation.value.budget.monthly_reserved_usd} /{' '}
              {observation.value.budget.monthly_limit_usd} USD luna aceasta. Factura furnizorului
              poate diferi; resetare UTC.
            </p>
          )}
          <div className="ai-chat-thread" aria-live="polite">
            {selected?.kind === 'INFER' ? (
              <>
                <div className="ai-chat-user-message">
                  <span>Întrebarea trimisă</span>
                  <p>
                    {preview?.id === selected.id
                      ? preview.question
                      : 'Textul întrebării nu este păstrat în istoricul vizibil după reîncărcare.'}
                  </p>
                </div>
                <div className="ai-chat-assistant-message">
                  {selected.output ? (
                    <ResponseContent
                      job={selected}
                      onCritic={criticDraft}
                      onTest={
                        session.user.role === 'OWNER'
                          ? (job) => {
                              const idea = researchIdea(job);
                              if (idea) {
                                offerResearchIdea(session.user.id, idea);
                                navigate('/testeaza/nou');
                              }
                            }
                          : undefined
                      }
                    />
                  ) : (
                    <div className="ai-chat-result-state" role="status">
                      <BrainCircuit size={22} aria-hidden="true" />
                      <strong>{stateLabels[selected.state]}</strong>
                      <p>
                        {selected.error
                          ? (aiErrors[selected.error] ?? 'Analiza nu a putut fi finalizată.') +
                            ' Cod: ' +
                            selected.error
                          : selected.content_expired
                            ? 'Conținutul a expirat; metadatele de audit rămân.'
                            : !selected.context_available
                              ? 'Contextul nu mai este autorizat, deci rezultatul nu poate fi afișat.'
                              : active(selected)
                                ? 'Solicitarea este în procesare. Rezultatul apare automat după finalizare.'
                                : 'Răspunsul structurat nu este disponibil.'}
                      </p>
                    </div>
                  )}
                  <details className="ai-chat-audit">
                    <summary>Detalii tehnice ale solicitării</summary>
                    <Evidence
                      title="Metadate verificabile"
                      value={{ ...selected, output: undefined }}
                    />
                  </details>
                </div>
              </>
            ) : selected ? (
              <div className="ai-chat-empty">
                <Clock3 size={30} aria-hidden="true" />
                <h3>Aceasta este o operațiune tehnică</h3>
                <p>Verificările și descoperirea modelelor nu sunt răspunsuri AI.</p>
                <Link href="/setari/ai">Deschide Setări AI</Link>
              </div>
            ) : (
              <div className="ai-chat-empty">
                <span className="ai-chat-empty-icon">
                  <BrainCircuit size={30} aria-hidden="true" />
                </span>
                <h3>Cu ce începem?</h3>
                <p>
                  Cere o ipoteză, un plan de backtesting sau o critică a unei strategii. Fiecare
                  solicitare este independentă: modelul nu primește automat istoricul.
                </p>
                <div className="ai-chat-suggestions">
                  {[
                    'Propune o ipoteză testabilă pentru XAUUSD pe M5.',
                    'Ce dovezi lipsesc pentru a valida o strategie?',
                    'Identifică riscurile de overfitting în backtesting.',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        setQuestion(suggestion);
                        setShowNew(true);
                      }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="ai-chat-composer" id="ai-question">
            <div className="ai-chat-composer-head">
              <label htmlFor="ai-chat-role">Tipul analizei</label>
              <select
                id="ai-chat-role"
                aria-label="Tipul analizei"
                value={role}
                disabled={busy || !!frozen.current}
                onChange={(event) => {
                  setRole(event.target.value as Role);
                  setAllowFallback(false);
                }}
              >
                {roles.map((option) => (
                  <option key={option} value={option}>
                    {roleLabels[option]}
                  </option>
                ))}
              </select>
            </div>
            <form onSubmit={(event) => void submit(event)}>
              <ContextBudgetControl
                mode={contextMode}
                onChange={setContextMode}
                disabled={busy || !!frozen.current}
                ceiling={contextWindow}
                preview={contextPreview}
              />
              <label htmlFor="ai-chat-question" className="sr-only">
                Întrebarea ta
              </label>
              <textarea
                id="ai-chat-question"
                aria-label="Întrebarea ta"
                required
                minLength={3}
                maxLength={4000}
                rows={3}
                disabled={busy || !!frozen.current}
                value={question}
                placeholder="Scrie ce ai vrea să analizeze modelul…"
                onChange={(event) => setQuestion(event.target.value)}
              />
              <details className="ai-chat-options">
                <summary>Context și opțiuni</summary>
                <div className="ai-chat-options-body">
                  <div className="ai-chat-reference">
                    <label htmlFor="ai-chat-ref-kind">Tip de referință</label>
                    <select
                      id="ai-chat-ref-kind"
                      aria-label="Tip de referință"
                      value={referenceKind}
                      disabled={busy || !!frozen.current}
                      onChange={(event) => setReferenceKind(event.target.value as ReferenceKind)}
                    >
                      {['documentation', 'dataset', 'experiment', 'strategy', 'ai_artifact'].map(
                        (option) => (
                          <option key={option}>{option}</option>
                        ),
                      )}
                    </select>
                    <label htmlFor="ai-chat-ref">ID referință (opțional)</label>
                    <input
                      id="ai-chat-ref"
                      maxLength={100}
                      value={reference}
                      disabled={busy || !!frozen.current}
                      onChange={(event) => setReference(event.target.value)}
                    />
                  </div>
                  <label className="ai-chat-check">
                    <input
                      type="checkbox"
                      checked={allowFallback}
                      disabled={busy || !!frozen.current || cloud}
                      onChange={(event) => setAllowFallback(event.target.checked)}
                    />
                    Permit doar modele alternative configurate explicit (nu OpenRouter).
                  </label>
                </div>
              </details>
              <div className="ai-chat-compose-bottom">
                <p>
                  Autorizarea permanentă și limitele sunt verificate de server pentru fiecare
                  solicitare.
                </p>
                <button type="submit" disabled={!canSubmit}>
                  <ArrowUp size={17} aria-hidden="true" /> Solicită analiza
                </button>
              </div>
              {unavailable && (
                <p className="ai-chat-hint" role="status">
                  {unavailable} <Link href="/setari/ai">Configurează modelul și rolurile</Link>.
                </p>
              )}
              {frozen.current && (
                <p className="ai-chat-hint">
                  Solicitarea incertă folosește aceeași cheie la reîncercare.{' '}
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => {
                      frozen.current = null;
                      setError('');
                    }}
                  >
                    Renunță la tentativa curentă
                  </button>
                </p>
              )}
              {error && (
                <p role="alert" className="ai-chat-error">
                  {error}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      void refresh();
                      refreshReadiness();
                    }}
                  >
                    Reîncarcă starea
                  </button>
                </p>
              )}
            </form>
            <p className="ai-chat-footer-note">
              Fără execuție de ordine · Niciun agent nu lucrează automat · GPU: necunoscut
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
