import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError } from './management-api';
import type { Session, RecordItem, RecordPage } from './management-api';
import type { components } from './generated/api';

type Dataset = components['schemas']['DatasetView'];
type Provider = components['schemas']['ProviderView'];
type Job = components['schemas']['JobView'];
type Sample = components['schemas']['Sample'];
type MarketRow = components['schemas']['Row'];

const text = {
  title: 'Centrul de date de piață',
  providers: 'Furnizori',
  history: 'Istoric și explorare',
  imports: 'Manager importuri',
  quality: 'Calitatea datelor',
  provenance: 'Proveniență',
  empty: 'Nu există seturi de date importate. Nu este presupusă nicio acoperire istorică.',
  source:
    'Datele sunt afișate din PostgreSQL și Parquet/MinIO. Nicio istorie nu este generată automat.',
};
function value(form: FormData, key: string) {
  return String(form.get(key) ?? '');
}
function Input({
  name,
  label,
  type = 'text',
  required = true,
  initial = '',
}: {
  name: string;
  label: string;
  type?: string;
  required?: boolean;
  initial?: string;
}) {
  return (
    <label className="management-field">
      <span>{label}</span>
      <input
        aria-label={label}
        name={name}
        type={type}
        required={required}
        defaultValue={initial}
      />
    </label>
  );
}
function Select({
  name,
  label,
  items,
}: {
  name: string;
  label: string;
  items: { id: string; name: string }[];
}) {
  return (
    <label className="management-field">
      <span>{label}</span>
      <select aria-label={label} name={name} required>
        <option value="">Alege…</option>
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
    </label>
  );
}
function PriceChart({ rows }: { rows: MarketRow[] }) {
  const [selected, setSelected] = useState(0);
  const points = rows
    .map((row) => ({ row, price: row.close ?? row.bid ?? row.price }))
    .filter(
      (p): p is { row: MarketRow; price: string } => p.price !== null && p.price !== undefined,
    );
  if (!points.length) return <p>Nu există prețuri în eșantionul disponibil la momentul ales.</p>;
  const prices = points.map((p) => Number(p.price));
  const low = Math.min(...prices),
    high = Math.max(...prices),
    range = high - low || 1;
  const index = Math.min(selected, points.length - 1);
  const coords = prices
    .map(
      (p, i) =>
        `${40 + (i / Math.max(1, prices.length - 1)) * 820},${200 - ((p - low) / range) * 160}`,
    )
    .join(' ');
  return (
    <div className="market-chart">
      <svg viewBox="0 0 900 240" role="img" aria-label="Prețuri din setul de date importat">
        <line x1="40" y1="200" x2="860" y2="200" stroke="currentColor" opacity="0.2" />
        <polyline points={coords} fill="none" stroke="var(--accent)" strokeWidth="2" />
        <text x="40" y="225" fill="currentColor" fontSize="12">
          {points[0].row.event_time}
        </text>
      </svg>
      <label>
        Observație{' '}
        <input
          aria-label="Observație în grafic"
          type="range"
          min="0"
          max={points.length - 1}
          value={index}
          onChange={(e) => setSelected(Number(e.target.value))}
        />
      </label>
      <p>
        <strong>{points[index].price}</strong> · UTC {points[index].row.event_time} · disponibil{' '}
        {points[index].row.available_at}
      </p>
    </div>
  );
}
export default function MarketData({
  session,
  onExpired,
}: {
  session: Session;
  onExpired: () => void;
}) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [instruments, setInstruments] = useState<RecordItem[]>([]);
  const [venues, setVenues] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<Dataset | null>(null);
  const [sample, setSample] = useState<Sample | null>(null);
  const [provenance, setProvenance] = useState<unknown>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [busy, setBusy] = useState(false);
  const canWrite = session.user.role !== 'VIEWER';
  const fail = useCallback(
    (e: unknown) => {
      setError(e instanceof Error ? e.message : 'Operațiune eșuată.');
      if (e instanceof ApiError && e.status === 401) onExpired();
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    try {
      const [p, d, j, a, i, v] = await Promise.all([
        api<Provider[]>('/market/providers'),
        api<components['schemas']['DatasetPage']>(
          `/market/datasets?offset=${page * 25}&limit=25&q=${encodeURIComponent(query)}`,
        ),
        api<Job[]>('/market/jobs'),
        api<RecordPage>('/records/accounts?limit=100'),
        api<RecordPage>('/records/instruments?limit=100'),
        api<RecordPage>('/records/venues?limit=100'),
      ]);
      setProviders(p);
      setDatasets(d.items);
      setTotal(d.total);
      setJobs(j);
      setAccounts(a.items);
      setInstruments(i.items);
      setVenues(v.items);
      setSelected((old) => (old ? (d.items.find((item) => item.id === old.id) ?? old) : null));
    } catch (e) {
      fail(e);
    }
  }, [page, query, fail]);
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 4000);
    return () => clearInterval(timer);
  }, [load]);
  const action = async (task: () => Promise<void>) => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      await task();
      await load();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };
  const mutate = <T,>(path: string, body: unknown) =>
    api<T>(path, { method: 'POST', body, csrf: session.csrf_token });
  const register = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    void action(async () => {
      await mutate('/market/providers', {
        name: value(data, 'name'),
        adapter: value(data, 'adapter'),
        rights_reference: value(data, 'rights'),
        attribution: value(data, 'attribution'),
        usage_rights_acknowledged: true,
      });
      setNotice('Furnizor înregistrat. Aceasta nu confirmă o conexiune externă.');
      form.reset();
    });
  };
  const createInstrument = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    void action(async () => {
      let venue = value(data, 'venue');
      if (!venue) {
        const created = await mutate<RecordItem>('/records/venues', {
          kind: 'venues',
          name: 'Importuri de date',
          venue_type: 'CUSTOM',
        });
        venue = created.id;
      }
      await mutate('/records/instruments', {
        kind: 'instruments',
        name: value(data, 'symbol'),
        symbol: value(data, 'symbol'),
        asset_class: value(data, 'asset'),
        venue_id: venue,
      });
      form.reset();
    });
  };
  const upload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    void action(async () => {
      const calendar = value(fields, 'calendar')
        ? {
            timezone: value(fields, 'zone'),
            weekdays: value(fields, 'weekdays').split(',').map(Number),
            holidays: value(fields, 'holidays')
              .split(',')
              .map((x) => x.trim())
              .filter(Boolean),
            opens: 0,
            closes: 1440,
            source: value(fields, 'calendar_source'),
            verified_until: new Date(value(fields, 'end')).toISOString(),
          }
        : null;
      const spec = {
        provider_id: value(fields, 'provider'),
        account_id: value(fields, 'account'),
        instrument_id: value(fields, 'instrument'),
        source_symbol: value(fields, 'symbol'),
        data_type: value(fields, 'type'),
        timeframe: value(fields, 'frame'),
        source_timezone: value(fields, 'zone'),
        format: value(fields, 'format'),
        provenance: value(fields, 'provenance'),
        start: new Date(value(fields, 'start')).toISOString(),
        end: new Date(value(fields, 'end')).toISOString(),
        calendar,
        transformation_reason: value(fields, 'reason') || null,
      };
      const provider = providers.find((p) => p.id === spec.provider_id);
      if (provider?.adapter === 'ECB') {
        await mutate('/market/jobs', { ...spec, provenance: 'PUBLIC_PROVIDER' });
      } else {
        const file = fields.get('file');
        if (!(file instanceof File) || !file.size)
          throw new Error('Selectează un fișier CSV sau Parquet.');
        const body = new FormData();
        body.set('spec_json', JSON.stringify(spec));
        body.set('file', file);
        const response = await fetch('/api/v1/market/imports', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRF-Token': session.csrf_token },
          body,
        });
        if (!response.ok)
          throw new ApiError(response.status, `Import refuzat (HTTP ${response.status}).`);
      }
      setNotice('Import înregistrat. Datele devin utilizabile după validare și publicare atomică.');
    });
  };
  const inspect = (dataset: Dataset) => {
    setSelected(dataset);
    setSample(null);
    setProvenance(null);
    setError('');
  };
  const retrieve = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selected) return;
    setSample(null);
    const fields = new FormData(event.currentTarget);
    void action(async () => {
      const params = new URLSearchParams({
        start: value(fields, 'start'),
        end: value(fields, 'end'),
        decision_at: new Date(value(fields, 'decision')).toISOString(),
        limit: '500',
        preview: 'true',
      });
      if (value(fields, 'sequence')) params.set('sequence_cutoff', value(fields, 'sequence'));
      setSample(await api<Sample>(`/market/datasets/${selected.id}/sample?${params}`));
    });
  };
  const names = (items: RecordItem[]) =>
    items.map((item) => ({ id: item.id, name: item.data.name }));
  return (
    <section className="panel management-panel market-data">
      <h2>{text.title}</h2>
      <p>{text.source}</p>
      <p>
        Țintă: cinci ani. Acoperirea este măsurată numai pentru intervalele importate; numărul
        așteptat de ticks poate fi necunoscut.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <label className="management-field">
        <span>Filtrează instrumente</span>
        <input
          aria-label="Filtrează instrumente"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(0);
          }}
        />
      </label>
      <div className="management-cards">
        {datasets.map((dataset) => (
          <article className="management-record" key={dataset.id}>
            <h3>
              {dataset.symbol} · v{dataset.version}
            </h3>
            <p>
              {dataset.spec.provenance} · {dataset.status} · {dataset.spec.data_type}/
              {dataset.spec.timeframe}
            </p>
            <p>
              {dataset.record_count} observații · acoperire{' '}
              {dataset.coverage_pct === null ? 'necunoscută' : `${dataset.coverage_pct}%`}
            </p>
            <p>
              {dataset.earliest ?? '—'} → {dataset.latest ?? '—'}
            </p>
            <button className="text-button" onClick={() => inspect(dataset)}>
              Explorează {dataset.symbol} v{dataset.version}
            </button>
          </article>
        ))}
      </div>
      {!datasets.length && <p>{text.empty}</p>}
      <div className="management-toolbar">
        <button className="text-button" disabled={!page} onClick={() => setPage(page - 1)}>
          Anterior
        </button>
        <span>
          Pagina {page + 1} · {total} seturi
        </span>
        <button
          className="text-button"
          disabled={(page + 1) * 25 >= total}
          onClick={() => setPage(page + 1)}
        >
          Următor
        </button>
      </div>
      {selected && (
        <section aria-label="Explorator set de date">
          <h3>
            {text.history} · {selected.symbol} v{selected.version}
          </h3>
          <strong>Proveniență: {selected.spec.provenance}</strong>
          <form className="management-form" onSubmit={retrieve} key={selected.id}>
            <Input name="start" label="Început interogare UTC" initial={selected.spec.start} />
            <Input name="end" label="Sfârșit interogare UTC" initial={selected.spec.end} />
            <Input
              name="decision"
              label="Informații disponibile la UTC"
              initial={new Date().toISOString()}
            />
            <Input
              name="sequence"
              label="Secvență maximă la momentul ales (opțional)"
              type="number"
              required={false}
            />
            <button className="secondary-button" disabled={busy}>
              Încarcă eșantionul
            </button>
          </form>
          {sample && (
            <>
              <p>
                {sample.items.length} observații; limită {sample.limit}
                {sample.truncated ? ' · interval trunchiat' : ''}. Previzualizarea unui set DEGRADED
                nu permite validarea strategiilor.
              </p>
              <PriceChart rows={sample.items} />
              <div className="market-table">
                <table>
                  <thead>
                    <tr>
                      <th>Secvență</th>
                      <th>UTC</th>
                      <th>Bid / Open</th>
                      <th>Ask / Close</th>
                      <th>Disponibil UTC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sample.items.slice(0, 20).map((row, i) => (
                      <tr key={i}>
                        <td>{row.sequence}</td>
                        <td>{row.event_time}</td>
                        <td>{row.bid ?? row.open ?? row.price ?? '—'}</td>
                        <td>{row.ask ?? row.close ?? '—'}</td>
                        <td>{row.available_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <h3>{text.quality}</h3>
          <p>Stare: {selected.status}. Numai VALID poate intra în cercetare.</p>
          <pre className="market-json">{JSON.stringify(selected.quality, null, 2)}</pre>
          <h3>{text.provenance}</h3>
          <p>
            Manifest SHA-256: <code>{selected.manifest_sha256 ?? 'nepublicat'}</code>
          </p>
          <button
            className="text-button"
            onClick={() =>
              void action(async () =>
                setProvenance(await api(`/market/datasets/${selected.id}/provenance`)),
              )
            }
          >
            Verifică manifestul și proveniența
          </button>
          {provenance !== null && (
            <section aria-label="Detalii de proveniență">
              <pre className="market-json">{JSON.stringify(provenance, null, 2)}</pre>
            </section>
          )}
          <label className="management-field">
            <span>Compară versiuni</span>
            <select
              aria-label="Compară versiuni"
              defaultValue=""
              onChange={(e) => {
                const other = e.target.value;
                if (other)
                  void action(async () =>
                    setProvenance(await api(`/market/datasets/${selected.id}/compare/${other}`)),
                  );
              }}
            >
              <option value="">Alege setul…</option>
              {datasets
                .filter((d) => d.id !== selected.id)
                .map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.symbol} v{d.version}
                  </option>
                ))}
            </select>
          </label>
        </section>
      )}
      <h3>{text.imports}</h3>
      <div className="management-cards">
        {jobs.map((job) => (
          <article className="management-record" key={job.id}>
            <code>{job.id}</code>
            <p>
              {job.state} · {job.progress_rows} rânduri · încercări {job.attempts}
            </p>
            {job.error_code && <p>{job.error_code}</p>}
            {canWrite && ['QUEUED', 'RETRY', 'RUNNING'].includes(job.state) && (
              <button
                className="text-button"
                onClick={() =>
                  void action(async () => {
                    await mutate(`/market/jobs/${job.id}/cancel`, {});
                  })
                }
              >
                Anulează importul
              </button>
            )}
          </article>
        ))}
      </div>
      {canWrite && (
        <>
          <form className="management-form" onSubmit={upload} aria-label="Import istoric">
            <h3>Importă CSV/Parquet sau descarcă referințe ECB</h3>
            <Select
              name="provider"
              label="Furnizor import"
              items={providers.map((p) => ({ id: p.id, name: p.name }))}
            />
            <Select name="account" label="Cont pentru date" items={names(accounts)} />
            <Select name="instrument" label="Instrument import" items={names(instruments)} />
            <Input name="symbol" label="Simbol exact la sursă" />
            <Select
              name="type"
              label="Tip de date"
              items={['TICK', 'BAR', 'REFERENCE', 'EVENT', 'SESSION'].map((id) => ({
                id,
                name: id,
              }))}
            />
            <Select
              name="frame"
              label="Interval de timp"
              items={['TICK', 'M1', 'M5', 'M15', 'H1', 'H4', 'D1'].map((id) => ({ id, name: id }))}
            />
            <Select
              name="format"
              label="Format fișier"
              items={['CSV', 'PARQUET'].map((id) => ({ id, name: id }))}
            />
            <Select
              name="provenance"
              label="Originea datelor"
              items={['USER_SUPPLIED', 'SYNTHETIC_TEST_FIXTURE', 'PUBLIC_PROVIDER'].map((id) => ({
                id,
                name: id,
              }))}
            />
            <Input name="zone" label="Fus orar original IANA" initial="UTC" />
            <Input name="start" label="Început import UTC" initial="2024-01-02T00:00:00Z" />
            <Input name="end" label="Sfârșit import UTC" initial="2024-01-02T00:05:00Z" />
            <Input name="file" label="Fișier istoric" type="file" required={false} />
            <Input name="reason" label="Justificare revizie (opțional)" required={false} />
            <label className="management-check">
              <input name="calendar" type="checkbox" /> Declar explicit calendarul sesiunii pentru
              acest interval
            </label>
            <Input name="weekdays" label="Zile deschise (0=luni, 6=duminică)" initial="0,1,2,3,4" />
            <Input
              name="holidays"
              label="Sărbători YYYY-MM-DD, separate prin virgulă"
              required={false}
            />
            <Input name="calendar_source" label="Sursa calendarului declarat" required={false} />
            <p>
              Fișierele necesită event_time, observed_at și available_at. Orele ambigue DST necesită
              fold. Fără calendar verificat, calitatea rămâne DEGRADED. ECB oferă numai referințe
              zilnice EUR/valută, fără bid/ask sau volum.
            </p>
            <button className="secondary-button" disabled={busy}>
              Pornește importul
            </button>
          </form>
          {!accounts.length && (
            <p>Configurează mai întâi un cont SIMULATED în Cont & administrare.</p>
          )}
          <form
            className="management-form"
            onSubmit={createInstrument}
            aria-label="Înregistrare instrument"
          >
            <h3>Înregistrează un instrument</h3>
            <Input name="symbol" label="Simbol canonic" />
            <label className="management-field">
              Loc de tranzacționare (opțional)
              <select name="venue" aria-label="Loc de tranzacționare">
                <option value="">Registru de import nou</option>
                {names(venues).map((v) => (
                  <option value={v.id} key={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </label>
            <Select
              name="asset"
              label="Clasă de active"
              items={['FOREX', 'METAL', 'INDEX', 'CRYPTO', 'OTHER'].map((id) => ({ id, name: id }))}
            />
            <button className="secondary-button" disabled={busy}>
              Salvează instrumentul
            </button>
          </form>
          <form className="management-form" onSubmit={register} aria-label="Înregistrare furnizor">
            <h3>{text.providers}</h3>
            <Input name="name" label="Denumire furnizor" />
            <Select
              name="adapter"
              label="Adaptor de date"
              items={['LOCAL', 'ECB', 'MT5_EXPORT', 'PREMIUM'].map((id) => ({ id, name: id }))}
            />
            <Input name="rights" label="Referință licență / drepturi de utilizare" />
            <Input name="attribution" label="Atribuire sursă" />
            <label className="management-check">
              <input type="checkbox" required /> Confirm dreptul de utilizare a acestor date
            </label>
            <button className="secondary-button" disabled={busy}>
              Înregistrează furnizorul
            </button>
          </form>
        </>
      )}
      <div className="management-cards">
        {providers.map((p) => (
          <article className="management-record" key={p.id}>
            <h3>{p.name}</h3>
            <p>
              {p.adapter} · {p.attribution}
            </p>
            <p>{p.rights_reference}</p>
            <pre className="market-json">{JSON.stringify(p.capabilities, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
