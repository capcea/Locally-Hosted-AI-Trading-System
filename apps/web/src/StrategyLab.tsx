import { useCallback, useEffect, useState, useRef } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError } from './management-api';
import type { RecordItem, RecordPage, Session } from './management-api';
import type { components } from './generated/api';

type Plan = components['schemas']['packages__research__contracts__ExperimentInput'];
type Dataset = components['schemas']['DatasetView'];
type Run = components['schemas']['RunView'];
type RunSummary = components['schemas']['RunSummary'];
type Context = components['schemas']['ContextInput'];
type Strategy = {
  id: Plan['strategy'];
  version: string;
  digest: string;
  entry: string;
  exit: string;
  assumptions: string;
  parameters: unknown;
};
type Job = {
  id: string;
  name: string;
  strategy: string;
  phase: string;
  engine: string;
  job: { state: string; progress: number; attempts: number; error: string | null };
  result: unknown;
};
type Seal = { id: string; dataset_id: string; prior_exposure: string };
type Point = { at: string; timestamp: number; equity: string };
type Result = {
  engine: string;
  trials: {
    ordinal: number;
    parameters: unknown;
    cost_multiplier: string;
    metrics?: Record<string, unknown>;
    approximate_net?: string;
    risk_validated: boolean;
  }[];
};
const value = (form: FormData, name: string) => String(form.get(name) ?? '');
const integer = (form: FormData, name: string) => Number(value(form, name));
const json = (item: unknown) => JSON.stringify(item, null, 2);

function EquityChart({ points }: { points: Point[] }) {
  if (points.length < 2) return <p>Curba nu are suficiente observații stocate.</p>;
  const amounts = points.map((p) => Number(p.equity));
  const low = Math.min(...amounts),
    high = Math.max(...amounts);
  const start = points[0].timestamp,
    duration = points.at(-1)!.timestamp - start || 1;
  const path = points
    .map(
      (p, i) =>
        `${20 + ((p.timestamp - start) / duration) * 560},${180 - ((amounts[i] - low) / (high - low || 1)) * 150}`,
    )
    .join(' ');
  return (
    <figure>
      <svg
        role="img"
        aria-label="Curba capitalului simulat stocat"
        viewBox="0 0 600 210"
        width="100%"
      >
        <polyline points={path} fill="none" stroke="currentColor" strokeWidth="2" />
        <text x="20" y="205">
          {points[0].at} — {points.at(-1)!.at}
        </text>
      </svg>
      <figcaption>
        Coordonate grafice aproximative; valorile păstrate sunt în tabel. SIMULATED.
      </figcaption>
    </figure>
  );
}

export default function StrategyLab({
  session,
  onExpired,
}: {
  session: Session;
  onExpired: () => void;
}) {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [templates, setTemplates] = useState<RunSummary[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [seals, setSeals] = useState<Seal[]>([]);
  const [account, setAccount] = useState('');
  const [dataset, setDataset] = useState('');
  const [strategy, setStrategy] = useState<Plan['strategy']>('EMA_TREND');
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [details, setDetails] = useState<unknown>(null);
  const [section, setSection] = useState('trades');
  const [trial, setTrial] = useState(0);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const requestKey = useRef(crypto.randomUUID());
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const fail = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && error.status === 401) onExpired();
      setError(error instanceof Error ? error.message : 'Operațiunea a eșuat.');
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    try {
      const [s, a, j, h, r] = await Promise.all([
        api<Strategy[]>('/research/strategies'),
        api<RecordPage>('/records/accounts?limit=100'),
        api<Job[]>('/research/experiments?limit=100'),
        api<Seal[]>('/research/holdouts'),
        api<RunSummary[]>('/execution/simulations?limit=50'),
      ]);
      setStrategies(s);
      setAccounts(a.items);
      setJobs(j);
      setSeals(h);
      setTemplates(r);
    } catch (error) {
      fail(error);
    }
  }, [fail]);
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 2000);
    return () => clearInterval(timer);
  }, [load]);
  useEffect(() => {
    if (!account) return;
    let active = true;
    api<{ items: Dataset[] }>(`/market/datasets?account_id=${account}&status=VALID&limit=100`)
      .then((data) => {
        if (active) setDatasets(data.items);
      })
      .catch(fail);
    return () => {
      active = false;
    };
  }, [account, fail]);
  const inspect = useCallback(
    async (id: string, index = 0) => {
      setSelected(id);
      setTrial(index);
      setError('');
      try {
        const [summary, curve] = await Promise.all([
          api<Result>(`/research/experiments/${id}/results`),
          api<{ items: Point[] }>(
            `/research/experiments/${id}/results?section=equity&trial=${index}&limit=500`,
          ),
        ]);
        setResult(summary);
        setPoints(curve.items);
        setDetails(await api(`/research/experiments/${id}/provenance`));
      } catch (error) {
        fail(error);
      }
    },
    [fail],
  );
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError('');
    setNotice('');
    const form = new FormData(event.currentTarget);
    try {
      const ids = form.getAll('dataset').map(String);
      const chosen = ids.length ? ids : [dataset];
      const template = await api<Run>(`/execution/simulations/${value(form, 'template')}`);
      const contexts = await api<{ context: Context }[]>(`/risk/runs/${template.id}/contexts`);
      if (!contexts.length)
        throw new Error('Configurează și verifică mai întâi contextul de risc al șablonului.');
      const definition = strategies.find((s) => s.id === strategy)!;
      const parameters = {
        fast: integer(form, 'fast'),
        slow: integer(form, 'slow'),
        lookback: integer(form, 'lookback'),
        volume: value(form, 'volume'),
        stop_ticks: integer(form, 'stop'),
        reward_multiple: value(form, 'reward'),
        direction: value(form, 'direction') as Plan['parameters'][number]['direction'],
        entry_order_type: value(
          form,
          'orderType',
        ) as Plan['parameters'][number]['entry_order_type'],
        entry_offset_ticks: integer(form, 'entryOffset'),
        pending_expiry_seconds: integer(form, 'expiry'),
        session_exit_buffer_seconds:60,flat_before_risk_reset:true,
        threshold: '2',
        session_open: 0,
        session_close: 1440,
        opening_minutes: 15,
        max_hold_seconds: integer(form, 'hold'),
        random_keep_pct: integer(form, 'random'),
      };
      const sweep = value(form, 'sweep').trim();
      const params = sweep ? (JSON.parse(sweep) as Plan['parameters']) : [parameters];
      const plan: Plan = {
        key: crypto.randomUUID(),
        name: value(form, 'name'),
        source_account_id: account,
        strategy,
        strategy_digest: definition.digest,
        datasets: chosen.map((id) => {
          const d = datasets.find((d) => d.id === id);
          if (!d?.manifest_sha256 || d.instrument_id !== template.instrument_id)
            throw new Error(
              'Setul și șablonul trebuie să aibă același instrument. Pentru portofolii folosește configurația JSON avansată.',
            );
          return {
            dataset_id: id,
            manifest_sha256: d.manifest_sha256,
            role: value(form, `role-${id}`) === 'CONFIRMATION' ? 'CONFIRMATION' : 'EXECUTION',
            symbol: { ...template.state.spec, symbol: d.spec.source_symbol },
            context: {...contexts[0].context,financial:{...contexts[0].context.financial,automated:true,execution_style:'INTRADAY_BENCHMARK'}},
          };
        }),
        parameters: params,
        chronology: {
          start: value(form, 'start'),
          discovery_end: value(form, 'discovery'),
          calibration_end: value(form, 'calibration'),
          validation_end: value(form, 'validation'),
          end: value(form, 'end'),
          purge_seconds: integer(form, 'purge'),
          embargo_seconds: integer(form, 'embargo'),
          walk_forward_folds: integer(form, 'folds'),
        },
        phase: value(form, 'phase') as Plan['phase'],
        engine: value(form, 'engine') as Plan['engine'],
        validation_mode: value(form, 'mode') as Plan['validation_mode'],
        assumptions: template.state.model,
        bar_spread: value(form, 'spread') || null,
        cost_multipliers: value(form, 'costs')
          .split(',')
          .map((x) => x.trim()),
        seed: integer(form, 'seed'),
        max_rows: integer(form, 'rows'),
        max_seconds: integer(form, 'seconds'),
        bootstrap_samples: integer(form, 'bootstrap'),
        acknowledged_clone_policy_to_isolated_accounts: true,
        acknowledged_research_only: true,
        acknowledged_cost_and_bar_assumptions: true,
      };
      const advanced = value(form, 'advanced').trim();
      const actual = advanced ? (JSON.parse(advanced) as Plan) : plan;
      actual.key = requestKey.current;
      const created = await api<Job>('/research/experiments', {
        method: 'POST',
        csrf: session.csrf_token,
        body: actual,
      });
      requestKey.current = crypto.randomUUID();
      setSelected(created.id);
      setResult(null);
      setPoints([]);
      setNotice(`Experiment înregistrat: ${created.id}`);
      await load();
    } catch (error) {
      fail(error);
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  const data = datasets.find((d) => d.id === dataset);
  const start = data?.spec.start ?? '2024-01-02T00:00:00Z';
  const end = data?.spec.end ?? '2024-01-03T00:00:00Z';
  const between = (fraction: number) =>
    new Date(Date.parse(start) + (Date.parse(end) - Date.parse(start)) * fraction).toISOString();
  const currentDefinition = strategies.find((s) => s.id === strategy);
  return (
    <section aria-label="Laborator de strategii" className="management-grid research-lab">
      <header className="panel management-panel">
        <h2>Laborator de strategii · SIMULATED</h2>
        <p>
          Experimente reproductibile pe date admise. Screening-ul este exploratoriu; niciun rezultat
          nu autorizează paper sau ordine externe. Filtrele ML/LLM nu sunt implementate.
        </p>
      </header>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <section className="panel management-panel">
        <h3>Biblioteca strategiilor revizuite</h3>
        <label>
          Strategie de referință
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as Plan['strategy'])}
          >
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.id} · {s.version}
              </option>
            ))}
          </select>
        </label>
        {currentDefinition && (
          <details>
            <summary>Contract, versiune și parametri</summary>
            <pre>{json(currentDefinition)}</pre>
          </details>
        )}
      </section>
      <form
        aria-label="Configurează backtest"
        className="panel management-panel"
        onSubmit={(event) => void submit(event)}
        key={dataset}
      >
        <h3>Configurație backtest</h3>
        <div className="research-fields">
          <label>
            Cont sursă verificat
            <select
              required
              value={account}
              onChange={(e) => {
                setAccount(e.target.value);
                setDataset('');
              }}
            >
              <option value="">Alege contul…</option>
              {accounts.map((a) => (
                <option value={a.id} key={a.id}>
                  {a.data.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Set de date principal
            <select required value={dataset} onChange={(e) => setDataset(e.target.value)}>
              <option value="">Alege un set VALID…</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.symbol} · {d.spec.timeframe} · v{d.version} · {d.record_count} observații
                </option>
              ))}
            </select>
          </label>
          <label>
            Șablon simulator și risc
            <select name="template" required>
              <option value="">Alege…</option>
              {templates
                .filter((r) => r.account_id === account)
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Denumire experiment
            <input name="name" defaultValue="Cercetare cantitativă" required maxLength={120} />
          </label>
          <label>
            Motor cercetare
            <select name="engine">
              <option value="EVENT">Evenimente + Risk Gateway</option>
              <option value="SCREEN">Screening Arrow exploratoriu</option>
            </select>
          </label>
          <label>
            Etapă cronologică
            <select name="phase">
              <option value="DISCOVERY">Descoperire</option>
              <option value="CALIBRATION">Calibrare</option>
              <option value="VALIDATION">Validare</option>
            </select>
          </label>
          <label>
            Metodă validare
            <select name="mode">
              <option value="DIRECT">Evaluare directă</option>
              <option value="WALK_FORWARD">Walk-forward: selecție pe train, evaluare OOS</option>
            </select>
          </label>
          {(
            [
              ['start', 'Început date', start],
              ['discovery', 'Sfârșit descoperire', between(0.25)],
              ['calibration', 'Sfârșit calibrare', between(0.5)],
              ['validation', 'Sfârșit validare', between(0.75)],
              ['end', 'Sfârșit protocol', end],
            ] as const
          ).map(([name, label, initial]) => (
            <label key={name}>
              {label}
              <input name={name} defaultValue={initial} required />
            </label>
          ))}
          {(
            [
              ['fast', 'Perioadă rapidă', '5'],
              ['slow', 'Perioadă lentă', '20'],
              ['lookback', 'Fereastră indicator', '14'],
              ['volume', 'Volum solicitat', '0.01'],
              ['stop', 'Stop în tick-uri', '20'],
              ['reward', 'Multiplu take-profit', '2'],
              ['hold', 'Durată maximă (secunde)', '3600'],
              ['purge', 'Purge (secunde)', '3600'],
              ['embargo', 'Embargo (secunde)', '60'],
              ['folds', 'Fold-uri walk-forward', '2'],
              ['random', 'Semnale păstrate aleator (%)', '100'],
              ['seed', 'Seed reproductibil', '7'],
              ['costs', 'Multipli stres costuri', '1'],
              ['spread', 'Spread ipotetic BAR', ''],
              ['rows', 'Limită observații', '1000'],
              ['seconds', 'Limită timp (secunde)', '120'],
              ['bootstrap', 'Eșantioane bootstrap', '200'],
            ] as const
          ).map(([name, label, initial]) => (
            <label key={name}>
              {label}
              <input name={name} defaultValue={initial} required={name !== 'spread'} />
            </label>
          ))}
          <label>
            Tip intrare
            <select name="orderType">
              <option value="MARKET">Market</option>
              <option value="LIMIT">Limit</option>
              <option value="STOP">Stop</option>
            </select>
          </label>
          <label>
            Offset intrare (tick-uri)
            <input name="entryOffset" defaultValue="1" required />
          </label>
          <label>
            Expirare ordin pending (secunde)
            <input name="expiry" defaultValue="60" required />
          </label>
          <label>
            Direcții
            <select name="direction">
              <option value="LONG_SHORT">Long și short</option>
              <option value="LONG_ONLY">Doar long</option>
              <option value="SHORT_ONLY">Doar short</option>
            </select>
          </label>
        </div>
        <details>
          <summary>Date pentru confirmare multi-timeframe și sweep-uri</summary>
          {datasets.map((d) => (
            <div key={d.id}>
              <label>
                <input type="checkbox" name="dataset" value={d.id} />
                {d.symbol} · {d.spec.timeframe} · v{d.version}
              </label>
              <select aria-label={`Rol ${d.id}`} name={`role-${d.id}`}>
                <option value="EXECUTION">Flux de execuție</option>
                <option value="CONFIRMATION">Confirmare disponibilă la momentul deciziei</option>
              </select>
            </div>
          ))}
          <label>
            Parametri pentru sweep (JSON, cel mult 16)
            <textarea name="sweep" maxLength={64000} />
          </label>
        </details>
        <details>
          <summary>Configurație avansată pentru portofolii</summary>
          <p>
            Configurație completă conform contractului API; doar strategii din registrul revizuit.
            Nu se acceptă sursă executabilă.
          </p>
          <label>
            Experiment JSON avansat
            <textarea name="advanced" maxLength={250000} />
          </label>
        </details>
        <label>
          <input type="checkbox" required />
          Autorizez copierea politicii verificate în conturi SIMULATED izolate; contul sursă nu este
          tranzacționat.
        </label>
        <label>
          <input type="checkbox" required />
          Accept costurile, incertitudinea intrabar și caracterul exclusiv de cercetare. Nu există
          promisiuni de profit.
        </label>
        <button type="submit" disabled={busy || !account || !dataset}>
          Înregistrează experimentul
        </button>
      </form>
      <section className="panel management-panel" aria-label="Experimente persistente">
        <h3>Joburi de cercetare</h3>
        <button onClick={() => void load()}>Reîncarcă experimentele</button>
        {jobs.map((job) => (
          <article key={job.id}>
            <h4>
              {job.name} · {job.job.state}
            </h4>
            <p>
              {job.strategy} · {job.engine} · {job.phase} · {job.job.progress}% · încercări{' '}
              {job.job.attempts}
            </p>
            {job.job.error && <p role="alert">{job.job.error}</p>}
            {job.job.state === 'SUCCEEDED' && (
              <button onClick={() => void inspect(job.id)}>Rezultate {job.id}</button>
            )}
            {['QUEUED', 'RUNNING', 'RETRY'].includes(job.job.state) && (
              <button
                onClick={() =>
                  void api(`/research/experiments/${job.id}/cancel`, {
                    method: 'POST',
                    csrf: session.csrf_token,
                    body: {},
                  })
                    .then(load)
                    .catch(fail)
                }
              >
                Anulează {job.id}
              </button>
            )}
          </article>
        ))}
      </section>
      {result && (
        <section className="panel management-panel" aria-label="Rezultate experiment">
          <h3>Rezultate stocate · {result.engine}</h3>
          <p>SIMULATED · nicio eligibilitate automată pentru paper/live.</p>
          <label>
            Scenariu rezultat
            <select value={trial} onChange={(e) => void inspect(selected, Number(e.target.value))}>
              {result.trials.map((t, i) => (
                <option key={i} value={i}>
                  Scenariu {t.ordinal} · stres {t.cost_multiplier}
                </option>
              ))}
            </select>
          </label>
          <EquityChart points={points} />
          <details>
            <summary>Capital exact stocat</summary>
            <pre>{json(points)}</pre>
          </details>
          <h4>Metrici și incertitudine</h4>
          <pre>{json(result.trials[trial])}</pre>
          <label>
            Replay și analiză
            <select
              value={section}
              onChange={(e) => {
                setSection(e.target.value);
                setOffset(0);
              }}
            >
              {['trades', 'fills', 'signals', 'replay', 'exposure', 'walk_forward'].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button
            onClick={() =>
              void api(
                `/research/experiments/${selected}/results?section=${section}&trial=${trial}&offset=${offset}&limit=100`,
              )
                .then(setDetails)
                .catch(fail)
            }
          >
            Încarcă analiza
          </button>
          <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>
            Pagina anterioară
          </button>
          <button onClick={() => setOffset(offset + 100)}>Pagina următoare</button>
          <button
            onClick={() =>
              void api(`/research/experiments/${selected}/provenance`).then(setDetails).catch(fail)
            }
          >
            Proveniență și număr total de încercări
          </button>
          <pre>{json(details)}</pre>
        </section>
      )}
      <form
        aria-label="Compară experimente"
        className="panel management-panel"
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          void api(`/research/experiments/${value(f, 'left')}/compare/${value(f, 'right')}`)
            .then(setDetails)
            .catch(fail);
        }}
      >
        <h3>Comparație cu condiții identice</h3>
        {['left', 'right'].map((name) => (
          <label key={name}>
            {name === 'left' ? 'Experiment A' : 'Experiment B'}
            <select name={name} required>
              {jobs
                .filter((j) => j.job.state === 'SUCCEEDED')
                .map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.name} · {j.id}
                  </option>
                ))}
            </select>
          </label>
        ))}
        <button>Compară rezultate stocate</button>
      </form>
      <section className="panel management-panel">
        <h3>Holdout final separat</h3>
        <p>
          Sigilarea blochează accesul obișnuit și permite o singură evaluare finală autorizată.
          Expunerea anterioară nu este certificată: datele existente nu sunt descrise ca „neatinse”.
        </p>
        <form
          aria-label="Sigilează holdout"
          onSubmit={(e) => {
            e.preventDefault();
            void api('/research/holdouts', {
              method: 'POST',
              csrf: session.csrf_token,
              body: {
                dataset_id: dataset,
                reason: 'Evaluare finală separată autorizată de proprietar',
                acknowledged_prior_exposure_unknown: true,
              },
            })
              .then(() => {
                setNotice('Holdout sigilat. Accesul obișnuit este blocat.');
                return load();
              })
              .catch(fail);
          }}
        >
          <label>
            <input type="checkbox" required />
            Confirm că expunerea anterioară este necunoscută și accesul va fi restricționat.
          </label>
          <button disabled={!dataset}>Sigilează setul selectat</button>
        </form>
        <pre>{json(seals)}</pre>
        <form
          aria-label="Eliberează evaluarea finală"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            try {
              const experiment = JSON.parse(value(f, 'frozen')) as Plan;
              void api<{ id: string }>(`/research/holdouts/${value(f, 'seal')}/release`, {
                method: 'POST',
                csrf: session.csrf_token,
                body: {
                  experiment,
                  acknowledged_single_final_evaluation: true,
                  acknowledged_not_certified_untouched: true,
                },
              })
                .then((release) =>
                  api('/research/experiments', {
                    method: 'POST',
                    csrf: session.csrf_token,
                    body: { ...experiment, holdout_release_id: release.id },
                  }),
                )
                .then(() => {
                  setNotice('Evaluare finală unică înregistrată.');
                  return load();
                })
                .catch(fail);
            } catch (error) {
              fail(error);
            }
          }}
        >
          <label>
            Holdout sigilat
            <select name="seal" required>
              {seals.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Configurație finală înghețată (JSON)
            <textarea name="frozen" required maxLength={250000} />
          </label>
          <label>
            <input type="checkbox" required />
            Autorizez o singură evaluare finală; rezultatul nu va fi folosit pentru tuning repetat
            prezentat drept test independent.
          </label>
          <button>Autorizează și înregistrează evaluarea finală</button>
        </form>
      </section>
    </section>
  );
}
