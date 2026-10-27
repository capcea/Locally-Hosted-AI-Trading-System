import { useCallback, useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { api, ApiError } from './management-api';
import type { RecordItem, RecordPage, Session } from './management-api';
import type { components } from './generated/api';

type Status = components['schemas']['AccountStatus'];
type Limits = components['schemas']['Limits-Output'];
type Policy = components['schemas']['PolicyView'];
type Profile = components['schemas']['ProfileView'];
type Run = components['schemas']['RunView'];
type RunSummary = components['schemas']['RunSummary'];
type Decision = components['schemas']['Decision'];
type Context = components['schemas']['ContextInput'];
type History = { id: string; key: string; timestamp: string; result: Decision };
type Reservation = {
  order_id: string;
  amount: string;
  margin: string;
  state: string;
  group: string;
};
const get = (data: FormData, name: string) => String(data.get(name) ?? '');
const integer = (data: FormData, name: string) => Number(get(data, name));
const defaults: { key: keyof Limits; label: string; value: string }[] = [
  { key: 'per_trade_pct', label: 'Risc pe tranzacție (%)', value: '0.25' },
  { key: 'daily_loss_pct', label: 'Pierdere zilnică internă (%)', value: '1' },
  { key: 'total_loss_pct', label: 'Drawdown total intern (%)', value: '3' },
  { key: 'aggregate_risk_pct', label: 'Risc agregat deschis și în așteptare (%)', value: '1' },
  { key: 'correlated_risk_pct', label: 'Risc pe grup corelat (%)', value: '0.5' },
  { key: 'headroom_buffer_pct', label: 'Buffer minim de siguranță (%)', value: '0.1' },
  { key: 'max_positions', label: 'Poziții și ordine simultane', value: '3' },
  { key: 'max_spread_ticks', label: 'Spread maxim în ticks', value: '20' },
  { key: 'max_slippage_ticks', label: 'Buffer slippage în ticks', value: '2' },
  { key: 'max_quote_age_seconds', label: 'Vechime maximă cotație (secunde)', value: '30' },
  { key: 'warning_utilization_pct', label: 'Prag avertizare utilizare (%)', value: '80' },
  { key: 'warning_risk_multiplier', label: 'Multiplicator risc la avertizare', value: '0.5' },
];
function Field({
  name,
  label,
  value = '',
  children,
  required = true,
}: {
  name: string;
  label: string;
  value?: string;
  children?: ReactNode;
  required?: boolean;
}) {
  return (
    <label className="management-field">
      <span>{label}</span>
      {children ?? (
        <input name={name} aria-label={label} defaultValue={value} required={required} />
      )}
    </label>
  );
}
function Choice({ name, label, values }: { name: string; label: string; values: string[] }) {
  return (
    <Field name={name} label={label}>
      <select name={name} aria-label={label}>
        {values.map((v) => (
          <option key={v}>{v}</option>
        ))}
      </select>
    </Field>
  );
}
function Ack({ name, children }: { name: string; children: ReactNode }) {
  return (
    <label className="management-check">
      <input name={name} type="checkbox" required />
      {children}
    </label>
  );
}
function Flag({
  name,
  label,
  checked = false,
}: {
  name: string;
  label: string;
  checked?: boolean;
}) {
  return (
    <label className="management-check">
      <input name={name} type="checkbox" defaultChecked={checked} />
      {label}
    </label>
  );
}
export default function RiskCenter({
  session,
  onExpired,
}: {
  session: Session;
  onExpired: () => void;
}) {
  const [records, setRecords] = useState<Record<string, RecordItem[]>>({});
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [accountId, setAccountId] = useState('');
  const [runId, setRunId] = useState('');
  const [run, setRun] = useState<Run | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [decisions, setDecisions] = useState<History[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [context, setContext] = useState<Context | null>(null);
  const [result, setResult] = useState<Decision | null>(null);
  const [scope, setScope] = useState('ACCOUNT');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(0);
  const owner = session.user.role === 'OWNER';
  const fail = useCallback(
    (value: unknown) => {
      setError(value instanceof Error ? value.message : 'Operațiune refuzată.');
      if (value instanceof ApiError && value.status === 401) onExpired();
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    const kinds = [
      'accounts',
      'strategies',
      'instruments',
      'firms',
      'programs',
      'policies',
      'incidents',
    ];
    const pages = await Promise.all(
      kinds.map((kind) => api<RecordPage>(`/records/${kind}?limit=100`)),
    );
    setRecords(Object.fromEntries(kinds.map((kind, index) => [kind, pages[index].items])));
    setRuns(await api<RunSummary[]>('/execution/simulations?limit=50'));
  }, []);
  const refresh = useCallback(async () => {
    if (!accountId) return;
    const base = `/risk/accounts/${accountId}`;
    const [s, p, policies, d, r] = await Promise.all([
      api<Status>(base + '/status'),
      api<Profile[]>(base + '/profiles'),
      api<Policy[]>(base + '/policies'),
      api<History[]>(base + `/decisions?offset=${page * 20}&limit=20`),
      api<Reservation[]>(base + '/reservations?limit=100'),
    ]);
    setStatus(s);
    setProfiles(p);
    setPolicies(policies);
    setDecisions(d);
    setReservations(r);
  }, [accountId, page]);
  useEffect(() => {
    void load().catch(fail);
  }, [load, fail]);
  useEffect(() => {
    setStatus(null);
    setPolicies([]);
    setProfiles([]);
    setDecisions([]);
    setReservations([]);
    void refresh().catch(fail);
    const timer = setInterval(() => {
      void refresh().catch(fail);
    }, 10000);
    return () => clearInterval(timer);
  }, [refresh, fail]);
  useEffect(() => {
    setRun(null);
    setContext(null);
    if (!runId) return;
    let current = true;
    void Promise.all([
      api<Run>(`/execution/simulations/${runId}`),
      api<{ context: Context }[]>(`/risk/runs/${runId}/contexts`),
    ])
      .then(([r, c]) => {
        if (current) {
          setRun(r);
          setContext(c[0]?.context ?? null);
        }
      })
      .catch(fail);
    return () => {
      current = false;
    };
  }, [runId, fail]);
  const post = <T,>(path: string, body: unknown) =>
    api<T>(path, {
      method: 'POST',
      body,
      csrf: session.csrf_token,
    });
  const submit =
    (work: (data: FormData) => Promise<void>) => async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setBusy(true);
      setError('');
      setNotice('');
      try {
        await work(new FormData(event.currentTarget));
        await refresh();
        await load();
      } catch (value) {
        fail(value);
      } finally {
        setBusy(false);
      }
    };
  const account = records.accounts?.find((a) => a.id === accountId);
  const currency = account?.data.kind === 'accounts' ? account.data.currency : 'USD';
  const prop = account?.data.kind === 'accounts' && Boolean(account.data.program_id);
  const scopeKinds: Record<string, string> = {
    STRATEGY: 'strategies',
    INSTRUMENT: 'instruments',
    FIRM: 'firms',
    PROGRAM_PHASE: 'programs',
  };
  const scopeKind = scopeKinds[scope];
  const scoped = records[scopeKind ?? ''] ?? [];
  const currentRuns = runs.filter((r) => r.account_id === accountId);
  return (
    <section className="panel management-panel risk-center" aria-label="Centru de risc">
      <h2>Centru de risc — SIMULATED</h2>
      <p>
        Calcule deterministe pe valori sintetice. Limitele de referință sunt interne, editabile și
        nu reprezintă reguli oficiale ale firmelor. Nicio decizie nu permite ordine demo sau LIVE.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <Field name="account" label="Cont pentru controlul riscului">
        <select
          aria-label="Cont pentru controlul riscului"
          value={accountId}
          onChange={(e) => {
            setAccountId(e.target.value);
            setRunId('');
            setResult(null);
            setPage(0);
          }}
        >
          <option value="">Alege contul…</option>
          {records.accounts?.map((a) => (
            <option value={a.id} key={a.id}>
              {a.data.name}
            </option>
          ))}
        </select>
      </Field>
      {accountId && (
        <>
          {status && (
            <section aria-label="Stare risc cont" className="management-card">
              <h3>
                {status.manual_stop || status.automatic_stop
                  ? 'INTRĂRI BLOCATE'
                  : 'Verificare obligatorie la fiecare ordin'}
              </h3>
              <p>
                {status.currency} · SIMULATED · {status.reasons.join(', ') || 'Nicio oprire activă'}
              </p>
              <dl className="risk-metrics">
                {Object.entries({
                  'Sold sintetic': status.values?.balance,
                  'Equity sintetic': status.values?.equity,
                  'P&L realizat': status.values?.realized_pnl,
                  'P&L flotant': status.values?.unrealized_pnl,
                  Comisioane: status.values?.commissions,
                  'Finanțare modelată': status.values?.funding,
                  'Risc poziții': status.values?.open_risk,
                  'Risc ordine în așteptare': status.values?.pending_risk,
                  'Rezervări (pot include riscul deja afișat)': status.values?.reserved_risk,
                  'Marjă modelată': status.values?.margin_used,
                  'Headroom zilnic': status.daily_headroom,
                  'Headroom total': status.total_headroom,
                }).map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value == null ? 'NECUNOSCUT' : String(value)}</dd>
                  </div>
                ))}
              </dl>
              <p>
                Ceas simulare: {status.clock ?? 'neinițializat'} · Ultima verificare monitor:{' '}
                {status.monitor_at ?? 'absentă'}
              </p>
              <details>
                <summary>Expunere corelată și integritatea registrului</summary>
                <pre className="market-json">
                  {JSON.stringify(
                    {
                      groups: status.values?.groups,
                      ledger_sequence: status.ledger_sequence,
                      ledger_digest: status.ledger_digest,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </section>
          )}
          {owner && (
            <form
              className="management-form"
              aria-label="Urgență risc"
              onSubmit={submit(async (data) => {
                if (!status) throw new Error('Reîncarcă starea contului.');
                if (get(data, 'action') === 'MONITOR') {
                  await post(`/risk/accounts/${accountId}/monitor`, {});
                  setNotice(
                    'Monitorul a verificat datele persistente; verifică motivele de refuz.',
                  );
                } else {
                  const result = await post<{
                    completed: boolean;
                    reasons?: string[];
                    remaining_positions: number;
                  }>(`/risk/accounts/${accountId}/emergency`, {
                    key: crypto.randomUUID(),
                    action: get(data, 'action'),
                    expected_revision: status.revision,
                    acknowledged_simulated_only: true,
                  });
                  setNotice(
                    result.completed
                      ? 'Operațiune persistentă confirmată. Ordinele externe rămân interzise.'
                      : `Operațiune incompletă: ${(result.reasons ?? []).join(', ')}; poziții rămase: ${result.remaining_positions}`,
                  );
                }
              })}
            >
              <h3>Monitor și comenzi de urgență</h3>
              <Choice
                name="action"
                label="Acțiune de siguranță"
                values={['STOP_NEW_ENTRIES', 'MONITOR', 'CLEAR_STOP', 'FLATTEN']}
              />
              <p>
                STOP blochează intrările și persistă la restart. CLEAR necesită date valide și MFA
                recent. FLATTEN încearcă doar închiderea pozițiilor simulate folosind cotațiile și
                lichiditatea disponibile.
              </p>
              <Ack name="emergency_ack">
                Confirm acțiunea exclusiv simulată; nu închid poziții reale.
              </Ack>
              <button className="secondary-button" disabled={busy || !status}>
                Aplică acțiunea de siguranță
              </button>
            </form>
          )}
          {owner && (
            <details open={!profiles.length}>
              <summary>Configurare profil și limite</summary>
              <form
                className="management-form"
                aria-label="Profil risc independent"
                onSubmit={submit(async (data) => {
                  const values = Object.fromEntries(
                    defaults.map(({ key }) => [
                      key,
                      ['max_positions', 'max_slippage_ticks', 'max_quote_age_seconds'].includes(key)
                        ? integer(data, key)
                        : get(data, key),
                    ]),
                  );
                  await post(`/risk/accounts/${accountId}/profiles`, {
                    name: get(data, 'name'),
                    scope,
                    reference_id: get(data, 'reference') || null,
                    asset_class: get(data, 'asset') || null,
                    limits: { ...values, requires_economic_calendar: data.has('profile_news') },
                    acknowledged_internal_defaults: true,
                  });
                  setNotice(
                    'Versiune de profil salvată. Intrările rămân oprite până la revizuirea explicită.',
                  );
                })}
              >
                <Field
                  name="name"
                  label="Denumire profil de risc"
                  value="Profil intern conservator"
                />
                <Field name="scope" label="Domeniu profil">
                  <select
                    name="scope"
                    aria-label="Domeniu profil"
                    value={scope}
                    onChange={(e) => setScope(e.target.value)}
                  >
                    {[
                      'ACCOUNT',
                      'STRATEGY',
                      'INSTRUMENT',
                      'ASSET_CLASS',
                      'FIRM',
                      'PROGRAM_PHASE',
                    ].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </Field>
                {scopeKind && (
                  <Field name="reference" label="Înregistrare pentru domeniul profilului">
                    <select
                      name="reference"
                      aria-label="Înregistrare pentru domeniul profilului"
                      required
                    >
                      <option value="">Alege…</option>
                      {scoped.map((r) => (
                        <option value={r.id} key={r.id}>
                          {r.data.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                )}
                {scope === 'ASSET_CLASS' && (
                  <Choice
                    name="asset"
                    label="Clasă de active pentru profil"
                    values={['FOREX', 'METAL', 'INDEX', 'CRYPTO']}
                  />
                )}
                {defaults.map((f) => (
                  <Field name={f.key} label={f.label} value={f.value} key={f.key} />
                ))}
                <Flag name="profile_news" label="Strategia necesită calendar economic actualizat" />
                <Ack name="profile_ack">
                  Confirm limite interne pentru simulare; nu reprezintă permisiuni de
                  tranzacționare.
                </Ack>
                <button className="secondary-button" disabled={busy}>
                  Salvează versiunea profilului
                </button>
              </form>
            </details>
          )}
          <details>
            <summary>Versiuni de profil ({profiles.length})</summary>
            <pre className="market-json" aria-label="Profiluri de risc persistente">
              {JSON.stringify(profiles, null, 2)}
            </pre>
          </details>
          {owner && (
            <details open={!policies.length}>
              <summary>Politică explicită pentru contul {prop ? 'prop' : 'personal'}</summary>
              <form
                className="management-form"
                aria-label="Politică risc verificabilă"
                onSubmit={submit(async (data) => {
                  const linked = records.policies?.find((p) => p.id === get(data, 'firm_policy'));
                  const external = linked?.data.kind === 'policies' ? linked.data : null;
                  const terms = {
                    currency,
                    timezone: get(data, 'zone'),
                    reset_minute: integer(data, 'reset'),
                    reset_fold: get(data, 'fold'),
                    daily_loss_pct: get(data, 'policy_daily'),
                    total_loss_pct: get(data, 'policy_total'),
                    daily_reference: get(data, 'daily_reference'),
                    daily_amount_basis: get(data, 'daily_basis'),
                    total_mode: get(data, 'total_mode'),
                    trailing_amount_basis: get(data, 'trailing_basis'),
                    include_floating: data.has('floating'),
                    include_fees: true,
                    allow_overnight: data.has('overnight'),
                    allow_weekend: data.has('weekend'),
                    automation_permitted: data.has('automation'),
                    max_position_seconds: integer(data, 'duration'),
                    permitted_instruments: get(data, 'symbols')
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                    prohibited_styles: get(data, 'styles')
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                    news_required: data.has('news'),
                    news_scope: get(data, 'news_scope'),
                    news_before_seconds: integer(data, 'news_before'),
                    news_after_seconds: integer(data, 'news_after'),
                  };
                  const encoded = new TextEncoder().encode(JSON.stringify(terms));
                  const internalDigest = [
                    ...new Uint8Array(await crypto.subtle.digest('SHA-256', encoded)),
                  ]
                    .map((b) => b.toString(16).padStart(2, '0'))
                    .join('');
                  await post(`/risk/accounts/${accountId}/policies`, {
                    kind: prop ? 'PROP' : 'PERSONAL',
                    firm_policy_id: external ? linked!.id : null,
                    terms,
                    effective_at: get(data, 'effective'),
                    expires_at: get(data, 'expiry'),
                    document_digest: external?.document_digest ?? internalDigest,
                    source_references: external?.source_references ?? [get(data, 'reference')],
                  });
                  setNotice(
                    'Politică nouă NEVERIFICATĂ. Revizuiește regulile și confirmă separat amprenta.',
                  );
                })}
              >
                {prop && (
                  <Field name="firm_policy" label="Politică exactă a programului">
                    <select name="firm_policy" aria-label="Politică exactă a programului" required>
                      <option value="">Alege…</option>
                      {records.policies
                        ?.filter(
                          (p) => p.data.kind === 'policies' && p.data.account_id === accountId,
                        )
                        .map((p) => (
                          <option value={p.id} key={p.id}>
                            {p.data.name}
                          </option>
                        ))}
                    </select>
                  </Field>
                )}
                <Field name="zone" label="Fus orar politică" value="UTC" />
                <Field name="reset" label="Minut resetare în ziua locală" value="0" />
                <Choice
                  name="fold"
                  label="Resetare la oră ambiguă DST"
                  values={['EARLIER', 'LATER']}
                />
                <Field
                  name="effective"
                  label="Politică valabilă de la UTC"
                  value="2020-01-01T00:00:00Z"
                />
                <Field name="expiry" label="Politică expiră la UTC" value="2030-01-01T00:00:00Z" />
                <Field name="policy_daily" label="Limită zilnică politică (%)" value="1" />
                <Field name="policy_total" label="Limită totală politică (%)" value="3" />
                <Choice
                  name="daily_reference"
                  label="Referință zilnică"
                  values={['BALANCE', 'EQUITY', 'MAX_BALANCE_EQUITY', 'INITIAL']}
                />
                <Choice
                  name="daily_basis"
                  label="Bază procent pierdere zilnică"
                  values={['INITIAL', 'DAILY_REFERENCE']}
                />
                <Choice
                  name="total_mode"
                  label="Mod drawdown total"
                  values={['STATIC', 'TRAILING_BALANCE', 'TRAILING_EQUITY']}
                />
                <Choice
                  name="trailing_basis"
                  label="Bază cuantum drawdown"
                  values={['INITIAL', 'HIGH_WATER']}
                />
                <Flag name="floating" label="Include P&L flotant în politica declarată" checked />
                <Flag name="overnight" label="Permite deținere peste noapte" />
                <Flag name="weekend" label="Permite expunere în weekend" />
                <Flag name="automation" label="Automatizare permisă explicit de politică" />
                <Field name="duration" label="Durată maximă poziție (secunde)" value="3600" />
                <Field
                  name="symbols"
                  label="Instrumente permise, separate prin virgulă"
                  value="EURUSD"
                />
                <Field
                  name="styles"
                  label="Stiluri interzise, separate prin virgulă"
                  required={false}
                />
                <Flag name="news" label="Necesită calendar economic actualizat" />
                <Choice
                  name="news_scope"
                  label="Domeniul restricției de știri"
                  values={['NEW_ENTRIES', 'EXPOSURE']}
                />
                <Field name="news_before" label="Blackout înainte știri (secunde)" value="300" />
                <Field name="news_after" label="Blackout după știri (secunde)" value="300" />
                {!prop && (
                  <Field
                    name="reference"
                    label="Proveniență politică internă"
                    value="owner://internal-simulated-policy"
                  />
                )}
                <Ack name="policy_ack">
                  Confirm regulile și perioada declarate. Politica internă nu este o regulă oficială
                  de firmă.
                </Ack>
                <button className="secondary-button" disabled={busy}>
                  Salvează politica neverificată
                </button>
              </form>
            </details>
          )}
          <section aria-label="Politici de risc">
            {policies.map((p) => (
              <article className="management-card" key={p.id}>
                <h3>
                  Politică v{p.version} · {p.status}
                </h3>
                <p>
                  {p.effective_at} — {p.expires_at}
                </p>
                <details>
                  <summary>Reguli, proveniență și amprentă</summary>
                  <pre className="market-json">{JSON.stringify(p, null, 2)}</pre>
                </details>
                {owner && (
                  <form
                    className="management-form"
                    aria-label={`Confirmare politică v${p.version}`}
                    onSubmit={submit(async (data) => {
                      await post(`/risk/policies/${p.id}/attest`, {
                        document_digest: p.document_digest,
                        action: get(data, 'action'),
                        acknowledged_exact_program_and_effective_dates: true,
                      });
                      setNotice(
                        'Atestare înregistrată. Verifică monitorul și deblochează explicit intrările când datele sunt valide.',
                      );
                    })}
                  >
                    <Choice
                      name="action"
                      label={`Acțiune politică v${p.version}`}
                      values={['VERIFY', 'REVOKE']}
                    />
                    <Ack name="attest_ack">
                      Am revizuit exact programul, regulile, proveniența, perioada și amprenta
                      afișată.
                    </Ack>
                    <button className="secondary-button" disabled={busy}>
                      Înregistrează atestarea politicii v{p.version}
                    </button>
                  </form>
                )}
              </article>
            ))}
          </section>
          <Field name="run" label="Scenariu pentru evaluarea riscului">
            <select
              aria-label="Scenariu pentru evaluarea riscului"
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
            >
              <option value="">Alege…</option>
              {currentRuns.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </Field>
          {run && owner && (
            <details open={!context}>
              <summary>Specificații monetare și dovezi sintetice</summary>
              <p>
                Contractul scenariului rămâne fix. Tick: {run.state.spec.tick_size}; contract:{' '}
                {run.state.spec.contract_size}; profit: {run.state.spec.profit_currency}. Nu deducem
                valori de pip sau reguli de marjă.
              </p>
              <form
                key={run.id}
                className="management-form"
                aria-label="Context monetar simulat"
                onSubmit={submit(async (data) => {
                  const file = data.get('evidence');
                  let evidence: { fx?: unknown[]; calendar?: unknown } = {};
                  if (file instanceof File && file.size) {
                    if (file.size > 65536) throw new Error('Dovezile depășesc 64 KiB.');
                    evidence = JSON.parse(await file.text());
                  }
                  const body = {
                    financial: {
                      payoff: get(data, 'payoff'),
                      base_currency: get(data, 'base') || null,
                      quote_currency: get(data, 'profit'),
                      tick_value_profit_currency: get(data, 'tick_value'),
                      margin_per_unit: get(data, 'margin') || null,
                      funding_buffer_per_unit: get(data, 'funding'),
                      correlation_group: get(data, 'group'),
                      execution_style: get(data, 'style'),
                      automated: data.has('automated'),
                      fx: evidence.fx ?? [],
                      source_reference: get(data, 'source'),
                      verified_at: get(data, 'observed'),
                      valid_until: get(data, 'valid'),
                      source: 'SIMULATED',
                    },
                    calendar: evidence.calendar ?? null,
                    owner_acknowledged_synthetic_assumptions: true,
                  };
                  await post(`/risk/runs/${run.id}/contexts`, body);
                  setContext(body as Context);
                  setNotice('Context salvat. Intrările rămân oprite pentru revizuire.');
                })}
              >
                <Choice
                  name="payoff"
                  label="Convenție payoff"
                  values={['LINEAR_CONTRACT', 'LINEAR_TICK', 'INVERSE', 'UNVERIFIED']}
                />
                <Field name="base" label="Monedă de bază" value="EUR" />
                <Field
                  name="profit"
                  label="Monedă cotație și profit"
                  value={run.state.spec.profit_currency}
                />
                <Field name="tick_value" label="Valoare tick în moneda profitului pe unitate" />
                <Field name="margin" label="Marjă sintetică pe unitate în moneda contului" />
                <Field
                  name="funding"
                  label="Buffer finanțare pe unitate în moneda contului"
                  value="0"
                />
                <Field name="group" label="Grup de corelație" value="USD_FOREX" />
                <Field name="style" label="Stil de execuție declarat" value="MANUAL" />
                <Flag name="automated" label="Propunere automatizată" />
                <Field
                  name="source"
                  label="Sursa ipotezelor monetare"
                  value="Ipoteze sintetice declarate explicit de proprietar"
                />
                <Field
                  name="observed"
                  label="Specificații observate la UTC"
                  value={run.state.clock}
                />
                <Field
                  name="valid"
                  label="Specificații monetare valabile până UTC"
                  value={run.state.spec.valid_until}
                />
                <Field
                  name="evidence"
                  label="Importă dovezi FX și calendar sintetice (JSON)"
                  required={false}
                >
                  <input
                    name="evidence"
                    aria-label="Importă dovezi FX și calendar sintetice (JSON)"
                    type="file"
                    accept=".json,application/json"
                  />
                </Field>
                <p>
                  Conversiile și calendarul lipsă nu sunt inventate. Produsele inverse sau
                  neverificate sunt refuzate. Dovezile importate sunt date, nu cod executabil.
                </p>
                <Ack name="context_ack">
                  Confirm explicit ipotezele sintetice și proveniența lor.
                </Ack>
                <button className="secondary-button" disabled={busy}>
                  Salvează contextul monetar
                </button>
              </form>
            </details>
          )}
          {run && session.user.role !== 'VIEWER' && (
            <form
              className="management-form"
              aria-label="Calculator risc ipotetic"
              onSubmit={submit(async (data) => {
                setResult(
                  await post<Decision>('/risk/what-if', {
                    run_id: run.id,
                    at: get(data, 'at'),
                    auto_size: data.has('auto'),
                    order: {
                      side: get(data, 'side'),
                      order_type: get(data, 'type'),
                      volume: get(data, 'volume'),
                      price: get(data, 'price') || null,
                      stop_loss: get(data, 'sl'),
                      take_profit: get(data, 'tp'),
                      strategy_version_id: null,
                    },
                  }),
                );
              })}
            >
              <h3>Calculator ipotetic — nu transmite ordine</h3>
              <Field name="at" label="Moment evaluare UTC" value={run.state.clock} />
              <Choice name="side" label="Sens pentru calculator" values={['BUY', 'SELL']} />
              <Choice
                name="type"
                label="Tip ordin pentru calculator"
                values={['MARKET', 'LIMIT', 'STOP']}
              />
              <Field name="volume" label="Volum propus pentru calculator" value="0.1" />
              <Field name="price" label="Preț pending pentru calculator" required={false} />
              <Field name="sl" label="Stop-loss pentru calculator" />
              <Field name="tp" label="Take-profit pentru calculator" />
              <Flag name="auto" label="Calculează volumul maxim legal fără transmitere" />
              <button className="secondary-button" disabled={busy}>
                Calculează riscul ipotetic
              </button>
            </form>
          )}
          {result && (
            <section aria-label="Rezultat calculator risc">
              <h3>{result.decision} · SIMULATED</h3>
              <p>{result.reasons.join(', ')}</p>
              <pre className="market-json">{JSON.stringify(result, null, 2)}</pre>
            </section>
          )}
          <section aria-label="Istoric decizii risc">
            <h3>Decizii și refuzuri persistente</h3>
            {decisions.map((d) => (
              <article key={d.id} className="management-card">
                <h4>
                  {d.result.decision} · {d.key}
                </h4>
                <p>{d.result.reasons.join(', ')}</p>
                <p>
                  {d.timestamp} · Risc estimat {d.result.estimated_risk}
                </p>
                <details>
                  <summary>Calcul și dovezi</summary>
                  <pre className="market-json">{JSON.stringify(d.result, null, 2)}</pre>
                </details>
              </article>
            ))}
            <button
              className="secondary-button"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              Decizii anterioare
            </button>
            <button
              className="secondary-button"
              disabled={decisions.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              Decizii mai vechi
            </button>
          </section>
          <section aria-label="Rezervări active">
            <h3>Rezervări durabile</h3>
            <pre className="market-json">{JSON.stringify(reservations, null, 2)}</pre>
          </section>
          <section aria-label="Incidente risc">
            <h3>Incidente persistente</h3>
            {records.incidents
              ?.filter((i) => i.data.kind === 'incidents' && i.data.account_id === accountId)
              .map((i) => (
                <p key={i.id}>
                  {i.data.name} · {i.data.kind === 'incidents' ? i.data.status : ''}
                </p>
              ))}
          </section>
        </>
      )}
    </section>
  );
}
