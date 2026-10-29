import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { api, safeError } from '../management-api';
import type { Session } from '../management-api';
import { Evidence } from '../ui/Controls';
import { Link, navigate, useRoute } from '../navigation/history';
import { active, ai, jobLabel, roleLabels, roles, stateLabels, verified } from './api';
import type { Binding, Connection, Endpoint, Job, Model, Role, Status, Submission } from './api';
import { aiErrors } from './copy';
import { AIRoles } from '../v1/AIWidgets';
import { StatusPill } from '../v1/components';
import { takeAIQuestion } from './draft';
import { CloudSetup, CredentialEditor } from './CloudSetup';
import AIChat from './AIChat';

const object = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((x): x is string => typeof x === 'string') : [];

function Answer({ job, critic, busy }: { job: Job; critic: () => void; busy: boolean }) {
  const output = object(job.output),
    metadata = object(job.metadata);
  return (
    <section className="panel" aria-label="Răspuns AI neverificat">
      <h3>{typeof output.title === 'string' ? output.title : 'Ce a răspuns modelul'}</h3>
      <p className="warning">
        Propunere AI neverificată. Nu este dovadă, recomandare de tranzacționare sau autorizare.
      </p>
      {['summary', 'hypothesis'].map(
        (key) => typeof output[key] === 'string' && <p key={key}>{output[key]}</p>,
      )}
      {['test_plan', 'objections', 'suggested_tests'].map(
        (key) =>
          strings(output[key]).length > 0 && (
            <div key={key}>
              <h4>
                {key === 'objections'
                  ? 'Puncte slabe'
                  : key === 'test_plan'
                    ? 'Cum poate fi testată'
                    : 'Teste sugerate'}
              </h4>
              <ul>
                {strings(output[key]).map((text, index) => (
                  <li key={index}>{text}</li>
                ))}
              </ul>
            </div>
          ),
      )}
      <h4>Ce dovezi lipsesc</h4>
      <ul>
        {strings(object(output.missing_evidence).items).map((text, index) => (
          <li key={index}>{text}</li>
        ))}
      </ul>
      <h4>Referințe citate · afirmațiile nu sunt validate automat</h4>
      {strings(output.evidence_refs).length ? (
        <ul>
          {strings(output.evidence_refs).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      ) : (
        <p>Modelul nu a citat dovezi.</p>
      )}
      {typeof output.candidate_source === 'string' && (
        <>
          <p>Cod propus · nu este executat și nu poate accesa conturi.</p>
          <pre className="ai-source">{output.candidate_source}</pre>
        </>
      )}
      <p>
        Durată:{' '}
        {typeof metadata.latency_ms === 'number' ? `${metadata.latency_ms} ms` : 'necunoscută'}.
        Tokenuri:{' '}
        {typeof metadata.input_tokens === 'number' ? metadata.input_tokens : 'necunoscute'} intrare
        / {typeof metadata.output_tokens === 'number' ? metadata.output_tokens : 'necunoscute'}{' '}
        ieșire. Cost estimat configurat:{' '}
        {typeof metadata.configured_cost_estimate === 'string'
          ? metadata.configured_cost_estimate
          : 'necunoscut'}
        .
      </p>
      <button type="button" onClick={critic} disabled={busy}>
        Cere o critică separată
      </button>
      <Evidence title="Model, parametri, referințe și amprente" value={job.metadata} />
    </section>
  );
}

function LegacyAICenter({
  session,
  advanced = false,
}: {
  session: Session;
  advanced?: boolean;
}) {
  const route = useRoute();
  const [status, setStatus] = useState<Status | null>(null),
    [models, setModels] = useState<Model[]>([]);
  const [bindings, setBindings] = useState<Binding[]>([]),
    [jobs, setJobs] = useState<Job[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]),
    [connections, setConnections] = useState<Connection[]>([]);
  const [readFailures, setReadFailures] = useState<string[]>([]);
  const [cloudCost, setCloudCost] = useState(false);
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState(''),
    [role, setRole] = useState<Role>('RESEARCH');
  const [reference, setReference] = useState(''),
    [referenceKind, setReferenceKind] = useState<
      'documentation' | 'dataset' | 'experiment' | 'strategy' | 'ai_artifact'
    >('documentation');
  const [ack, setAck] = useState(false),
    [remote, setRemote] = useState(false),
    [fallback, setFallback] = useState(false);
  const selected = route.jobId ?? null;
  const setSelected = (id: string) => navigate(`/testeaza/ai/${encodeURIComponent(id)}`);
  const frozen = useRef<Submission | null>(null);
  const [preview, setPreview] = useState<{ id: string; question: string } | null>(null);
  useEffect(() => {
    const handoff = takeAIQuestion(session.user.id);
    if (handoff) setQuestion(handoff);
  }, [session.user.id]);
  const owner = session.user.role === 'OWNER';
  const refresh = useCallback(async () => {
    const reads = await Promise.allSettled([
      ai<Status>('/status'),
      ai<Model[]>('/models'),
      ai<Binding[]>('/routes'),
      ai<Job[]>('/requests'),
      ai<Endpoint[]>('/endpoints'),
      ai<Connection[]>('/connections'),
    ] as const);
    const [s, m, r, j, e, c] = reads;
    setStatus(s.status === 'fulfilled' ? s.value : null);
    setModels(m.status === 'fulfilled' ? m.value : []);
    setBindings(r.status === 'fulfilled' ? r.value : []);
    setJobs(j.status === 'fulfilled' ? j.value : []);
    setEndpoints(e.status === 'fulfilled' ? e.value : []);
    setConnections(c.status === 'fulfilled' ? c.value : []);
    const names = [
      'starea AI',
      'modelele',
      'rolurile',
      'activitatea',
      'destinațiile',
      'conexiunile',
    ];
    setReadFailures(reads.flatMap((result, i) => (result.status === 'rejected' ? [names[i]] : [])));
  }, []);
  useEffect(() => {
    let alive = true;
    void refresh()
      .catch((e: unknown) => {
        if (alive) setError(safeError(e));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [refresh]);
  // Poll actual durable state; no invented percentage or optimistic cancellation.
  const pending = jobs.some(active);
  useEffect(() => {
    let alive = true;
    const timer = window.setInterval(() => {
      void ai<Status>('/status')
        .then((value) => {
          if (alive) setStatus(value);
        })
        .catch((e: unknown) => {
          if (alive) {
            setStatus(null);
            setError(safeError(e));
          }
        });
    }, 10000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (!selected || jobs.some((j) => j.id === selected)) return;
    let alive = true;
    void ai<Job>(`/requests/${encodeURIComponent(selected)}`)
      .then((job) => {
        if (alive) setJobs((current) => [job, ...current.filter((j) => j.id !== job.id)]);
      })
      .catch((e: unknown) => {
        if (alive) setError(safeError(e));
      });
    return () => {
      alive = false;
    };
  }, [selected, jobs]);
  useEffect(() => {
    if (!pending) return;
    let alive = true;
    const timer = window.setInterval(() => {
      void ai<Job[]>('/requests')
        .then((j) => {
          if (alive) setJobs(j);
        })
        .catch((e: unknown) => {
          if (alive) setError(safeError(e));
        });
    }, 2000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [pending]);
  async function mutate(path: string, body: unknown, method = 'POST') {
    setBusy(true);
    setError('');
    try {
      const result = await api<unknown>(`/ai${path}`, { method, body, csrf: session.csrf_token });
      await refresh();
      return result;
    } catch (e) {
      setError(safeError(e));
      return undefined;
    } finally {
      setBusy(false);
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!frozen.current)
      frozen.current = {
        schema_version: 1,
        key: crypto.randomUUID().replaceAll('-', ''),
        question,
        role,
        references: reference
          ? [{ kind: referenceKind, id: reference }]
          : [{ kind: 'documentation', id: 'research-limits-v1' }],
        parameters: {
          context_tokens: 4096,
          output_tokens: 768,
          temperature: 0,
          top_p: 1,
          reasoning: 'DEFAULT',
          max_seconds: 90,
        },
        allow_remote: remote,
        cloud_cost_acknowledged: cloudCost,
        allow_fallback: fallback,
        processing_acknowledged: true,
        retain_structured_output: true,
      };
    const submission = frozen.current;
    const result = (await mutate('/requests', submission)) as Job | undefined;
    if (result) {
      setPreview({ id: result.id, question: submission.question });
      setSelected(result.id);
      frozen.current = null;
      setQuestion('');
    }
  }
  const binding = bindings.find((b) => b.role === role);
  const usable = binding && models.some((m) => m.id === binding.model_id && verified(m));
  const current = jobs.find((j) => j.id === selected);
  const unavailable = !owner
    ? 'Numai proprietarul cu MFA recent poate solicita o analiză.'
    : !status
      ? 'Starea gateway-ului nu poate fi verificată. Reîncarcă informațiile; nu presupunem disponibilitatea.'
      : !status.configured
        ? 'Gateway-ul nu este configurat. Configurează infrastructura privată.'
        : !usable
          ? 'Rolul ales nu are un model verificat curent. Verifică modelul în Setări.'
          : status.worker_state !== 'OBSERVED_RECENTLY'
            ? 'Worker-ul nu a fost observat recent. Verifică serviciul înainte de a solicita analiza.'
            : '';

  return (
    <div className={`ai-center ai-workbench${advanced ? ' ai-advanced' : ''}`}>
      <section className="panel v1-ai-heading" aria-label="Centru AI">
        <h2>{advanced ? 'Modele AI și roluri' : 'Analizează o idee cu AI'}</h2>
        <p>
          AI poate propune, rezuma și critica. Nu execută cod, nu schimbă limite și nu trimite
          ordine. Cercetarea autonomă nu este implementată.
        </p>
        <p>
          <strong>
            {status?.configured
              ? `${models.filter((m) => verified(m)).length} modele cu verificare curentă`
              : 'Niciun model confirmat disponibil'}
          </strong>{' '}
          · Worker:{' '}
          {status?.worker_state === 'OBSERVED_RECENTLY' ? 'observat recent' : 'necunoscut'} · GPU:
          necunoscut.
        </p>
        <p>SIMULATED / DENY_ALL · disponibilitatea AI nu autorizează tranzacții.</p>
        {loading && <p role="status">Citim configurația și activitatea…</p>}
        {error && <p role="alert">{error}</p>}
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            setError('');
            void refresh().catch((e: unknown) => setError(safeError(e)));
          }}
        >
          Reîncarcă starea
        </button>
        <p>
          {advanced ? (
            <Link href="/testeaza/ai">Deschide analiza</Link>
          ) : (
            <Link href="/setari/ai">Configurează modele și roluri</Link>
          )}
        </p>
        {status && (
          <p>
            Limite: {status.limits.hourly_owner} solicitări/oră, {status.limits.hourly_role}
            /rol/oră, cel mult {status.limits.global_concurrency} analize simultane. Datele
            temporare expiră conform politicii, cel mult 30 minute; răspunsurile structurate cel
            mult 24 ore.
          </p>
        )}
      </section>
      {!advanced && <AIRoles models={models} bindings={bindings} status={status} />}
      {!advanced && (
        <section className="panel v1-ai-composer" id="ai-question">
          <nav className="v1-filter-chips" aria-label="Instrumente AI">
            <a href="#ai-question">Asistent</a>
            <a href="#ai-roles">Roluri și modele</a>
            <a href="#ai-activity">Jurnale</a>
          </nav>
          <h3>Ce dorești să verifici?</h3>
          {unavailable && <p id="ai-unavailable">{unavailable}</p>}
          <form
            onSubmit={(event) => {
              void submit(event);
            }}
          >
            <label>
              Tipul analizei
              <select
                aria-label="Tipul analizei"
                value={role}
                disabled={!!frozen.current}
                onChange={(e) => setRole(e.target.value as Role)}
              >
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {roleLabels[r]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Întrebarea ta
              <textarea
                required
                minLength={3}
                maxLength={4000}
                value={question}
                disabled={!!frozen.current}
                onChange={(e) => setQuestion(e.target.value)}
              />
            </label>
            <div className="v1-suggestions" role="group" aria-label="Întrebări sugerate">
              {[
                'Ce dovezi lipsesc?',
                'Propune o ipoteză testabilă',
                'Caută o explicație alternativă',
              ].map((text) => (
                <button
                  className="secondary-button"
                  type="button"
                  key={text}
                  disabled={Boolean(frozen.current)}
                  onClick={() => {
                    setQuestion(text);
                    setAck(false);
                  }}
                >
                  {text}
                </button>
              ))}
            </div>
            <p>
              Nu introduce parole, chei, date personale sau informații fără drept de utilizare.
              Întrebarea nu este salvată în browser.
            </p>
            <details>
              <summary>Alege contextul permis · opțional</summary>
              <label>
                Tip de referință
                <select
                  aria-label="Tip de referință"
                  value={referenceKind}
                  onChange={(e) => setReferenceKind(e.target.value as typeof referenceKind)}
                  disabled={!!frozen.current}
                >
                  {['documentation', 'dataset', 'experiment', 'strategy', 'ai_artifact'].map(
                    (kind) => (
                      <option key={kind}>{kind}</option>
                    ),
                  )}
                </select>
              </label>
              <label>
                Identificatorul referinței
                <input
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  disabled={!!frozen.current}
                  maxLength={100}
                />
              </label>
              <p>
                Fără selecție, trimitem doar explicația limitelor cercetării. Datele finale
                protejate și conturile altor utilizatori sunt refuzate de server.
              </p>
              <label>
                <input
                  type="checkbox"
                  checked={fallback}
                  onChange={(e) => setFallback(e.target.checked)}
                  disabled={!!frozen.current}
                />
                Permit numai modelele alternative configurate explicit pentru acest rol.
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={remote}
                  onChange={(e) => setRemote(e.target.checked)}
                  disabled={!!frozen.current}
                />
                Permit procesarea la distanță aprobată în politica conexiunii; pentru OpenRouter,
                contextul ajunge în cloud public și la furnizorul aprobat.
              </label>
            </details>
            <label>
              <input
                type="checkbox"
                checked={cloudCost}
                onChange={(e) => setCloudCost(e.target.checked)}
                disabled={!!frozen.current}
              />
              Aprob costul unei solicitări OpenRouter în limita autorizată. Nu este necesar pentru
              modele private.
            </label>
            <label>
              <input
                type="checkbox"
                required
                checked={ack}
                onChange={(e) => setAck(e.target.checked)}
              />
              Am dreptul să trimit acest context și accept procesarea temporară și păstrarea
              criptată, limitată, a răspunsului structurat.
            </label>
            <button
              type="submit"
              disabled={busy || !!unavailable || !ack}
              aria-describedby={unavailable ? 'ai-unavailable' : undefined}
            >
              {frozen.current ? 'Reîncearcă aceeași solicitare' : 'Solicită analiza'}
            </button>
            {frozen.current && (
              <p>
                Solicitarea este păstrată în memorie cu aceeași cheie. Verifică activitatea înainte
                de a o retrimite.{' '}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    frozen.current = null;
                    setError('');
                  }}
                >
                  Renunță la draftul trimis
                </button>
              </p>
            )}
          </form>
        </section>
      )}
      {readFailures.length > 0 && (
        <p role="alert">
          Nu putem citi {readFailures.join(', ')}. Listele indisponibile nu înseamnă că nu există
          înregistrări.{' '}
          <button type="button" disabled={busy} onClick={() => void refresh()}>
            Reîncearcă citirea configurării
          </button>
        </p>
      )}
      {advanced && (
        <Registry
          models={models}
          bindings={bindings}
          endpoints={endpoints}
          connections={connections}
          busy={busy || !owner || loading}
          mutate={mutate}
        />
      )}
      {advanced && <AIRoles models={models} bindings={bindings} status={status} />}
      <section className="panel v1-ai-activity" id="ai-activity" aria-label="Activitatea AI">
        <h3>Solicitări recente</h3>
        <p>Ultimele 25 de solicitări. Procentele de progres nu sunt estimate.</p>
        {jobs.length === 0 && (
          <p>Nu există analize în această listă. Niciun agent nu lucrează automat.</p>
        )}
        <ul className="ai-jobs">
          {jobs.map((job) => (
            <li key={job.id}>
              <button type="button" onClick={() => setSelected(job.id)}>
                {jobLabel(job)} · {stateLabels[job.state]}
              </button>
              <span>
                {job.cancel_requested && active(job)
                  ? 'Anulare solicitată · așteptăm confirmarea worker-ului.'
                  : ''}
              </span>
              {owner && active(job) && (
                <button
                  type="button"
                  disabled={busy || job.cancel_requested}
                  onClick={() => {
                    void mutate(`/requests/${job.id}/cancel`, {});
                  }}
                >
                  Solicită anularea
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>
      {current && (
        <section className="panel v1-ai-answer" aria-label="Detalii analiză">
          <h3>{stateLabels[current.state]}</h3>
          {preview?.id === current.id && (
            <p>Întrebarea trimisă · numai în memoria acestei pagini: {preview.question}</p>
          )}
          {current.error && (
            <p role="status">
              {aiErrors[current.error] ?? 'Nu putem confirma rezultatul analizei.'} Analiza nu poate
              fi folosită ca rezultat. Verifică modelul, autorizarea și contextul înainte de o nouă
              solicitare. Cod diagnostic:{' '}
              <code>
                {/^[A-Z_0-9]{1,80}$/.test(current.error) ? current.error : 'AI_OPERATION_FAILED'}
              </code>
            </p>
          )}
          {!current.context_available && (
            <p>
              Contextul nu mai este autorizat. Conținutul nu este afișat; metadatele de audit rămân.
            </p>
          )}
          {current.state === 'CANCELLED' && (
            <p>
              Răspunsul nu va fi publicat. Închiderea conexiunii nu dovedește oprirea procesării pe
              GPU-ul furnizorului.
            </p>
          )}
          {current.output && current.kind === 'INFER' ? (
            <Answer
              job={current}
              busy={busy}
              critic={() => {
                setRole('CRITIC');
                setReferenceKind('ai_artifact');
                setReference(current.id);
                setQuestion(
                  'Identifică afirmațiile nesusținute și dovezile lipsă din această propunere.',
                );
                setAck(false);
                frozen.current = null;
                document.querySelector('textarea')?.focus();
              }}
            />
          ) : current.output ? (
            <Evidence title="Modele descoperite sau capabilități măsurate" value={current.output} />
          ) : (
            <p>
              {current.content_expired
                ? 'Conținutul a expirat; metadatele de audit rămân.'
                : 'Răspunsul structurat nu este disponibil.'}
            </p>
          )}
          {owner && (
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                void mutate(`/requests/${current.id}/content`, undefined, 'DELETE');
              }}
            >
              Șterge conținutul păstrat
            </button>
          )}
          <Evidence
            title="Metadate verificabile ale solicitării"
            value={{ ...current, output: undefined }}
          />
        </section>
      )}
    </div>
  );
}

export function Registry({
  models,
  bindings,
  endpoints,
  connections,
  busy,
  mutate,
}: {
  models: Model[];
  bindings: Binding[];
  endpoints: Endpoint[];
  connections: Connection[];
  busy: boolean;
  mutate: (path: string, body: unknown, method?: string) => Promise<unknown>;
}) {
  const [destination, setDestination] = useState('');
  const [protocol, setProtocol] = useState('OLLAMA_NATIVE');
  const [credentialFor, setCredentialFor] = useState('');
  const [cloudProbeConsent, setCloudProbeConsent] = useState(false);
  const chosen = endpoints.find((e) => e.id === destination) ?? endpoints[0];
  const publicCloud = chosen?.transport === 'OPENROUTER_PUBLIC';
  const value = (data: FormData, key: string) => String(data.get(key) ?? '');
  function save(
    event: FormEvent<HTMLFormElement>,
    path: string,
    body: (data: FormData) => unknown,
  ) {
    event.preventDefault();
    void mutate(path, body(new FormData(event.currentTarget)));
  }
  return (
    <section className="panel v1-ai-registry" aria-label="Registru AI">
      <h3>Configurare avansată · proprietar cu MFA recent</h3>
      <p>
        Adresele și secretele sunt configurate de operator în infrastructură. Browserul alege doar
        destinații aprobate. Salvarea unui model nu confirmă funcționarea sa.
      </p>
      <CloudSetup busy={busy} mutate={mutate} />
      <nav className="v1-filter-chips" aria-label="Configurare AI">
        <a href="#ai-destinations">Destinații și cloud</a>
        <a href="#ai-models">Modele</a>
        <a href="#ai-role-config">Roluri</a>
        <a href="#ai-connections">Conexiuni</a>
        <a href="#ai-roles">Limite și consum</a>
      </nav>
      <div
        className="table-scroll v1-model-table"
        role="region"
        aria-label="Modele înregistrate"
        id="ai-models"
        tabIndex={0}
      >
        <table>
          <caption>Modele configurate · o înregistrare nu confirmă disponibilitatea</caption>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col">Conexiune</th>
              <th scope="col">Plafon declarat</th>
              <th scope="col">Verificare și capabilități</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.name}</td>
                <td>
                  {connections.find((c) => c.id === m.connection_id)?.name ??
                    'Conexiune necunoscută'}
                </td>
                <td>{m.context_ceiling} tokenuri</td>
                <td>
                  <StatusPill tone={verified(m) ? 'positive' : 'neutral'}>
                    {verified(m) ? 'Verificare curentă' : 'Neverificat / expirat'}
                  </StatusPill>
                  <p>Expiră: {m.verified_until ?? 'neverificat'}</p>
                  <Evidence title="Capabilități măsurate" value={m.verification} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!models.length && (
          <p>
            Niciun model înregistrat. Completează conexiunea, apoi înregistrează și verifică
            modelul.
          </p>
        )}
      </div>
      {!endpoints.length && (
        <p>
          Nicio destinație aprobată. Configurează o destinație privată în AI_DEPLOYMENT_GUIDE.md sau
          autorizează explicit OpenRouter mai sus. Conexiunea și modelul devin disponibile după
          acești pași.
        </p>
      )}
      <div className="v1-registry-forms">
        <form
          onSubmit={(e) =>
            save(e, '/connections', (d) => ({
              name: value(d, 'name'),
              endpoint_id: value(d, 'endpoint'),
              provider: value(d, 'provider'),
              policy: {
                rights_confirmed: true,
                approved_processing: true,
                remote_processing: d.has('remote'),
                cloud_processing_acknowledged: d.has('cloud_policy'),
                account_context_remote: d.has('account_remote'),
                temporary_processing_minutes: Number(d.get('temporary')),
                structured_retention_hours: Number(d.get('retention')),
              },
            }))
          }
        >
          <h4 id="ai-connections">1. Aprobă o conexiune</h4>
          <label>
            Numele conexiunii
            <input name="name" required maxLength={100} />
          </label>
          <label>
            Destinație aprobată
            <select
              aria-label="Destinație aprobată"
              name="endpoint"
              required
              disabled={!endpoints.length || busy}
              value={chosen?.id ?? ''}
              onChange={(e) => setDestination(e.target.value)}
            >
              {!endpoints.length && <option value="">Configurează mai întâi destinația</option>}
              {endpoints.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.label} · {e.transport}
                </option>
              ))}
            </select>
          </label>
          <label>
            Protocol
            <select
              aria-label="Protocol"
              name="provider"
              value={
                publicCloud ? 'OPENROUTER' : protocol === 'OPENROUTER' ? 'OLLAMA_NATIVE' : protocol
              }
              onChange={(e) => setProtocol(e.target.value)}
            >
              {publicCloud ? (
                <option value="OPENROUTER">OPENROUTER · OpenAI compatibil</option>
              ) : (
                <>
                  <option>OLLAMA_NATIVE</option>
                  <option>OLLAMA_OPENAI</option>
                  <option>PRIVATE_OPENAI</option>
                </>
              )}
            </select>
          </label>
          <label>
            Procesare temporară · minute
            <input type="number" name="temporary" min={1} max={30} defaultValue={10} required />
          </label>
          <label>
            Păstrare răspuns structurat · ore
            <input type="number" name="retention" min={1} max={24} defaultValue={1} required />
          </label>
          <label key={`remote-${chosen?.id ?? ''}`}>
            <input type="checkbox" name="remote" required={publicCloud} />
            {publicCloud
              ? 'Aprob procesarea la distanță prin OpenRouter și furnizorul din amonte.'
              : 'Aprob infrastructura privată la distanță.'}
          </label>
          <label key={`account-${chosen?.id ?? ''}`}>
            <input type="checkbox" name="account_remote" />
            Aprob și contextul minimizat asociat conturilor pe această infrastructură.
          </label>
          {publicCloud && (
            <label key={`cloud-${chosen?.id ?? ''}`}>
              <input type="checkbox" name="cloud_policy" required />
              Aprob politica cloud public separat de aprobarea privată.
            </label>
          )}
          <label key={`rights-${chosen?.id ?? ''}`}>
            <input type="checkbox" required />
            {publicCloud
              ? 'Am verificat drepturile, destinația cloud și politica de păstrare.'
              : 'Am verificat drepturile, destinația privată și politica de păstrare.'}
          </label>
          <button disabled={busy || !endpoints.length}>Salvează conexiunea aprobată</button>
        </form>
        <ul>
          {connections.map((c) => (
            <li key={c.id}>
              {c.name} · {c.enabled ? 'permisă' : 'dezactivată'}
              {c.provider === 'OPENROUTER' && (
                <>
                  <p>
                    {c.credential_configured
                      ? 'Cheie configurată pe server · nu poate fi recitită.'
                      : 'Lipsește cheia: salveaz-o înainte de catalog sau verificare.'}
                  </p>
                  <button type="button" disabled={busy} onClick={() => setCredentialFor(c.id)}>
                    Configurează cheia OpenRouter
                  </button>
                  {credentialFor === c.id && (
                    <CredentialEditor
                      connection={c.id}
                      busy={busy}
                      mutate={mutate}
                      close={() => setCredentialFor('')}
                    />
                  )}
                </>
              )}
              <button
                type="button"
                disabled={
                  busy || !c.enabled || (c.provider === 'OPENROUTER' && !c.credential_configured)
                }
                onClick={() => {
                  void mutate(`/connections/${c.id}/discover`, {
                    key: crypto.randomUUID().replaceAll('-', ''),
                  });
                }}
              >
                Citește modelele disponibile
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  void mutate(`/connections/${c.id}`, { enabled: !c.enabled }, 'PATCH');
                }}
              >
                {c.enabled ? 'Dezactivează conexiunea' : 'Activează conexiunea'}
              </button>
            </li>
          ))}
        </ul>
        <form
          onSubmit={(e) =>
            save(e, '/models', (d) => ({
              connection_id: value(d, 'connection'),
              name: value(d, 'model'),
              context_ceiling: Number(d.get('context')),
            }))
          }
        >
          <h4>2. Înregistrează și verifică modelul</h4>
          <label>
            Conexiune
            <select
              aria-label="Conexiune"
              name="connection"
              required
              disabled={busy || !connections.some((c) => c.enabled)}
            >
              {!connections.some((c) => c.enabled) && (
                <option value="">Creează mai întâi o conexiune activă</option>
              )}
              {connections
                .filter((c) => c.enabled)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
            </select>
          </label>
          <p>
            Folosește identificatorul exact din configurație sau catalog. Pentru OpenRouter:
            autor/model. Înregistrarea nu verifică modelul și nu trimite o cerere cu plată.
          </p>
          <label>
            Numele exact al modelului
            <input name="model" required maxLength={150} />
          </label>
          <label>
            Plafon de context · tokenuri
            <input
              name="context"
              type="number"
              min={1024}
              max={32768}
              defaultValue={4096}
              required
            />
          </label>
          <button disabled={busy || !connections.some((c) => c.enabled)}>
            Înregistrează modelul neverificat
          </button>
        </form>
        <label>
          <input
            type="checkbox"
            checked={cloudProbeConsent}
            onChange={(e) => setCloudProbeConsent(e.target.checked)}
          />
          Aprob o verificare OpenRouter cu o singură completare structurată, cu posibile costuri în
          limita autorizată.
        </label>
        <ul>
          {models.map((m) => (
            <li key={m.id}>
              {m.name} · {verified(m) ? 'verificare curentă' : 'neverificat sau expirat'}
              <button
                type="button"
                disabled={
                  busy ||
                  (connections.find((c) => c.id === m.connection_id)?.provider === 'OPENROUTER' &&
                    !cloudProbeConsent)
                }
                onClick={() => {
                  void mutate(`/models/${m.id}/probe`, {
                    cloud_cost_acknowledged: cloudProbeConsent,
                    key: crypto.randomUUID().replaceAll('-', ''),
                  });
                }}
              >
                Verifică printr-o solicitare reală
              </button>
              <Evidence title="Capabilități măsurate și expirare" value={m} />
            </li>
          ))}
        </ul>
        <form
          onSubmit={(e) =>
            save(e, '/routes', (d) => ({
              role: value(d, 'role'),
              model_id: value(d, 'model'),
              fallback_ids: d.getAll('fallback').filter(Boolean),
            }))
          }
        >
          <h4 id="ai-role-config">3. Alege separat modelul fiecărui rol</h4>
          <label>
            Rol
            <select aria-label="Rol" name="role">
              {roles.map((r) => (
                <option key={r} value={r}>
                  {roleLabels[r]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Model principal
            <select
              aria-label="Model principal"
              name="model"
              required
              disabled={busy || !models.some((m) => verified(m))}
            >
              {!models.some((m) => verified(m)) && (
                <option value="">Verifică mai întâi un model</option>
              )}
              {models
                .filter((m) => verified(m))
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} · {m.id.slice(0, 8)}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Alternativă explicită · opțional
            <select aria-label="Alternativă explicită · opțional" name="fallback">
              <option value="">Fără alternativă</option>
              {models
                .filter((m) => verified(m))
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} · {m.id.slice(0, 8)}
                  </option>
                ))}
            </select>
          </label>
          <button disabled={busy || !models.some((m) => verified(m))}>
            Salvează o nouă versiune a rolului
          </button>
        </form>
      </div>
      <Evidence title="Versiuni imuabile ale rolurilor" value={bindings} />
    </section>
  );
}

/** The user-facing workspace is chat-first; the original registry remains under Setări. */
export default function AICenter({
  session,
  advanced = false,
}: {
  session: Session;
  advanced?: boolean;
}) {
  return advanced ? <LegacyAICenter session={session} advanced /> : <AIChat session={session} />;
}
