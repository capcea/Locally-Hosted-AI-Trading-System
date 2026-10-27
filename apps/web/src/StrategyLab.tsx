import { useCallback, useEffect, useState, useRef } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError, safeError } from './management-api';
import type { RecordItem, Session } from './management-api';
import type { components } from './generated/api';
import { useRoute, navigate, Link } from './navigation/history';
import { progressPath, resultPath } from './navigation/routes';
import { EquityChart, ResultSummary, StoredRecords, object } from './results/ResultView';
import type { Point } from './results/ResultView';
import { Evidence } from './ui/Controls';
import FinalEvaluation from './FinalEvaluation';
import AdvancedStatistics from './results/AdvancedStatistics';
import { allRecords } from './records';
import { readResearchDraft, writeResearchDraft } from './research-drafts';
import { strategyLabels, jobLabels, phaseLabels, sourceLabels } from './copy/ro';

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
  job: {
    state: string;
    progress: number;
    attempts: number;
    error: string | null;
    cancel_requested?: boolean;
  };
  result: unknown;
};
type Seal = { id: string; dataset_id: string; prior_exposure: string };
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

export default function StrategyLab({
  session,
  onExpired,
  initialAccount = '',
  onAccountChange,
}: {
  session: Session;
  onExpired: () => void;
  initialAccount?: string;
  onAccountChange?: (id: string) => void;
}) {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [templates, setTemplates] = useState<RunSummary[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [seals, setSeals] = useState<Seal[]>([]);
  const route = useRoute();
  const savedDraft = readResearchDraft(session.user.id);
  const safeDraft =
    !initialAccount || initialAccount === savedDraft?.account ? savedDraft : undefined;
  const [step, setStep] = useState(safeDraft?.step ?? 1);
  const [account, setAccount] = useState(safeDraft?.account ?? initialAccount);
  const [templateId, setTemplateId] = useState(safeDraft?.templateId ?? '');
  const draftValues = useRef<Record<string, string>>(safeDraft?.values ?? {});
  const [setup, setSetup] = useState<{
    run: Run;
    context: Context | null;
    status: components['schemas']['AccountStatus'];
    policies: components['schemas']['PolicyView'][];
    profiles: components['schemas']['ProfileView'][];
  } | null>(null);
  const [setupError, setSetupError] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [jobsFailed, setJobsFailed] = useState(false);
  const [historyPage, setHistoryPage] = useState(0);
  const [focusedJob, setFocusedJob] = useState<Job | null>(null);
  const [cancelRequested, setCancelRequested] = useState<string[]>([]);
  const inspectGeneration = useRef(0);
  const [inputSources, setInputSources] = useState<Record<string, string>>({});
  const [provenance, setProvenance] = useState<unknown>(null);
  const [chartTotal, setChartTotal] = useState(0);
  const [comparisonContext, setComparisonContext] = useState<{ left: unknown; right: unknown }>({
    left: null,
    right: null,
  });
  const [comparison, setComparison] = useState<unknown>(null);
  const [reviewValues, setReviewValues] = useState<Record<string, string>>(safeDraft?.review ?? {});
  const formRef = useRef<HTMLFormElement>(null);
  const stepHeading = useRef<HTMLHeadingElement>(null);
  const [dataset, setDataset] = useState(safeDraft?.dataset ?? '');
  const [strategy, setStrategy] = useState<Plan['strategy']>(
    (safeDraft?.strategy as Plan['strategy']) ?? 'EMA_TREND',
  );
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [details, setDetails] = useState<unknown>(null);
  const [section, setSection] = useState('trades');
  const [trial, setTrial] = useState(0);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const requestKey = useRef(safeDraft?.requestKey ?? crypto.randomUUID());
  const submittedPlan = useRef<Plan | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  useEffect(() => {
    if (onAccountChange && initialAccount !== account) {
      if (submittedPlan.current) {
        onAccountChange?.(account);
        setError(
          'Solicitarea anterioară are un răspuns incert. Verifică activitatea acestui cont înainte de a schimba configurația.',
        );
        return;
      }
      setAccount(initialAccount);
      setDataset('');
      setTemplateId('');
      setSetup(null);
      setStep(1);
      draftValues.current = {};
      setReviewValues({});
    }
  }, [initialAccount, account, onAccountChange]);
  const fail = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && error.status === 401) onExpired();
      setError(safeError(error));
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    try {
      const values = await Promise.allSettled([
        api<Strategy[]>('/research/strategies'),
        allRecords('accounts'),
        api<Job[]>(`/research/experiments?offset=${historyPage * 100}&limit=100`),
        api<Seal[]>('/research/holdouts'),
        api<RunSummary[]>('/execution/simulations?limit=50'),
      ] as const);
      const [s, a, j, h, r] = values;
      if (s.status === 'fulfilled') setStrategies(s.value);
      if (a.status === 'fulfilled') setAccounts(a.value);
      setJobsFailed(j.status === 'rejected');
      if (j.status === 'fulfilled') setJobs(j.value);
      if (h.status === 'fulfilled') setSeals(h.value);
      if (r.status === 'fulfilled') setTemplates(r.value);
      setLoaded(true);
      const failure = values.find((v) => v.status === 'rejected');
      if (failure?.status === 'rejected') fail(failure.reason);
    } catch (error) {
      fail(error);
    }
  }, [fail, historyPage]);
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 2000);
    return () => clearInterval(timer);
  }, [load]);
  useEffect(() => {
    setDatasets([]);
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
      const generation = ++inspectGeneration.current;
      setSelected(id);
      setTrial(index);
      setError('');
      setResult(null);
      setPoints([]);
      setProvenance(null);
      setDetails(null);
      setInputSources({});
      const [summary, curve, manifest] = await Promise.allSettled([
        api<Result>(`/research/experiments/${id}/results`),
        api<{ items: Point[]; total: number }>(
          `/research/experiments/${id}/results?section=equity&trial=${index}&limit=500&chart=true`,
        ),
        api(`/research/experiments/${id}/provenance`),
      ] as const);
      if (generation !== inspectGeneration.current) return;
      if (summary.status === 'fulfilled') setResult(summary.value);
      else fail(summary.reason);
      if (curve.status === 'fulfilled') {
        setPoints(curve.value.items);
        setChartTotal(curve.value.total);
      } else fail(curve.reason);
      if (manifest.status === 'fulfilled') {
        setProvenance(manifest.value);
        const pins = object(manifest.value).plan
          ? object(object(manifest.value).plan).datasets
          : [];
        if (Array.isArray(pins)) {
          const sources = await Promise.all(
            pins.map(async (pin) => {
              const id = String(object(pin).dataset_id);
              try {
                const d = await api<Dataset>(`/market/datasets/${id}`);
                return [id, d.spec.provenance] as const;
              } catch {
                return [id, 'UNKNOWN'] as const;
              }
            }),
          );
          if (generation === inspectGeneration.current)
            setInputSources(Object.fromEntries(sources));
        }
      } else fail(manifest.reason);
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
      let actual: Plan;
      const advanced = value(form, 'advanced').trim();
      if (advanced) {
        actual = JSON.parse(advanced) as Plan;
        if (actual.phase === 'FINAL_HOLDOUT' || actual.holdout_release_id)
          throw new ApiError(
            409,
            'Evaluarea finală necesită fluxul separat de autorizare. Folosește Evaluare finală protejată; nu consumăm o autorizare din testul obișnuit.',
          );
        if (actual.source_account_id !== account)
          throw new Error(
            'Datele și contul selectat trebuie să corespundă configurației avansate.',
          );
      } else {
        const ids = form.getAll('dataset').map(String);
        const chosen = ids.length ? ids : [dataset];
        const template = await api<Run>(`/execution/simulations/${value(form, 'template')}`);
        const contexts = await api<{ context: Context }[]>(`/risk/runs/${template.id}/contexts`);
        if (!contexts.length)
          throw new Error('Configurează și verifică mai întâi contextul de risc al șablonului.');
        const definition = strategies.find((s) => s.id === strategy)!;
        const parameters: Plan['parameters'][number] = {
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
          session_exit_buffer_seconds: 60,
          flat_before_risk_reset: true,
          cross_asset_confirmation: false,
          confirmation_direction: 'SAME',
          confirmation_max_age_seconds: 86400,
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
          signal_timeframe: value(form, 'signalTimeframe') as Plan['signal_timeframe'],
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
              role:
                value(form, `role-${id}`) === 'FX'
                  ? 'FX'
                  : value(form, `role-${id}`) === 'CONFIRMATION'
                    ? 'CONFIRMATION'
                    : value(form, `role-${id}`) === 'SIGNAL'
                      ? 'SIGNAL'
                      : 'EXECUTION',
              symbol: { ...template.state.spec, symbol: d.spec.source_symbol },
              context: {
                ...contexts[0].context,
                financial: {
                  ...contexts[0].context.financial,
                  automated: true,
                  execution_style: 'INTRADAY_BENCHMARK',
                },
              },
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
        actual = plan;
      }
      actual.key = requestKey.current;
      if (submittedPlan.current) actual = submittedPlan.current;
      else submittedPlan.current = actual;
      const created = await api<Job>('/research/experiments', {
        method: 'POST',
        csrf: session.csrf_token,
        body: actual,
      });
      requestKey.current = crypto.randomUUID();
      submittedPlan.current = null;
      setStep(1);
      setSelected(created.id);
      setResult(null);
      setPoints([]);
      setNotice(`Test înregistrat: ${created.id}`);
      navigate(progressPath(created.id));
      await load();
    } catch (error) {
      if (error instanceof ApiError && error.status < 500) submittedPlan.current = null;
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
  useEffect(() => {
    stepHeading.current?.focus();
  }, [step]);
  useEffect(() => {
    if (!templateId || !account) {
      setSetup(null);
      return;
    }
    let active = true;
    setSetup(null);
    setSetupError('');
    void Promise.all([
      api<Run>(`/execution/simulations/${templateId}`),
      api<{ context: Context }[]>(`/risk/runs/${templateId}/contexts`),
      api<components['schemas']['AccountStatus']>(`/risk/accounts/${account}/status`),
      api<components['schemas']['PolicyView'][]>(`/risk/accounts/${account}/policies`),
      api<components['schemas']['ProfileView'][]>(`/risk/accounts/${account}/profiles`),
    ])
      .then(([run, contexts, status, policies, profiles]) => {
        if (active)
          setSetup({ run, context: contexts[0]?.context ?? null, status, policies, profiles });
      })
      .catch((e) => {
        if (active) setSetupError(safeError(e));
      });
    return () => {
      active = false;
    };
  }, [templateId, account]);
  useEffect(() => {
    if (!route.experimentId) return;
    setFocusedJob(null);
    let active = true;
    const read = () =>
      api<Job>(`/research/experiments/${route.experimentId}`)
        .then((j) => {
          if (active) setFocusedJob(j);
        })
        .catch(fail);
    void read();
    const timer = setInterval(() => void read(), 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [route.experimentId, fail]);
  useEffect(() => {
    if (route.experimentId && route.area === 'results') void inspect(route.experimentId);
  }, [route.experimentId, route.area, inspect]);
  const verifiedPolicy = setup?.policies.find(
    (p) =>
      p.status === 'VERIFIED' &&
      p.terms.automation_permitted &&
      Date.parse(p.effective_at) <= Date.parse(reviewValues.start ?? start) &&
      Date.parse(p.expires_at) >= Date.parse(reviewValues.end ?? end),
  );
  useEffect(() => {
    const mapping: Record<string, string> = {
      result: 'trades',
      tranzactii: 'trades',
      decizii: 'replay',
      validare: 'walk_forward',
      provenienta: 'provenance',
    };
    const selected = mapping[route.section ?? ''];
    if (selected) {
      setSection(selected);
      setOffset(0);
    }
  }, [route.section]);
  useEffect(() => {
    if (!route.experimentId || route.area !== 'results') return;
    let active = true;
    const path =
      section === 'provenance'
        ? `/research/experiments/${route.experimentId}/provenance`
        : `/research/experiments/${route.experimentId}/results?section=${section}&trial=${trial}&offset=${offset}&limit=100`;
    void api(path)
      .then((value) => {
        if (active) setDetails(value);
      })
      .catch((e) => {
        if (active) fail(e);
      });
    return () => {
      active = false;
    };
  }, [route.experimentId, route.area, section, trial, offset, fail]);
  const readySetup = Boolean(
    setup?.context &&
    verifiedPolicy &&
    setup.profiles.some((p) => p.scope_key === 'ACCOUNT') &&
    setup.status.configured &&
    setup.status.data_verified &&
    setup.status.ledger_verified &&
    !setup.status.manual_stop &&
    !setup.status.automatic_stop &&
    setup.run.account_id === account &&
    setup.run.instrument_id === data?.instrument_id,
  );
  const showWizard =
    route.area === 'research' && ['index', 'nou'].includes(route.section ?? 'index');
  const showFinal = route.section === 'evaluare-finala';
  const showHistory = ['index', 'activitate', 'progress', 'results'].includes(
    route.section ?? 'index',
  );
  const showResults = route.area === 'results' && Boolean(route.experimentId);
  useEffect(() => {
    writeResearchDraft(session.user.id, {
      account,
      dataset,
      templateId,
      strategy,
      step,
      requestKey: requestKey.current,
      values: draftValues.current,
      review: reviewValues,
    });
  }, [session.user.id, account, dataset, templateId, strategy, step, reviewValues]);
  useEffect(() => {
    if (!showWizard || !formRef.current) return;
    for (const control of formRef.current.querySelectorAll<HTMLInputElement | HTMLSelectElement>(
      'input[name],select[name]',
    )) {
      if (
        Object.hasOwn(draftValues.current, control.name) &&
        control.type !== 'checkbox' &&
        control.type !== 'file' &&
        !['template'].includes(control.name)
      )
        control.value = draftValues.current[control.name];
    }
  }, [showWizard, dataset]);
  const next = () => {
    const current = formRef.current?.querySelector(`fieldset[data-step="${step}"]`);
    const controls = current?.querySelectorAll<HTMLInputElement | HTMLSelectElement>(
      'input,select,textarea',
    );
    if (controls)
      for (const control of controls) {
        if (!control.checkValidity()) {
          let parent = control.parentElement;
          while (parent && parent !== current) {
            if (parent instanceof HTMLDetailsElement) parent.open = true;
            parent = parent.parentElement;
          }
          control.reportValidity();
          return;
        }
      }
    if (step === 3 && formRef.current) {
      const values = new FormData(formRef.current);
      const times = ['start', 'discovery', 'calibration', 'validation', 'end'].map((key) =>
        Date.parse(String(values.get(key))),
      );
      if (times.some((time, i) => !Number.isFinite(time) || (i > 0 && time <= times[i - 1]))) {
        setError(
          'Perioadele trebuie să fie momente UTC valide, strict în ordine: început, descoperire, calibrare, validare, sfârșit.',
        );
        return;
      }
    }
    if (step === 2 && !currentDefinition) {
      setError('Strategia nu poate fi verificată. Reîncarcă biblioteca înainte de a continua.');
      return;
    }
    if (step === 4 && !readySetup) {
      setError('Configurația nu este pregătită. Verifică datele, contextul și oprirea contului.');
      return;
    }
    if (step >= 3 && formRef.current)
      setReviewValues(
        Object.fromEntries(
          Array.from(new FormData(formRef.current)).filter(
            ([key, v]) =>
              [
                'name',
                'start',
                'end',
                'phase',
                'mode',
                'costs',
                'rows',
                'seconds',
                'engine',
              ].includes(key) && typeof v === 'string',
          ),
        ) as Record<string, string>,
      );
    setError('');
    setStep(Math.min(5, step + 1));
  };
  return (
    <section aria-label="Testează strategii" className="research-lab">
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {route.section === 'index' && (
        <section className="panel">
          <h2>Testează pe date istorice</h2>
          <p>
            Alege date admise și o configurație revizuită. Nu există strategii generate de AI sau
            ordine către brokeri.
          </p>
          <Link className="primary-button" href="/testeaza/nou">
            Pregătește un test
          </Link>
        </section>
      )}
      {route.section === 'strategii' && (
        <section className="panel">
          <h2>Strategii revizuite</h2>
          <p>Etaloane experimentale, nu recomandări de investiții.</p>
          {strategies.map((s) => (
            <article key={s.id}>
              <h3>{strategyLabels[s.id] ?? s.id}</h3>
              <p>
                {s.entry} · {s.exit}
              </p>
              <Evidence title={`${s.id} · versiune și parametri`} value={s} />
            </article>
          ))}
          <Link href="/testeaza/nou">Alege strategia într-un test nou</Link>
        </section>
      )}
      {showWizard && (
        <form
          ref={formRef}
          aria-label="Configurează testul istoric"
          onInput={(event) => {
            const target = event.target as HTMLInputElement;
            if (
              target.name &&
              target.type !== 'checkbox' &&
              target.type !== 'file' &&
              !['advanced', 'sweep'].includes(target.name)
            )
              draftValues.current[target.name] = target.value;
          }}
          className="panel management-panel research-wizard"
          key={dataset}
          onSubmit={(event) => {
            if (step !== 5) {
              event.preventDefault();
              next();
            } else void submit(event);
          }}
        >
          <h2 ref={stepHeading} tabIndex={-1}>
            Testează pe date istorice · Pasul {step} din 5
          </h2>
          <ol className="wizard-steps">
            {['Piață', 'Strategie', 'Perioadă', 'Configurație revizuită', 'Revizuire'].map(
              (label, i) => (
                <li key={label} aria-current={step === i + 1 ? 'step' : undefined}>
                  {i + 1}. {label}
                </li>
              ),
            )}
          </ol>
          <fieldset data-step="1" hidden={step !== 1}>
            <legend>Alege piața</legend>
            <p>
              Sunt afișate numai seturile VALID la care ai acces. Originea declarată nu devine
              independent verificată printr-un import.
            </p>
            <div className="research-fields">
              <label>
                Contul testului
                <select
                  aria-label="Contul testului"
                  required
                  value={account}
                  onChange={(e) => {
                    setAccount(e.target.value);
                    onAccountChange?.(e.target.value);
                    setDataset('');
                    setTemplateId('');
                    setSetup(null);
                    setStep(1);
                    draftValues.current = {};
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
                <select
                  aria-label="Set de date principal"
                  required
                  value={dataset}
                  onChange={(e) => {
                    setDataset(e.target.value);
                    draftValues.current = {};
                  }}
                >
                  <option value="">Alege un set VALID…</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.symbol} · {d.spec.timeframe} · v{d.version} · {d.record_count} observații
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {data && (
              <p>
                {sourceLabels[data.spec.provenance] ?? data.spec.provenance} · {data.spec.start} →{' '}
                {data.spec.end} · {data.record_count} observații. Nu presupunem tick-uri lipsă sau
                cinci ani de acoperire.
              </p>
            )}
            {loaded && !accounts.length && (
              <p>
                Nu există conturi în lista citită.{' '}
                <Link href="/conturi">Configurează un cont pentru simulare</Link>
              </p>
            )}
            {account && !datasets.length && (
              <p>
                Nu există date admise în lista citită pentru această alegere sau citirea nu s-a
                încheiat.{' '}
                <Link href="/testeaza/date/import">Verifică ori importă date istorice</Link>
              </p>
            )}
          </fieldset>
          <fieldset data-step="2" hidden={step !== 2}>
            <legend>Alege strategia</legend>
            <p>Strategii fixe revizuite, fără promisiuni de profit.</p>
            <label>
              Strategie de referință
              <select
                aria-label="Strategie de referință"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as Plan['strategy'])}
              >
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {strategyLabels[s.id] ?? s.id} · {s.version}
                  </option>
                ))}
              </select>
            </label>
            {currentDefinition && (
              <details>
                <summary>Contract, versiune și parametri</summary>
                <pre tabIndex={0}>{json(currentDefinition)}</pre>
              </details>
            )}
          </fieldset>
          <fieldset data-step="3" hidden={step !== 3}>
            <legend>Alege perioada și tipul evaluării</legend>
            <p>
              OOS este o evaluare ulterioară conform protocolului; nu este automat o perioadă
              nevăzută. Evaluarea finală protejată are autorizare separată.
            </p>
            <div className="research-fields">
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
              <label>
                Etapă cronologică
                <select aria-label="Etapă cronologică" name="phase">
                  <option value="DISCOVERY">Descoperire</option>
                  <option value="CALIBRATION">Calibrare</option>
                  <option value="VALIDATION">Validare</option>
                </select>
              </label>
              <label>
                Metodă validare
                <select aria-label="Metodă validare" name="mode">
                  <option value="DIRECT">Evaluare directă</option>
                  <option value="WALK_FORWARD">
                    Walk-forward: selecție pe train, evaluare OOS
                  </option>
                </select>
              </label>
            </div>
          </fieldset>
          <fieldset data-step="4" hidden={step !== 4}>
            <legend>Alege configurația revizuită</legend>
            <div className="research-fields">
              <label>
                Șablon simulator și risc
                <select
                  aria-label="Șablon simulator și risc"
                  name="template"
                  required
                  value={templateId}
                  onChange={(e) => setTemplateId(e.target.value)}
                >
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
            </div>
            <p>
              O configurație existentă nu este o aprobare automată. Verificăm contextul,
              instrumentul și starea contului; serverul rămâne autoritatea finală.
            </p>
            {setupError && <p role="alert">{setupError}</p>}
            {templateId && !setup && !setupError && (
              <p role="status">Verificăm configurația existentă…</p>
            )}
            <ul>
              <li>
                Context monetar existent:{' '}
                {setup?.context ? 'citit' : 'lipsește sau nu poate fi verificat'}
              </li>
              <li>
                Specificație pe același instrument:{' '}
                {setup?.run.instrument_id === data?.instrument_id && data
                  ? 'corespunde înregistrărilor citite'
                  : 'neconfirmată'}
              </li>
              <li>
                Politică verificată care acoperă datele și permite automatizarea:{' '}
                {verifiedPolicy
                  ? `versiunea ${verifiedPolicy.version}`
                  : 'neconfirmată — revizuire obligatorie'}
              </li>
              <li>
                Limite configurate:{' '}
                {setup?.profiles.some((p) => p.scope_key === 'ACCOUNT')
                  ? 'profil ACCOUNT citit; versiuni în dovezi'
                  : 'neconfirmate — lipsește profilul aplicat contului'}
              </li>
              <li>
                Oprire persistentă:{' '}
                {setup
                  ? setup.status.manual_stop || setup.status.automatic_stop
                    ? 'activă — revizuire obligatorie'
                    : 'nicio oprire în răspunsul citit'
                  : 'UNKNOWN'}
              </li>
            </ul>
            <p>
              <Link href={account ? `/conturi/${account}/siguranta` : '/conturi/siguranta'}>
                Configurează limitele, politica și contextul
              </Link>{' '}
              ·{' '}
              <Link href="/conturi/avansat/simulator">
                Pregătește specificația în simulatorul avansat
              </Link>
              . Nu substituim o configurație fictivă.
            </p>
            {setup && (
              <Evidence
                title="Versiuni, costuri și politici citite — verifică aplicabilitatea"
                value={setup}
              />
            )}
            <details>
              <summary>Setări avansate: parametri, costuri, portofolii și cote</summary>
              <p>
                Maximum 5000 observații, 24 scenarii și 300 secunde conform contractului curent;
                limitele proprietarului se verifică pe server. Lipsa marjei, calendarului sau
                drepturilor nu este completată automat.
              </p>
              <div className="research-fields">
                <label>
                  Timeframe semnal
                  <select aria-label="Timeframe semnal" name="signalTimeframe">
                    <option value="NATIVE">Nativ fluxului de execuție</option>
                    {['TICK', 'M1', 'M5', 'M15', 'H1', 'H4', 'D1'].map((frame) => (
                      <option key={frame} value={frame}>
                        {frame} — flux SIGNAL separat obligatoriu
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Motor cercetare
                  <select aria-label="Motor cercetare" name="engine">
                    <option value="EVENT">Evenimente + Risk Gateway</option>
                    <option value="SCREEN">Screening Arrow exploratoriu</option>
                  </select>
                </label>
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
                  <select aria-label="Tip intrare" name="orderType">
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
                  <select aria-label="Direcții" name="direction">
                    <option value="LONG_SHORT">Long și short</option>
                    <option value="LONG_ONLY">Doar long</option>
                    <option value="SHORT_ONLY">Doar short</option>
                  </select>
                </label>

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
                        <option value="FX">Conversie FX din tick-uri observate</option>
                        <option value="SIGNAL">Semnal pe observații închise</option>
                        <option value="CONFIRMATION">
                          Confirmare disponibilă la momentul deciziei
                        </option>
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
                    Configurație completă conform contractului API; doar strategii din registrul
                    revizuit. Nu se acceptă sursă executabilă.
                  </p>
                  <label>
                    Experiment JSON avansat
                    <textarea name="advanced" maxLength={250000} />
                  </label>
                </details>
              </div>
            </details>
          </fieldset>
          <fieldset data-step="5" hidden={step !== 5}>
            <legend>Verifică testul înainte de pornire</legend>
            <dl>
              <dt>Piață și origine</dt>
              <dd>
                {data?.symbol} · {sourceLabels[data?.spec.provenance ?? ''] ?? 'neconfirmată'} ·
                execuție simulată
              </dd>
              <dt>Cont și strategie</dt>
              <dd>
                {accounts.find((a) => a.id === account)?.data.name} ·{' '}
                {strategyLabels[strategy] ?? strategy}
              </dd>
              <dt>Perioadă</dt>
              <dd>
                {reviewValues.start} → {reviewValues.end}
              </dd>
              <dt>Evaluare</dt>
              <dd>
                {phaseLabels[reviewValues.phase]} · {reviewValues.mode}
              </dd>
              <dt>Costuri și limite</dt>
              <dd>
                Stres {reviewValues.costs}; {reviewValues.rows} observații; {reviewValues.seconds}{' '}
                secunde. Comisioanele și derapajul sunt cele ale configurației revizuite. Finanțarea
                se verifică în context.
              </dd>
            </dl>
            {setup && (
              <section aria-label="Limitele și politica revizuite pentru test">
                <h4>Limitele și politica revizuite</h4>
                <p>
                  Politică{' '}
                  {verifiedPolicy?.kind === 'PROP' ? 'pentru programul acestui cont' : 'personală'}{' '}
                  · versiunea {verifiedPolicy?.version ?? 'neconfirmată'} · valabilă până la{' '}
                  {verifiedPolicy?.expires_at ?? 'necunoscut'}. Verificarea este pentru acest cont
                  și perioadă, nu pentru toate conturile unei firme.
                </p>
                <dl>
                  {setup.profiles.map((profile) => (
                    <div key={profile.id}>
                      <dt>
                        {profile.scope_key} · versiunea {profile.version}
                      </dt>
                      <dd>
                        Pe tranzacție: {profile.limits.per_trade_pct}%; pierdere zilnică:{' '}
                        {profile.limits.daily_loss_pct}%; scădere totală:{' '}
                        {profile.limits.total_loss_pct}%; risc agregat:{' '}
                        {profile.limits.aggregate_risk_pct}%.
                      </dd>
                    </div>
                  ))}
                  <dt>Până la limita zilnică, conform contului sursă</dt>
                  <dd>
                    {setup.status.daily_headroom ?? 'UNKNOWN'} {setup.status.currency}
                  </dd>
                  <dt>Până la limita totală</dt>
                  <dd>
                    {setup.status.total_headroom ?? 'UNKNOWN'} {setup.status.currency}
                  </dd>
                </dl>
                <p>
                  Valori citite pentru contul sursă, ceas {setup.status.clock ?? 'necunoscut'}.
                  Dimensionarea și verificarea finală aparțin Risk Gateway. Nicio cifră nu este o
                  pierdere maximă viitoare garantată.
                </p>
                <Evidence
                  title="Context, surse, versiuni și costuri exacte ale configurației"
                  value={setup}
                />
              </section>
            )}
            <p>
              Rezultatul este istoric simulat. Nu este o promisiune, un sold real sau o aprobare de
              tranzacționare.
            </p>
            <label>
              <input type="checkbox" required />
              Autorizez copierea politicii verificate în conturi SIMULATED izolate; contul sursă nu
              este tranzacționat.
            </label>
            <label>
              <input type="checkbox" required />
              Accept costurile, incertitudinea intrabar și caracterul exclusiv de cercetare. Nu
              există promisiuni de profit.
            </label>
          </fieldset>
          <div className="wizard-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={step === 1 || busy || Boolean(submittedPlan.current)}
              onClick={() => setStep(step - 1)}
            >
              Înapoi
            </button>
            {step < 5 ? (
              <button
                type="button"
                onClick={next}
                disabled={
                  !loaded || (step === 1 && (!account || !dataset)) || (step === 4 && !readySetup)
                }
              >
                Continuă
              </button>
            ) : (
              <button type="submit" disabled={busy || !readySetup}>
                {submittedPlan.current
                  ? 'Retrimite aceeași solicitare'
                  : 'Pornește testul în simulare'}
              </button>
            )}
          </div>
          {submittedPlan.current && !busy && (
            <p role="alert">
              Răspunsul solicitării este incert. Configurația trimisă rămâne fixată. Verifică
              Activitatea; o retrimitere folosește exact aceeași cheie și configurație, nu creează o
              variantă nouă.
            </p>
          )}
          {!loaded && <p role="status">Verificăm datele necesare…</p>}
          {step === 4 && !readySetup && (
            <p>
              Continuarea este blocată până la o configurație compatibilă, context și limite
              revizuite, fără oprire activă. Nu deblocăm automat contul.
            </p>
          )}
        </form>
      )}
      {showHistory && (
        <section className="panel" aria-label="Experimente persistente">
          <h2>{route.section === 'progress' ? 'Progresul testului' : 'Activitatea testelor'}</h2>
          {jobsFailed && (
            <p role="alert">
              UNKNOWN · istoricul nu poate fi reîncărcat. Nu presupunem că lipsa unui răspuns
              înseamnă lipsa testelor.
            </p>
          )}
          <p>
            Stările și procentele provin din server. Nu estimăm durata sau sănătatea procesului de
            calcul.
          </p>
          <button className="secondary-button" onClick={() => void load()}>
            Reîncarcă experimentele
          </button>
          {(route.experimentId
            ? focusedJob
              ? [focusedJob]
              : []
            : jobs.filter((j) => route.section !== 'results' || j.job.state === 'SUCCEEDED')
          ).map((job) => (
            <article key={job.id} className="management-record">
              <h3>
                {job.name} · {job.job.state}
              </h3>
              <p>
                {jobLabels[job.job.state] ?? 'Stare necunoscută'} · {job.job.progress}% raportat ·
                încercări {job.job.attempts} · {phaseLabels[job.phase] ?? job.phase}
              </p>
              {job.job.error && (
                <p className="notice">
                  Testul s-a oprit. Nu publicăm rezultate incomplete. Verifică datele, configurația
                  și diagnosticul permis.
                </p>
              )}
              <Evidence title="Identificator și stare tehnică" value={job} />
              {job.job.state === 'SUCCEEDED' ? (
                <Link className="primary-button" href={resultPath(job.id)}>
                  Vezi rezultatul {job.name}
                </Link>
              ) : (
                <Link href={progressPath(job.id)}>Deschide progresul</Link>
              )}
              {['QUEUED', 'RUNNING', 'RETRY'].includes(job.job.state) && (
                <>
                  <button
                    className="secondary-button"
                    disabled={cancelRequested.includes(job.id) || job.job.cancel_requested}
                    onClick={() =>
                      void api<Job>(`/research/experiments/${job.id}/cancel`, {
                        method: 'POST',
                        csrf: session.csrf_token,
                        body: {},
                      })
                        .then((j) => {
                          setCancelRequested((old) => [...old, job.id]);
                          setFocusedJob(j);
                          return load();
                        })
                        .catch(fail)
                    }
                  >
                    Solicită anularea {job.name}
                  </button>
                  {(cancelRequested.includes(job.id) || job.job.cancel_requested) && (
                    <p role="status">
                      Anularea a fost cerută. Așteptăm starea finală; finalizarea poate câștiga
                      cursa.
                    </p>
                  )}
                </>
              )}
            </article>
          ))}
          {!jobs.length && loaded && !jobsFailed && !route.experimentId && (
            <p>
              Nu există teste în pagina citită. Un rezultat gol nu confirmă că toate paginile
              istorice sunt goale.
            </p>
          )}
          {!route.experimentId && (
            <div className="wizard-actions">
              <button
                className="secondary-button"
                disabled={historyPage === 0}
                onClick={() => setHistoryPage(historyPage - 1)}
              >
                Teste mai recente
              </button>
              <span>Pagina {historyPage + 1} · maximum100 înregistrări</span>
              <button
                className="secondary-button"
                disabled={jobs.length < 100}
                onClick={() => setHistoryPage(historyPage + 1)}
              >
                Teste mai vechi
              </button>
            </div>
          )}
        </section>
      )}
      {showResults && result && (
        <section className="panel" aria-label="Rezultate experiment">
          <h2>Rezultatul testului</h2>
          <label>
            Scenariu rezultat
            <select
              aria-label="Scenariu rezultat"
              value={trial}
              onChange={(e) => void inspect(selected, Number(e.target.value))}
            >
              {result.trials.map((t, i) => (
                <option key={i} value={i}>
                  Scenariu {t.ordinal} · stres {t.cost_multiplier}
                </option>
              ))}
            </select>
          </label>
          <ResultSummary
            result={result}
            trial={trial}
            provenance={provenance}
            inputSources={inputSources}
          />
          <EquityChart
            points={points}
            total={chartTotal}
            currency={String(
              object(object(provenance).plan).assumptions
                ? (object(object(object(provenance).plan).assumptions).account_currency ??
                    'neconfirmată')
                : 'neconfirmată',
            )}
          />
          <nav className="section-navigation" aria-label="Detalii rezultat">
            {[
              ['', 'Sinteză'],
              ['tranzactii', 'Tranzacții'],
              ['decizii', 'Decizii și replay'],
              ['validare', 'Validare'],
              ['provenienta', 'De unde provin datele'],
            ].map(([slug, label]) => (
              <Link key={slug} href={resultPath(selected, slug)}>
                {label}
              </Link>
            ))}
          </nav>
          <label>
            Replay și analiză
            <select
              aria-label="Replay și analiză"
              value={section}
              onChange={(e) => {
                setSection(e.target.value);
                setOffset(0);
              }}
            >
              {[
                'equity',
                'trades',
                'fills',
                'signals',
                'replay',
                'exposure',
                'walk_forward',
                'provenance',
              ].map((v) => (
                <option key={v} value={v}>
                  {
                    (
                      {
                        equity: 'Capital',
                        trades: 'Tranzacții',
                        fills: 'Execuții simulate',
                        signals: 'Semnale',
                        replay: 'Firul deciziilor',
                        exposure: 'Expunere',
                        walk_forward: 'Ferestre de evaluare',
                        provenance: 'De unde provin datele',
                      } as Record<string, string>
                    )[v]
                  }
                </option>
              ))}
            </select>
          </label>
          <button
            className="secondary-button"
            onClick={() =>
              void api(
                section === 'provenance'
                  ? `/research/experiments/${selected}/provenance`
                  : `/research/experiments/${selected}/results?section=${section}&trial=${trial}&offset=${offset}&limit=100`,
              )
                .then(setDetails)
                .catch(fail)
            }
          >
            Încarcă analiza
          </button>
          <button
            className="secondary-button"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - 100))}
          >
            Pagina anterioară
          </button>
          <button
            className="secondary-button"
            disabled={
              typeof object(details).total !== 'number' ||
              offset + 100 >= Number(object(details).total)
            }
            onClick={() => setOffset(offset + 100)}
          >
            Pagina următoare
          </button>
          <button
            className="secondary-button"
            onClick={() =>
              void api(`/research/experiments/${selected}/provenance`).then(setDetails).catch(fail)
            }
          >
            Proveniență și număr total de încercări
          </button>
          <StoredRecords value={details} />
          <AdvancedStatistics session={session} experimentId={selected} trial={trial} />
          <Link href="/rezultate/compara">Compară două teste</Link> ·{' '}
          <Link href="/testeaza/nou">Analizează o variantă nouă</Link>
        </section>
      )}
      {route.section === 'compare' && (
        <form
          aria-label="Compară experimente"
          className="panel"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            setError('');
            setComparison(null);
            void api(`/research/experiments/${value(f, 'left')}/compare/${value(f, 'right')}`)
              .then(async (comparison) => {
                setComparison(comparison);
                const values = await Promise.allSettled([
                  api(`/research/experiments/${value(f, 'left')}/provenance`),
                  api(`/research/experiments/${value(f, 'right')}/provenance`),
                ]);
                setComparisonContext({
                  left: values[0].status === 'fulfilled' ? values[0].value : null,
                  right: values[1].status === 'fulfilled' ? values[1].value : null,
                });
              })
              .catch((e) => {
                if (e instanceof ApiError && e.status === 409)
                  setError(
                    'Aceste teste nu au condițiile necesare pentru o comparație directă. Verifică datele, perioada, costurile, riscul și versiunea software. Nu forțăm compararea.',
                  );
                else fail(e);
              });
          }}
        >
          <h2>Compară două teste</h2>
          <p>
            Condițiile trebuie să corespundă conform serverului. Alegerea din multe încercări nu
            elimină riscul selecției.
          </p>
          {['left', 'right'].map((name) => (
            <label key={name}>
              {name === 'left' ? 'Experiment A' : 'Experiment B'}
              <select
                aria-label={name === 'left' ? 'Experiment A' : 'Experiment B'}
                name={name}
                required
              >
                <option value="">Alege…</option>
                {jobs
                  .filter((j) => j.job.state === 'SUCCEEDED')
                  .map((j) => (
                    <option value={j.id} key={j.id}>
                      {j.name} · {j.id}
                    </option>
                  ))}
              </select>
            </label>
          ))}
          <button>Compară rezultate stocate</button>
          {comparison !== null && (
            <>
              <div className="overview-columns">
                <ResultSummary
                  result={object(comparison).left}
                  provenance={comparisonContext.left}
                />
                <ResultSummary
                  result={object(comparison).right}
                  provenance={comparisonContext.right}
                />
              </div>
              <Evidence value={comparison} />
            </>
          )}
        </form>
      )}
      {showFinal && session.user.role === 'OWNER' && (
        <FinalEvaluation
          session={session}
          accounts={accounts}
          datasets={datasets}
          seals={seals}
          jobs={jobs}
          account={account}
          dataset={dataset}
          setAccount={(id) => {
            setAccount(id);
            onAccountChange?.(id);
          }}
          setDataset={setDataset}
          onChanged={load}
        />
      )}
      {showFinal && session.user.role !== 'OWNER' && (
        <p>
          Doar proprietarul cu MFA recent poate autoriza evaluarea finală. Nu afișăm conținutul
          perioadei protejate.
        </p>
      )}
    </section>
  );
}
