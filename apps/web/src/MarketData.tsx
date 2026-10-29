import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError, safeError } from './management-api';
import type { Session, RecordItem } from './management-api';
import type { components } from './generated/api';
import { useRoute, navigate, Link } from './navigation/history';
import { Evidence, Field, SelectField } from './ui/Controls';
import { sourceLabels, jobLabels } from './copy/ro';
import { allRecords } from './records';

type Dataset = components['schemas']['DatasetView'];
type Provider = components['schemas']['ProviderView'];
type Job = components['schemas']['JobView'];
type Sample = components['schemas']['Sample'];
type MarketRow = components['schemas']['Row'];

const text = {
  title: 'Date pentru teste',
  providers: 'Furnizori',
  history: 'Istoric și explorare',
  imports: 'Manager importuri',
  quality: 'Calitatea datelor',
  provenance: 'De unde provin datele',
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
  return <Field label={label} name={name} type={type} required={required} defaultValue={initial} />;
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
    <SelectField name={name} label={label} required>
      <option value="">Alege…</option>
      {items.map((item) => (
        <option key={item.id} value={item.id}>
          {item.name}
        </option>
      ))}
    </SelectField>
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
  const times = points.map((p) => Date.parse(p.row.event_time));
  const firstTime = Math.min(...times);
  const duration = Math.max(...times) - firstTime || 1;
  const coords = prices
    .map(
      (p, i) =>
        `${40 + ((times[i] - firstTime) / duration) * 820},${200 - ((p - low) / range) * 160}`,
    )
    .join(' ');
  return (
    <div className="market-chart">
      <p>
        Momente UTC reale pe axa orizontală. Observațiile nu sunt unite peste intervale neobservate;
        nu sunt prețuri interpolate.
      </p>
      <svg viewBox="0 0 900 240" role="img" aria-label="Prețuri din setul de date importat">
        <line x1="40" y1="200" x2="860" y2="200" stroke="currentColor" opacity="0.2" />
        {coords.split(' ').map((point, i) => {
          const [x, y] = point.split(',');
          return <circle key={i} cx={x} cy={y} r="3" fill="var(--accent)" />;
        })}
        <text x="40" y="20">
          Preț în unitățile sursei · {high.toPrecision(6)}
        </text>
        <text x="40" y="195">
          {low.toPrecision(6)}
        </text>
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
  settingsView,
}: {
  session: Session;
  onExpired: () => void;
  settingsView?: 'surse';
}) {
  const route = useRoute();
  const [importStep, setImportStep] = useState(1);
  const [importReview, setImportReview] = useState<Record<string, string>>({});
  const [focusedJob, setFocusedJob] = useState<Job | null>(null);
  const [cancelRequests, setCancelRequests] = useState<string[]>([]);
  const [readFailed, setReadFailed] = useState(false);
  const showImport = route.section === 'import';
  const showSources =
    route.area === 'settings' && (route.section === 'surse' || settingsView === 'surse');
  const showInstruments = route.area === 'settings' && route.section === 'catalog';
  const showCatalog = route.area === 'research' && !showImport;
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
      setError(safeError(e));
      if (e instanceof ApiError && e.status === 401) onExpired();
    },
    [onExpired],
  );
  const load = useCallback(async () => {
    try {
      const values = await Promise.allSettled([
        api<Provider[]>('/market/providers'),
        api<components['schemas']['DatasetPage']>(
          `/market/datasets?offset=${page * 25}&limit=25&q=${encodeURIComponent(query)}`,
        ),
        api<Job[]>('/market/jobs'),
        allRecords('accounts'),
        allRecords('instruments'),
        allRecords('venues'),
      ] as const);
      const [p, d, j, a, i, v] = values;
      setReadFailed(d.status === 'rejected');
      if (p.status === 'fulfilled') setProviders(p.value);
      if (d.status === 'fulfilled') {
        setDatasets(d.value.items);
        setTotal(d.value.total);
        setSelected((old) =>
          old ? (d.value.items.find((item) => item.id === old.id) ?? old) : null,
        );
      }
      if (j.status === 'fulfilled') setJobs(j.value);
      if (a.status === 'fulfilled') setAccounts(a.value);
      if (i.status === 'fulfilled') setInstruments(i.value);
      if (v.status === 'fulfilled') setVenues(v.value);
      const failure = values.find((v) => v.status === 'rejected');
      if (failure?.status === 'rejected') fail(failure.reason);
    } catch (e) {
      setReadFailed(true);
      fail(e);
    }
  }, [page, query, fail]);
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 4000);
    return () => clearInterval(timer);
  }, [load]);
  useEffect(() => {
    if (!route.datasetId) return;
    setSelected(null);
    setSample(null);
    setProvenance(null);
    let active = true;
    void api<Dataset>(`/market/datasets/${route.datasetId}`)
      .then((dataset) => {
        if (active) {
          setSelected(dataset);
          setSample(null);
          setProvenance(null);
        }
      })
      .catch(fail);
    return () => {
      active = false;
    };
  }, [route.datasetId, fail]);
  useEffect(() => {
    if (!route.jobId) return;
    let active = true;
    const read = () =>
      api<Job>(`/market/jobs/${route.jobId}`)
        .then((job) => {
          if (active) setFocusedJob(job);
        })
        .catch(fail);
    void read();
    const timer = setInterval(() => void read(), 4000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [route.jobId, fail]);
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
            opens: Number(value(fields, 'opens')),
            closes: Number(value(fields, 'closes')),
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
        const job = await mutate<Job>('/market/jobs', { ...spec, provenance: 'PUBLIC_PROVIDER' });
        navigate(`/testeaza/date/importuri/${job.id}`);
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
          throw new ApiError(
            response.status,
            `Import refuzat (HTTP ${response.status}). Verifică formatul, drepturile și limitele; nu presupunem că datele sunt admise.`,
          );
        const job = (await response.json()) as Job;
        navigate(`/testeaza/date/importuri/${job.id}`);
      }
      setNotice('Import înregistrat. Datele devin utilizabile după validare și publicare atomică.');
    });
  };
  const inspect = (dataset: Dataset) => {
    setSelected(dataset);
    navigate(`/testeaza/date/${dataset.id}`);
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
    <section
      className={`panel management-panel market-data${showSources ? ' v1-platform-sources' : ''}`}
    >
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
      <nav className="section-navigation" aria-label="Date și configurare">
        <Link href="/testeaza/date">Seturi de date</Link>
        <Link className="primary-button" href="/testeaza/date/import">
          Adaugă date istorice
        </Link>
        <Link href="/setari/surse">Surse și drepturi</Link>
        <Link href="/setari/catalog">Instrumente și locuri</Link>
      </nav>
      {showCatalog && !route.jobId && (
        <>
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
          {!datasets.length && !readFailed && (
            <p>{query ? 'Niciun set nu corespunde filtrului.' : text.empty}</p>
          )}
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
        </>
      )}
      {selected && selected.id === route.datasetId && (
        <section aria-label="Explorator set de date">
          <h3>
            {text.history} · {selected.symbol} v{selected.version}
          </h3>
          <strong>
            {sourceLabels[selected.spec.provenance] ?? selected.spec.provenance} · execuție
            simulată. Calitatea nu certifică independent autenticitatea sursei.
          </strong>
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
          <p>
            {selected.status === 'VALID'
              ? 'Date admise pentru utilizările permise. Eligibilitatea testului se verifică separat.'
              : selected.status === 'DEGRADED'
                ? 'Date care necesită verificare. Previzualizarea nu permite cercetarea.'
                : 'Date blocate sau încă în verificare. Un upload nu este admitere.'}
          </p>
          <dl>
            {Object.entries((selected.quality.counts ?? {}) as Record<string, unknown>).map(
              ([code, count]) => (
                <div key={code}>
                  <dt>
                    {(
                      {
                        MISSING_BARS: 'Bare de preț lipsă',
                        EMPTY_DATASET: 'Fișier fără observații admisibile',
                        SESSION_CALENDAR_UNVERIFIED: 'Calendar neverificat',
                        SESSION_CALENDAR_EXPIRED: 'Calendar expirat',
                        SOURCE_SYMBOL_MISMATCH: 'Simbol diferit de sursa declarată',
                        OUTSIDE_REQUESTED_RANGE: 'Observații în afara perioadei',
                        AVAILABILITY_PRECEDES_OBSERVATION:
                          'Disponibilitate anterioară observării — cronologie invalidă',
                        OBSERVATION_PRECEDES_PRICE:
                          'Observație anterioară prețului — cronologie invalidă',
                        BAR_AVAILABLE_BEFORE_CLOSE: 'Bară disponibilă înainte de închidere',
                        BID_ASK_MISSING: 'Lipsesc prețuri de cumpărare sau vânzare',
                        OHLC_MISSING: 'Lipsesc prețuri ale barei',
                        OHLC_INCONSISTENT: 'Prețurile barei nu sunt coerente',
                        OUT_OF_ORDER: 'Observații în ordine greșită',
                        DUPLICATE_RECORD: 'Observații duplicate',
                        PRICE_SPIKE: 'Variații de preț care necesită revizuire',
                        CLOSED_SESSION_OR_HOLIDAY: 'Observații în afara sesiunii declarate',
                      } as Record<string, string>
                    )[code] ?? `Verificare: ${code}`}
                  </dt>
                  <dd>{String(count)}</dd>
                </div>
              ),
            )}
          </dl>
          <Evidence
            title="Raport de calitate exact și rânduri semnalate"
            value={selected.quality}
          />
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
              <pre tabIndex={0} className="market-json">
                {JSON.stringify(provenance, null, 2)}
              </pre>
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
      {showCatalog && (
        <>
          <h3>{text.imports}</h3>
          <div className="management-cards">
            {(route.jobId ? (focusedJob ? [focusedJob] : []) : jobs).map((job) => (
              <article className="management-record" key={job.id}>
                <code>{job.id}</code>
                <p>
                  {jobLabels[job.state] ?? job.state} · {job.state} · {job.progress_rows} rânduri ·
                  încercări {job.attempts}
                </p>
                {job.error_code && (
                  <p>
                    Importul nu a fost admis. Verifică formatul, simbolul și momentele sursei.{' '}
                    <Evidence value={{ code: job.error_code }} />
                  </p>
                )}
                {(cancelRequests.includes(job.id) || job.cancel_requested) &&
                  !['CANCELLED', 'SUCCEEDED', 'FAILED'].includes(job.state) && (
                    <p role="status">Anularea a fost cerută. Așteptăm confirmarea.</p>
                  )}
                <Link href={`/testeaza/date/${job.dataset_id}`}>
                  Vezi calitatea și datele importului
                </Link>
                {canWrite && ['QUEUED', 'RETRY', 'RUNNING'].includes(job.state) && (
                  <button
                    className="text-button"
                    onClick={() =>
                      void action(async () => {
                        await mutate(`/market/jobs/${job.id}/cancel`, {});
                        setCancelRequests((old) => [...old, job.id]);
                      })
                    }
                  >
                    Solicită anularea importului
                  </button>
                )}
              </article>
            ))}
          </div>
        </>
      )}
      {!canWrite && (
        <p>
          Rolul Doar citire permite inspectarea datelor, nu importul sau modificarea configurației.
        </p>
      )}
      {canWrite && (
        <>
          {showImport && (
            <form
              className="management-form panel"
              aria-label="Import istoric"
              onSubmit={(e) => {
                if (importStep !== 5) {
                  e.preventDefault();
                  return;
                }
                upload(e);
              }}
            >
              <h3>Adaugă date istorice · Pasul {importStep} din 5</h3>
              <p>
                După înregistrare urmează pasul6: rezultatul real al verificării calității. Nicio
                mapare nu inventează momente sau prețuri.
              </p>
              <fieldset data-step="1" hidden={importStep !== 1}>
                <legend>Alege sursa permisă</legend>{' '}
                <Select
                  name="provider"
                  label="Furnizor import"
                  items={providers.map((p) => ({ id: p.id, name: p.name }))}
                />
                <p>
                  Înregistrarea sursei și drepturile trebuie revizuite înainte de utilizare.{' '}
                  <Link href="/setari/surse">Configurează o sursă</Link>
                </p>
              </fieldset>
              <fieldset data-step="2" hidden={importStep !== 2}>
                <legend>Alege instrumentul și contul</legend>{' '}
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
                  items={['TICK', 'M1', 'M5', 'M15', 'H1', 'H4', 'D1'].map((id) => ({
                    id,
                    name: id,
                  }))}
                />
                <Link href="/setari/catalog">
                  Lipsește instrumentul? Configurează-l fără a presupune tradabilitatea.
                </Link>
              </fieldset>
              <fieldset data-step="3" hidden={importStep !== 3}>
                <legend>Verifică fișierul și momentele sursei</legend>{' '}
                <Select
                  name="format"
                  label="Format fișier"
                  items={['CSV', 'PARQUET'].map((id) => ({ id, name: id }))}
                />
                <Select
                  name="provenance"
                  label="Originea datelor"
                  items={['USER_SUPPLIED', 'SYNTHETIC_TEST_FIXTURE', 'PUBLIC_PROVIDER'].map(
                    (id) => ({
                      id,
                      name: sourceLabels[id] ?? id,
                    }),
                  )}
                />
                <Input name="zone" label="Fus orar original IANA" initial="UTC" />
                <Input name="start" label="Început import UTC" />
                <Input name="end" label="Sfârșit import UTC" />
                <Input name="file" label="Fișier istoric" type="file" required={false} />
                <p>
                  CSV/Parquet trebuie să respecte contractul adaptorului:
                  event_time/original_timestamp, observed_at și available_at sunt momente diferite.
                  TICK necesită bid/ask reale ale sursei; BAR necesită OHLC cu disponibilitate după
                  închidere. Nu corectăm automat momentele lipsă sau ambigue.
                </p>
                <Evidence
                  title="Schema și conversia exactă"
                  value={{
                    timestamps: ['event_time / original_timestamp', 'observed_at', 'available_at'],
                    exact_prices: 'șiruri zecimale, nu valori inventate',
                    DST: 'fus IANA și fold explicit când ora este ambiguă',
                  }}
                />
              </fieldset>
              <fieldset data-step="4" hidden={importStep !== 4}>
                <legend>Confirmă drepturile și calendarul</legend>{' '}
                <Input name="reason" label="Justificare revizie (opțional)" required={false} />
                <label className="management-check">
                  <input name="calendar" type="checkbox" /> Declar explicit calendarul sesiunii
                  pentru acest interval
                </label>
                <Input
                  name="opens"
                  label="Minut deschidere local (0 înseamnă 00:00)"
                  type="number"
                  initial="0"
                />
                <Input
                  name="closes"
                  label="Minut închidere local (1440 înseamnă sfârșitul zilei)"
                  type="number"
                  initial="1440"
                />
                <Input
                  name="weekdays"
                  label="Zile deschise (0=luni, 6=duminică)"
                  initial="0,1,2,3,4"
                />
                <Input
                  name="holidays"
                  label="Sărbători YYYY-MM-DD, separate prin virgulă"
                  required={false}
                />
                <Input
                  name="calendar_source"
                  label="Sursa calendarului declarat"
                  required={false}
                />
                <p>
                  Fișierele necesită event_time, observed_at și available_at. Orele ambigue DST
                  necesită fold. Fără calendar verificat, calitatea rămâne DEGRADED. ECB oferă numai
                  referințe zilnice EUR/valută, fără bid/ask sau volum.
                </p>
                <label className="management-check">
                  <input type="checkbox" required />
                  Am verificat drepturile sursei, simbolul exact și fusul orar original. Nu presupun
                  un calendar sau momente de disponibilitate lipsă.
                </label>
              </fieldset>
              <fieldset data-step="5" hidden={importStep !== 5}>
                <legend>Revizuiește înainte de import</legend>
                <dl>
                  {Object.entries(importReview).map(([key, v]) => (
                    <div key={key}>
                      <dt>
                        {(
                          {
                            provider: 'Sursă',
                            account: 'Cont',
                            instrument: 'Instrument',
                            symbol: 'Simbol la sursă',
                            type: 'Tip',
                            frame: 'Interval',
                            format: 'Format',
                            provenance: 'Origine',
                            zone: 'Fus orar original',
                            start: 'Început UTC',
                            end: 'Sfârșit UTC',
                          } as Record<string, string>
                        )[key] ?? key}
                      </dt>
                      <dd>
                        {key === 'provider'
                          ? (providers.find((p) => p.id === v)?.name ?? v)
                          : key === 'account'
                            ? (accounts.find((a) => a.id === v)?.data.name ?? v)
                            : key === 'instrument'
                              ? (instruments.find((i) => i.id === v)?.data.name ?? v)
                              : (sourceLabels[v] ?? v)}
                      </dd>
                    </div>
                  ))}
                </dl>
                <p>
                  Încărcarea reușită nu înseamnă date admise. Vom afișa starea reală, acoperirea și
                  motivele de respingere. ECB oferă cursuri zilnice de referință, fără bid/ask sau
                  lichiditate pentru ordine.
                </p>
                <button type="submit" className="primary-button" disabled={busy}>
                  Pornește importul
                </button>
              </fieldset>
              <div className="wizard-actions">
                <button
                  type="button"
                  className="secondary-button"
                  disabled={importStep === 1 || busy}
                  onClick={() => setImportStep(importStep - 1)}
                >
                  Înapoi
                </button>
                {importStep < 5 && (
                  <button
                    type="button"
                    onClick={(e) => {
                      const form = e.currentTarget.form!;
                      const fields = form
                        .querySelector(`fieldset[data-step="${importStep}"]`)!
                        .querySelectorAll<HTMLInputElement | HTMLSelectElement>('input,select');
                      if (Array.from(fields).some((f) => !f.reportValidity())) return;
                      const data = new FormData(form);
                      if (
                        importStep === 3 &&
                        (!Number.isFinite(Date.parse(String(data.get('start')))) ||
                          !Number.isFinite(Date.parse(String(data.get('end')))) ||
                          Date.parse(String(data.get('start'))) >=
                            Date.parse(String(data.get('end'))))
                      ) {
                        setError(
                          'Perioada nu este validă. Introdu momente UTC ISO și un sfârșit ulterior începutului.',
                        );
                        return;
                      }
                      setError('');
                      setImportReview(
                        Object.fromEntries(
                          [
                            'provider',
                            'account',
                            'instrument',
                            'symbol',
                            'type',
                            'frame',
                            'format',
                            'provenance',
                            'zone',
                            'start',
                            'end',
                          ].map((name) => [name, String(data.get(name) ?? '')]),
                        ),
                      );
                      setImportStep(importStep + 1);
                    }}
                  >
                    Continuă
                  </button>
                )}
              </div>
            </form>
          )}
          {!accounts.length && (
            <p>Configurează mai întâi un cont pentru simulare în Conturi și siguranță.</p>
          )}
          {showInstruments && (
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
                items={['FOREX', 'METAL', 'INDEX', 'CRYPTO', 'OTHER'].map((id) => ({
                  id,
                  name: id,
                }))}
              />
              <button className="secondary-button" disabled={busy}>
                Salvează instrumentul
              </button>
            </form>
          )}
        </>
      )}
      {showInstruments && (
        <section>
          <h3>Instrumente înregistrate</h3>
          <p>Metadatele nu certifică specificația sau tradabilitatea la broker.</p>
          {instruments.map((item) => (
            <article className="management-record" key={item.id}>
              <h4>{item.data.name}</h4>
              <Evidence value={item} />
            </article>
          ))}
        </section>
      )}
      {showSources && (
        <div className="v1-provider-columns">
          <div className="management-cards" aria-label="Surse înregistrate">
            <h3>Furnizori de date</h3>
            <p>
              Înregistrarea nu confirmă disponibilitatea, drepturile sau calitatea datelor. ECB
              oferă cursuri de referință, nu cotații bid/ask tranzacționabile.
            </p>
            {!providers.length && (
              <p>
                {readFailed
                  ? 'UNKNOWN · sursele nu pot fi verificate.'
                  : 'Niciun furnizor înregistrat. Completează formularul pentru o sursă permisă.'}
              </p>
            )}
            {providers.map((p) => (
              <article className="management-record" key={p.id}>
                <h3>{p.name}</h3>
                <p>
                  {p.adapter} · {p.attribution}
                </p>
                <p>{p.rights_reference}</p>
                <pre tabIndex={0} className="market-json">
                  {JSON.stringify(p.capabilities, null, 2)}
                </pre>
              </article>
            ))}
          </div>
          {canWrite && (
            <form
              className="management-form"
              onSubmit={register}
              aria-label="Înregistrare furnizor"
            >
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
          )}
        </div>
      )}
    </section>
  );
}
