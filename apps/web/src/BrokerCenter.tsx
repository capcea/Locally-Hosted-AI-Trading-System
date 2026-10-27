import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError } from './management-api';
import type { RecordItem, RecordPage, Session } from './management-api';
import type { components } from './generated/api';

type Run = components['schemas']['RunView'];
type RunSummary = components['schemas']['RunSummary'];
type Connection = components['schemas']['ConnectionView'];
type Command = components['schemas']['Command'];
type Dataset = components['schemas']['DatasetView'];
type JournalEvent = { sequence: number; event: { kind: string; payload: unknown }; digest: string };

function text(data: FormData, name: string) {
  return String(data.get(name) ?? '');
}
function nullable(data: FormData, name: string) {
  return text(data, name) || null;
}
function Input({
  name,
  label,
  initial = '',
  required = true,
  type = 'text',
}: {
  name: string;
  label: string;
  initial?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="management-field">
      <span>{label}</span>
      <input
        aria-label={label}
        name={name}
        defaultValue={initial}
        required={required}
        type={type}
      />
    </label>
  );
}
function Select({
  name,
  label,
  values,
}: {
  name: string;
  label: string;
  values: { id: string; name: string }[];
}) {
  return (
    <label className="management-field">
      <span>{label}</span>
      <select aria-label={label} name={name} required>
        <option value="">Alege…</option>
        {values.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
    </label>
  );
}
const options = (values: string[]) => values.map((id) => ({ id, name: id }));

export default function BrokerCenter({
  session,
  onExpired,
}: {
  session: Session;
  onExpired: () => void;
}) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [instruments, setInstruments] = useState<RecordItem[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<Run | null>(null);
  const [events, setEvents] = useState<JournalEvent[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState('SIMULATOR');
  const [lastCommand, setLastCommand] = useState<Command | null>(null);
  const [eventPage, setEventPage] = useState(0);
  const canWrite = session.user.role !== 'VIEWER';
  const fail = useCallback(
    (error: unknown) => {
      setError(error instanceof Error ? error.message : 'Operațiune eșuată.');
      if (error instanceof ApiError && error.status === 401) onExpired();
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    const [c, r, a, i, d] = await Promise.all([
      api<Connection[]>('/execution/connections?limit=100'),
      api<RunSummary[]>('/execution/simulations'),
      api<RecordPage>('/records/accounts?limit=100'),
      api<RecordPage>('/records/instruments?limit=100'),
      api<components['schemas']['DatasetPage']>('/market/datasets?limit=100&status=VALID'),
    ]);
    setConnections(c);
    setRuns(r);
    setAccounts(a.items);
    setInstruments(i.items);
    setDatasets(d.items);
  }, []);
  useEffect(() => {
    void load().catch(fail);
  }, [load, fail]);
  const inspect = async (id: string, offset = 0) => {
    const [run, journal] = await Promise.all([
      api<Run>(`/execution/simulations/${id}`),
      api<JournalEvent[]>(`/execution/simulations/${id}/events?offset=${offset * 100}&limit=100`),
    ]);
    setSelected(run);
    setEvents(journal);
    setEventPage(offset);
  };
  const action = async (task: () => Promise<void>) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await task();
      await load();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };
  const post = <T,>(path: string, body: unknown) =>
    api<T>(path, { method: 'POST', body, csrf: session.csrf_token });
  const command = async (body: Omit<Command, 'key'> & { key?: string }) => {
    if (!selected) return;
    const full = { ...body, key: body.key ?? crypto.randomUUID() } as Command;
    try {
      await post(`/execution/simulations/${selected.id}/commands`, full);
      setLastCommand(full);
    } finally {
      await inspect(selected.id);
    }
  };
  const submit =
    (task: (fields: FormData) => Promise<void>) => (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      void action(() => task(data));
    };
  const names = (records: RecordItem[]) =>
    records.map((item) => ({ id: item.id, name: item.data.name }));
  return (
    <section className="panel management-panel broker-center">
      <h2>Centrul brokerilor și simulatorului</h2>
      <p>
        Execuție externă: DENY_ALL. DEMO_EXECUTION și LIVE sunt indisponibile. Numai simulatorul
        intern produce ordine și rezultate SIMULATED. Orice intrare necesită profil, politică
        verificată, context monetar și monitor de risc actualizat. Configurează-le în „Centru de
        risc”.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <button className="text-button" disabled={busy} onClick={() => void action(load)}>
        Actualizează brokerii
      </button>
      <h3>Conexiuni și conturi observate</h3>
      {!connections.length && (
        <p>Nicio conexiune verificată. Nu sunt presupuse solduri, cotații sau capabilități.</p>
      )}
      <div className="management-cards">
        {connections.map((connection) => (
          <article className="management-record" key={connection.id}>
            <h4>{connection.name}</h4>
            <p>
              {connection.provider} · {connection.mode} · {connection.status}
            </p>
            <p>
              Ultima sincronizare: {connection.last_synced_at ?? 'neobservată'} · ordine externe
              dezactivate
            </p>
            {connection.snapshot && (
              <>
                <strong>
                  Sursă: {connection.snapshot.source} · {connection.snapshot.observed_at}
                </strong>
                <p>
                  Latență snapshot: {connection.snapshot.latency_ms ?? 'necunoscută'} ms ·
                  reconectări: {connection.snapshot.reconnect_attempt}
                </p>
                <p>
                  {connection.snapshot.source === 'BROKER_OBSERVED'
                    ? 'Sold raportat de broker'
                    : 'Sold de simulare / fixture'}
                  : {connection.snapshot.balance ?? 'necunoscut'} {connection.snapshot.currency}
                </p>
                <p>
                  Cont extern: {connection.snapshot.account_id} ·{' '}
                  {connection.snapshot.account_mode ?? 'mod necunoscut'} · autorizare{' '}
                  {connection.snapshot.authorization}
                </p>
                <details>
                  <summary>Simboluri, cotații și restricții</summary>
                  <pre className="market-json">
                    {JSON.stringify(
                      {
                        symbols: connection.snapshot.symbols,
                        quotes: connection.snapshot.quotes,
                        restrictions: connection.snapshot.restrictions,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
                <details>
                  <summary>Ordine și poziții raportate</summary>
                  <pre className="market-json">
                    {JSON.stringify(
                      {
                        orders: connection.snapshot.orders,
                        positions: connection.snapshot.positions,
                        history: connection.snapshot.history,
                        history_complete: connection.snapshot.history_complete,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </>
            )}
            {session.user.role === 'OWNER' && connection.mode === 'DEMO_READ_ONLY' && (
              <form
                aria-label={`Observație semnată ${connection.name}`}
                onSubmit={submit(async (data) => {
                  const file = data.get('packet');
                  if (!(file instanceof File) || !file.size || file.size > 1048576)
                    throw new Error('Fișier semnat de maximum 1 MiB necesar.');
                  await post(
                    `/execution/connections/${connection.id}/observations`,
                    JSON.parse(await file.text()),
                  );
                  setNotice(
                    'Observație înregistrată; semnătura nu acordă permisiunea de tranzacționare.',
                  );
                })}
              >
                <Input
                  name="packet"
                  label="Fișier de observație semnat, fără credențiale"
                  type="file"
                />
                <button className="secondary-button" disabled={busy}>
                  Verifică și sincronizează observația
                </button>
              </form>
            )}
          </article>
        ))}
      </div>
      {session.user.role === 'OWNER' && (
        <form
          className="management-form"
          aria-label="Conexiune broker"
          onSubmit={submit(async (data) => {
            const meta = await post<RecordItem>('/records/brokers', {
              kind: 'brokers',
              name: text(data, 'name'),
              account_id: text(data, 'account'),
              adapter: provider === 'SIMULATOR' ? 'CUSTOM' : provider,
              source: provider === 'SIMULATOR' ? 'SYNTHETIC_TEST_FIXTURE' : 'USER_ENTERED',
            });
            await post('/execution/connections', {
              broker_connection_id: meta.id,
              provider,
              mode: provider === 'SIMULATOR' ? 'SIMULATED' : 'DEMO_READ_ONLY',
              external_account: provider === 'SIMULATOR' ? null : text(data, 'external'),
              server: provider === 'SIMULATOR' ? null : text(data, 'server'),
              public_key: provider === 'SIMULATOR' ? null : text(data, 'public_key'),
            });
            setNotice(
              'Identitate înregistrată. Conexiunea externă rămâne neverificată până la o observație semnată.',
            );
          })}
        >
          <h3>Înregistrează identitatea conexiunii</h3>
          <Input name="name" label="Denumire conexiune" />
          <Select name="account" label="Cont local" values={names(accounts)} />
          <label className="management-field">
            <span>Adaptor broker</span>
            <select
              aria-label="Adaptor broker"
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
            >
              {options(['SIMULATOR', 'MT5', 'CTRADER']).map((item) => (
                <option key={item.id}>{item.id}</option>
              ))}
            </select>
          </label>
          {provider !== 'SIMULATOR' && (
            <>
              <Input name="external" label="Identificator exact al contului demo" />
              <Input
                name="server"
                label="Server demo exact"
                initial={provider === 'CTRADER' ? 'demo.ctraderapi.com' : ''}
              />
              <Input name="public_key" label="Cheie publică Ed25519 a conectorului privat" />
              <p>
                Parolele MT5 și tokenurile OAuth rămân pe serviciul privat. Acest formular nu le
                primește. Schimbarea identității necesită o conexiune nouă și MFA recent.
              </p>
            </>
          )}
          <button className="secondary-button" disabled={busy}>
            Înregistrează conexiunea
          </button>
        </form>
      )}
      <h3>Scenarii de execuție sintetică</h3>
      <div className="management-cards">
        {runs.map((run) => (
          <article className="management-record" key={run.id}>
            <h4>{run.name}</h4>
            <p>
              SIMULATED · {run.symbol} · {run.account_mode}
            </p>
            <p>
              {run.order_count} ordine · {run.fill_count} fill-uri sintetice
            </p>
            <button
              className="text-button"
              onClick={() =>
                void action(async () => {
                  setLastCommand(null);
                  await inspect(run.id);
                })
              }
            >
              Explorează {run.name}
            </button>
          </article>
        ))}
      </div>
      {canWrite && (
        <form
          className="management-form"
          aria-label="Scenariu sintetic"
          onSubmit={submit(async (data) => {
            const connection = connections.find((item) => item.id === text(data, 'connection'));
            const account = accounts.find((item) => item.id === connection?.account_id);
            const instrument = instruments.find((item) => item.id === text(data, 'instrument'));
            if (
              !account ||
              account.data.kind !== 'accounts' ||
              !instrument ||
              instrument.data.kind !== 'instruments'
            )
              throw new Error('Contul și instrumentul trebuie configurate.');
            const start = text(data, 'start'),
              until = text(data, 'until');
            const created = await post<Run>('/execution/simulations', {
              connection_id: text(data, 'connection'),
              instrument_id: instrument.id,
              name: text(data, 'name'),
              start_at: start,
              dataset_id: nullable(data, 'dataset'),
              spec: {
                symbol: text(data, 'symbol'),
                canonical_symbol: instrument.data.symbol,
                asset_class: instrument.data.asset_class,
                tick_size: text(data, 'tick'),
                digits: Number(text(data, 'digits')),
                contract_size: text(data, 'contract'),
                stop_distance: text(data, 'stop_distance'),
                freeze_distance: text(data, 'freeze_distance'),
                min_volume: text(data, 'min'),
                max_volume: text(data, 'max'),
                volume_step: text(data, 'step'),
                profit_currency: account.data.currency,
                order_types: ['MARKET', 'LIMIT', 'STOP'],
                account_mode: text(data, 'mode'),
                oco_supported: data.has('oco'),
                source: 'EXPLICIT_SYNTHETIC_OWNER_ASSUMPTIONS',
                observed_at: start,
                valid_until: until,
                calendar: {
                  timezone: 'UTC',
                  weekdays: [0, 1, 2, 3, 4],
                  holidays: [],
                  opens: 0,
                  closes: 1440,
                  verified_until: until,
                  source: 'EXPLICIT_SYNTHETIC_WEEKDAY_CALENDAR',
                },
              },
              assumptions: {
                assumption_source: text(data, 'assumptions'),
                latency_ms: Number(text(data, 'latency')),
                slippage_ticks: Number(text(data, 'slippage')),
                commission_per_unit: text(data, 'commission'),
                liquidity_per_tick: text(data, 'liquidity'),
                synthetic_initial_balance: text(data, 'balance'),
                account_currency: account.data.currency,
                seed: Number(text(data, 'seed')),
              },
            });
            await inspect(created.id);
          })}
        >
          <h3>Scenariu nou — ipoteze exclusiv sintetice</h3>
          <Input name="name" label="Denumire scenariu" />
          <Select
            name="connection"
            label="Conexiune simulator"
            values={connections
              .filter((item) => item.provider === 'SIMULATOR')
              .map((item) => ({ id: item.id, name: item.name }))}
          />
          <Select name="instrument" label="Instrument scenariu" values={names(instruments)} />
          <Input name="symbol" label="Simbol exact scenariu" initial="EURUSD.test" />
          <Select name="mode" label="Mod de poziții" values={options(['HEDGING', 'NETTING'])} />
          <Input name="start" label="Început virtual UTC" initial="2024-01-02T00:00:00Z" />
          <Input
            name="until"
            label="Specificație și calendar valabile până la UTC"
            initial="2024-02-01T00:00:00Z"
          />
          <Input name="tick" label="Mărime tick declarată" initial="0.0001" />
          <Input name="digits" label="Precizie preț" initial="4" type="number" />
          <Input name="contract" label="Mărime contract declarată" initial="100000" />
          <Input name="stop_distance" label="Distanță minimă stop declarată" initial="0" />
          <Input name="freeze_distance" label="Distanță freeze declarată" initial="0" />
          <Input name="min" label="Volum minim" initial="0.01" />
          <Input name="max" label="Volum maxim" initial="100" />
          <Input name="step" label="Pas volum" initial="0.01" />
          <Input name="balance" label="Sold inițial sintetic" initial="25000" />
          <Input name="commission" label="Comision sintetic per unitate" initial="0" />
          <Input name="liquidity" label="Lichiditate sintetică per tick" initial="1" />
          <Input name="latency" label="Latență modelată (ms)" initial="0" type="number" />
          <Input name="slippage" label="Slippage advers (ticks)" initial="0" type="number" />
          <Input name="seed" label="Seed determinist" initial="7" type="number" />
          <Input
            name="assumptions"
            label="Sursa și justificarea ipotezelor"
            initial="Scenariu sintetic declarat; nu reproduce un broker real"
          />
          <label className="management-check">
            <input name="oco" type="checkbox" /> Activez OCO exclusiv în simulator
          </label>
          <label className="management-field">
            <span>Set de ticks VALID (opțional)</span>
            <select aria-label="Set de ticks VALID (opțional)" name="dataset">
              <option value="">Cotații manuale marcate sintetice</option>
              {datasets
                .filter((d) => d.spec.data_type === 'TICK')
                .map((d) => (
                  <option value={d.id} key={d.id}>
                    {d.symbol} v{d.version} · {d.spec.provenance}
                  </option>
                ))}
            </select>
          </label>
          <p>
            Calendarul acestui formular este o ipoteză sintetică UTC, luni–vineri. Simularea
            necesită aceeași monedă de profit și de cont. Pentru reguli avansate folosește API-ul
            tipizat; nicio specificație nu certifică tranzacționabilitatea reală.
          </p>
          <label className="management-check">
            <input type="checkbox" required /> Confirm explicit ipotezele sintetice și lipsa
            autorității de tranzacționare
          </label>
          <button className="secondary-button" disabled={busy}>
            Creează scenariul sintetic
          </button>
        </form>
      )}
      {selected && (
        <section aria-label="Scenariu selectat">
          <h3>{selected.name} · SIMULATED</h3>
          <p>
            Ceas virtual: {selected.state.clock} · {selected.state.connection} ·{' '}
            {selected.state.incident ?? 'fără incident'}
          </p>
          <p>
            Sold sintetic: {selected.state.cash} {selected.state.model.account_currency} ·
            comisioane {selected.state.fees} · finanțare {selected.state.swap}
          </p>
          <p>
            Sursa prețurilor:{' '}
            {selected.source_binding
              ? JSON.stringify(selected.source_binding)
              : 'Cotații sintetice declarate manual'}
          </p>
          {canWrite && (
            <>
              {!selected.source_binding ? (
                <form
                  className="management-form"
                  aria-label="Tick sintetic"
                  key={`quote-${selected.id}`}
                  onSubmit={submit(async (data) => {
                    const at = text(data, 'at');
                    await command({
                      action: 'TICK',
                      at,
                      quote: {
                        symbol: selected.state.spec.symbol,
                        event_time: at,
                        available_at: at,
                        bid: text(data, 'bid'),
                        ask: text(data, 'ask'),
                        sequence: Number(text(data, 'sequence')),
                      },
                    });
                  })}
                >
                  <h4>Cotație sintetică nouă</h4>
                  <Input
                    key={selected.state.clock}
                    name="at"
                    label="Moment tick UTC"
                    initial={selected.state.clock}
                  />
                  <Input
                    key={selected.state.quote?.sequence ?? -1}
                    name="sequence"
                    label="Secvență tick"
                    initial={String((selected.state.quote?.sequence ?? -1) + 1)}
                    type="number"
                  />
                  <Input name="bid" label="Bid sintetic" initial="1.1000" />
                  <Input name="ask" label="Ask sintetic" initial="1.1002" />
                  <button className="secondary-button" disabled={busy}>
                    Aplică tick sintetic
                  </button>
                </form>
              ) : (
                <form
                  className="management-form"
                  aria-label="Replay ticks validați"
                  onSubmit={submit(async (data) => {
                    await post(`/execution/simulations/${selected.id}/replay`, {
                      key: text(data, 'key'),
                      start: text(data, 'start'),
                      end: text(data, 'end'),
                      decision_at: text(data, 'decision'),
                      limit: 500,
                    });
                    await inspect(selected.id);
                  })}
                >
                  <Input name="key" label="Cheie replay" initial={crypto.randomUUID()} />
                  <Input name="start" label="Început replay UTC" initial={selected.state.clock} />
                  <Input name="end" label="Sfârșit replay UTC" />
                  <Input name="decision" label="Informații disponibile la decizia replay UTC" />
                  <button className="secondary-button" disabled={busy}>
                    Redă ticks din setul verificat
                  </button>
                </form>
              )}
              <form
                className="management-form"
                aria-label="Ordin sintetic"
                key={`order-${selected.id}`}
                onSubmit={submit(async (data) =>
                  command({
                    key: text(data, 'key'),
                    action: 'SUBMIT',
                    at: text(data, 'at'),
                    order: {
                      side: text(data, 'side') as 'BUY' | 'SELL',
                      order_type: text(data, 'type') as 'MARKET' | 'LIMIT' | 'STOP',
                      volume: text(data, 'volume'),
                      price: nullable(data, 'price'),
                      stop_loss: nullable(data, 'sl'),
                      take_profit: nullable(data, 'tp'),
                      expires_at: nullable(data, 'expires'),
                      oco_group: nullable(data, 'oco'),
                    },
                  }),
                )}
              >
                <h4>Ordin exclusiv simulat</h4>
                <Input name="key" label="Cheie idempotentă ordin" initial={crypto.randomUUID()} />
                <Input
                  key={selected.state.clock}
                  name="at"
                  label="Moment comandă UTC"
                  initial={selected.state.clock}
                />
                <Select name="side" label="Sens ordin" values={options(['BUY', 'SELL'])} />
                <Select
                  name="type"
                  label="Tip ordin simulat"
                  values={options(['MARKET', 'LIMIT', 'STOP'])}
                />
                <Input name="volume" label="Volum ordin sintetic" initial="0.10" />
                <Input
                  name="price"
                  label="Preț limită / stop (gol pentru MARKET)"
                  required={false}
                />
                <Input name="sl" label="Stop-loss sintetic obligatoriu" />
                <Input name="tp" label="Take-profit sintetic obligatoriu" />
                <Input name="expires" label="Expirare UTC (opțional)" required={false} />
                <Input name="oco" label="Grup OCO sintetic (opțional)" required={false} />
                <p>
                  Fill-urile apar numai la un tick ulterior eligibil; lichiditatea și latența pot
                  produce execuții parțiale. Prețurile și rezultatele sunt SIMULATED.
                </p>
                <button className="secondary-button" disabled={busy}>
                  Trimite ordin în simulator
                </button>
              </form>
              {lastCommand && (
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => void action(() => command(lastCommand))}
                >
                  Repetă aceeași comandă idempotentă
                </button>
              )}
              <form
                aria-label="Fault sintetic"
                className="management-form"
                onSubmit={submit(async (data) =>
                  command({
                    action: 'FAULT',
                    at: selected.state.clock,
                    fault: text(data, 'fault') as Command['fault'],
                  }),
                )}
              >
                <Select
                  name="fault"
                  label="Defecțiune sintetică următoare"
                  values={options([
                    'NONE',
                    'BEFORE_SUBMIT',
                    'AFTER_SUBMIT',
                    'REJECT_NEXT',
                    'DELAY_ACK',
                  ])}
                />
                <button className="secondary-button" disabled={busy}>
                  Configurează defecțiunea sintetică
                </button>
              </form>
              <button
                className="secondary-button"
                disabled={busy}
                onClick={() =>
                  void action(() => command({ action: 'RECONCILE', at: selected.state.clock }))
                }
              >
                Reconciliază adevărul brokerului sintetic
              </button>
            </>
          )}
          <h4>Ordine simulate și corelații</h4>
          <div className="management-cards">
            {Object.values(selected.state.orders ?? {}).map((order) => (
              <article className="management-record" key={order.id}>
                <h5>
                  {order.request.side} {order.request.order_type} · {order.state}
                </h5>
                <p>
                  {order.idempotency_key} · {order.broker_order_id ?? 'netrimis'}
                </p>
                <p>
                  {order.filled_volume} / {order.request.volume} ·{' '}
                  {order.rejection_reason ?? 'fără refuz'}
                </p>
                {canWrite && ['ACKNOWLEDGED', 'PARTIALLY_FILLED'].includes(order.state) && (
                  <button
                    className="text-button"
                    disabled={busy}
                    onClick={() =>
                      void action(() =>
                        command({
                          action: 'CANCEL',
                          at: selected.state.clock,
                          target_id: order.id,
                        }),
                      )
                    }
                  >
                    Anulează ordinul simulat {order.id}
                  </button>
                )}
              </article>
            ))}
          </div>
          <h4>Poziții sintetice</h4>
          {Object.values(selected.state.positions ?? {})
            .filter((p) => /[1-9]/.test(p.volume.split(/[eE]/)[0]))
            .map((position) => (
              <article className="management-record" key={position.id}>
                <p>
                  {position.side} · {position.volume} · intrare {position.entry_price} · P&amp;L
                  realizat sintetic {position.realized_pnl}
                </p>
                {canWrite && (
                  <>
                    <form
                      className="management-form"
                      aria-label={`Protecție poziție ${position.id}`}
                      onSubmit={submit(async (data) =>
                        command({
                          action: 'MODIFY',
                          at: selected.state.clock,
                          target_id: position.id,
                          stop_loss: nullable(data, 'sl'),
                          take_profit: nullable(data, 'tp'),
                        }),
                      )}
                    >
                      <Input
                        name="sl"
                        label="Stop-loss poziție"
                        initial={position.stop_loss ?? ''}
                        required={false}
                      />
                      <Input
                        name="tp"
                        label="Take-profit poziție"
                        initial={position.take_profit ?? ''}
                        required={false}
                      />
                      <button disabled={busy}>Modifică protecția sintetică</button>
                    </form>
                    <form
                      aria-label={`Închidere poziție ${position.id}`}
                      onSubmit={submit(async (data) =>
                        command({
                          action: 'CLOSE',
                          at: selected.state.clock,
                          target_id: position.id,
                          volume: text(data, 'volume'),
                        }),
                      )}
                    >
                      <Input name="volume" label="Volum de închis" initial={position.volume} />
                      <button disabled={busy}>Închide parțial / total în simulator</button>
                    </form>
                  </>
                )}
              </article>
            ))}
          <h4>Fill-uri sintetice</h4>
          <pre aria-label="Fill-uri sintetice" className="market-json">
            {JSON.stringify(selected.state.fills, null, 2)}
          </pre>
          <h4>Jurnal persistent</h4>
          <p>
            Secvență {selected.sequence} · amprentă {selected.digest}
          </p>
          <pre aria-label="Evenimente jurnal" className="market-json">
            {JSON.stringify(events, null, 2)}
          </pre>
          <button
            disabled={!eventPage || busy}
            onClick={() => void action(() => inspect(selected.id, eventPage - 1))}
          >
            Evenimente anterioare
          </button>
          <button
            disabled={events.length < 100 || busy}
            onClick={() => void action(() => inspect(selected.id, eventPage + 1))}
          >
            Evenimente următoare
          </button>
        </section>
      )}
    </section>
  );
}
