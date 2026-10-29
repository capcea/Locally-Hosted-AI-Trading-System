import { useState } from 'react';
import { Evidence } from '../ui/Controls';
import { phaseLabels, sourceLabels } from '../copy/ro';

export type Point = { at: string; timestamp: number; equity: string };
export function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}
export function exact(value: unknown): string {
  if (value === null || value === undefined) return 'Nu poate fi stabilit';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  return 'Vezi dovezile exacte';
}
export function ResultSummary({
  result,
  trial = 0,
  provenance,
  inputSources = {},
}: {
  result: unknown;
  trial?: number;
  provenance?: unknown;
  inputSources?: Record<string, string>;
}) {
  const summary = object(result);
  const trials = Array.isArray(summary.trials) ? summary.trials : [];
  const chosen = object(trials[trial]);
  const metrics = object(chosen.metrics);
  const plan = object(object(provenance).plan);
  const assumptions = object(plan.assumptions);
  const chronology = object(plan.chronology);
  const pins = Array.isArray(plan.datasets) ? plan.datasets : [];
  const currency =
    typeof assumptions.account_currency === 'string'
      ? assumptions.account_currency
      : 'monedă neconfirmată';
  return (
    <section aria-label="Înțelege rezultatul">
      <p>
        <strong>Execuție simulată</strong> ·{' '}
        {phaseLabels[String(summary.phase)] ?? 'Etapa se verifică în protocolul fixat'} · fără
        eligibilitate pentru ordine externe.
      </p>
      {summary.engine === 'SCREEN' && (
        <p className="notice">
          Explorare aproximativă: acest rezultat nu validează execuția și riscul. Nu îl confunda cu
          o simulare verificată de Risk Gateway.
        </p>
      )}
      <dl className="metric-grid">
        <div>
          <dt>Modificarea netă a capitalului simulat</dt>
          <dd>
            {exact(metrics.net_profit ?? chosen.approximate_net)} {currency}
          </dd>
        </div>
        <div>
          <dt>Cea mai mare scădere</dt>
          <dd>
            {exact(metrics.max_drawdown)} {currency}
          </dd>
        </div>
        <div>
          <dt>Tranzacții încheiate</dt>
          <dd>{exact(metrics.trade_count)}</dd>
        </div>
      </dl>
      <p>
        Cea mai mare scădere este pierderea observată de la un vârf anterior în acest test. Nu este
        limita pierderii viitoare.
      </p>
      <dl>
        <dt>Perioada protocolului</dt>
        <dd>
          {exact(chronology.start)} → {exact(chronology.end)} · UTC
        </dd>
        <dt>Costuri și ipoteze</dt>
        <dd>
          Comision: {exact(assumptions.commission_per_unit)}; derapaj:{' '}
          {exact(assumptions.slippage_ticks)} tick-uri; stres: {exact(chosen.cost_multiplier)}.
        </dd>
      </dl>
      <p>
        Spread-ul depinde de observațiile și modelul fixate. Finanțarea neconfirmată nu este
        presupusă gratuită.{' '}
        <strong>Costurile exacte și contextul monetar sunt păstrate în dovezi.</strong>
      </p>
      <p>
        Acoperirea este cea a versiunilor admise, nu cinci ani presupuşi. Sunt fixate {pins.length}{' '}
        fluxuri; sursa și disponibilitatea fiecăruia se inspectează în proveniență.
      </p>
      {pins.map((p, index) => {
        const pin = object(p);
        return (
          <p key={index}>
            Flux {index + 1}: {exact(pin.role)} ·{' '}
            {sourceLabels[inputSources[String(pin.dataset_id)]] ??
              'UNKNOWN · originea datelor nu poate fi citită, inclusiv dacă perioada este protejată'}{' '}
            · set {exact(pin.dataset_id)}
          </p>
        );
      })}
      <h4>Ce nu putem concluziona</h4>
      <p>
        Un rezultat pozitiv nu demonstrează profit viitor. Configurațiile încercate nu sunt
        observații independente. O evaluare ulterioară nu este automat o perioadă finală nevăzută.
      </p>
      <p>
        {metrics.ratios_reason === 'IRREGULAR_CALENDAR_DAILY_OBSERVATIONS'
          ? 'Lipsesc zile în seria observată. Indicatorii anualizați nu sunt afișați.'
          : metrics.ratios_reason
            ? 'Sunt prea puține observații zilnice pentru indicatorii anualizați.'
            : 'Indicatorii disponibili descriu numai eșantionul și ipotezele acestui test.'}{' '}
        Un indicator absent nu este zero și nu înseamnă risc absent.
      </p>
      <Evidence
        title="Protocol, costuri și avertismente exacte"
        value={{
          chronology,
          assumptions,
          transaction_costs: chosen.transaction_costs,
          warnings: summary.warnings,
          metrics,
        }}
      />
    </section>
  );
}

export function EquityChart({
  points,
  currency = 'moneda contului',
  total,
}: {
  points: Point[];
  currency?: string;
  total?: number;
}) {
  const [drawdown, setDrawdown] = useState(false);
  const valid = points.filter(
    (p) =>
      Number.isFinite(p.timestamp) &&
      Number.isFinite(new Date(p.timestamp * 1000).getTime()) &&
      Number.isFinite(Number(p.equity)),
  );
  if (valid.length < 2) return <p>Curba nu are suficiente observații stocate.</p>;
  let peak = -Infinity;
  const values = valid.map((p) => {
    const equity = Number(p.equity);
    peak = Math.max(peak, equity);
    return drawdown ? equity - peak : equity;
  });
  const min = Math.min(...values),
    max = Math.max(...values),
    range = max - min || 1;
  const first = valid[0].timestamp,
    duration = valid.at(-1)!.timestamp - first || 1;
  return (
    <figure className="chart-frame">
      <figcaption>
        <strong>
          {drawdown
            ? 'Scădere aproximativă între punctele afișate'
            : 'Capital simulat din observații stocate'}
        </strong>{' '}
        · {currency} · timp UTC
      </figcaption>
      <button
        type="button"
        className="secondary-button"
        aria-pressed={!drawdown}
        onClick={() => setDrawdown(false)}
      >
        Capital
      </button>{' '}
      <button
        type="button"
        className="secondary-button"
        aria-pressed={drawdown}
        onClick={() => setDrawdown(true)}
      >
        Scăderi · vizualizare aproximativă
      </button>
      <svg role="img" aria-label="Curba capitalului simulat stocat" viewBox="0 0 680 260">
        <title>
          {drawdown ? 'Scăderi aproximative, fără a înlocui maximul stocat' : 'Capital simulat'} în{' '}
          {currency}, timp UTC
        </title>
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <g key={fraction}>
            <line
              x1="100"
              x2="650"
              y1={200 - fraction * 160}
              y2={200 - fraction * 160}
              stroke="var(--line)"
            />
            <text x="5" y={195 - fraction * 160}>
              {(min + fraction * range).toPrecision(5)}
            </text>
          </g>
        ))}
        {[0.25, 0.5, 0.75].map((fraction) => (
          <g key={fraction}>
            <line
              x1={100 + fraction * 550}
              x2={100 + fraction * 550}
              y1="40"
              y2="200"
              stroke="var(--line)"
            />
            <text x={100 + fraction * 550} y="245" textAnchor="middle">
              {new Date((first + fraction * duration) * 1000)
                .toISOString()
                .slice(5, 16)
                .replace('T', ' ')}
            </text>
          </g>
        ))}
        <line x1="100" x2="650" y1="200" y2="200" stroke="currentColor" />
        {valid.map((p, i) => (
          <g key={i}>
            <line
              x1={100 + ((p.timestamp - first) / duration) * 550}
              x2={100 + ((p.timestamp - first) / duration) * 550}
              y1="200"
              y2={200 - ((values[i] - min) / range) * 160}
              stroke="var(--accent)"
              strokeWidth="2"
              opacity="0.12"
            />
            <circle
              cx={100 + ((p.timestamp - first) / duration) * 550}
              cy={200 - ((values[i] - min) / range) * 160}
              r="2"
              fill="var(--accent)"
            >
              <title>
                {p.at} · {drawdown ? 'aproximativ ' + values[i] : p.equity} {currency}
              </title>
            </circle>
          </g>
        ))}
        <text x="100" y="230">
          {valid[0].at.slice(0, 19)}
        </text>
        <text x="650" y="250" textAnchor="end">
          {valid.at(-1)!.at.slice(0, 19)}
        </text>
      </svg>
      <p>
        Coordonate grafice aproximative.{' '}
        {total !== undefined && total > points.length
          ? `Eșantion: ${points.length} din ${total} observații, min/max pe intervale.`
          : `${points.length} observații afișate.`}{' '}
        Punctele nu sunt unite peste intervale neobservate. Scăderea din eșantion nu înlocuiește cea
        mai mare scădere calculată și stocată de motor.
      </p>
      <details>
        <summary>Capital exact stocat</summary>
        <div
          className="table-scroll"
          role="region"
          aria-label="Valori exacte ale capitalului"
          tabIndex={0}
        >
          <table>
            <caption>Observațiile afișate, fără completarea golurilor</caption>
            <thead>
              <tr>
                <th scope="col">Moment UTC</th>
                <th scope="col">Capital · {currency}</th>
              </tr>
            </thead>
            <tbody>
              {valid.map((p, i) => (
                <tr key={i}>
                  <td>{p.at}</td>
                  <td>{p.equity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

export function StoredRecords({ value }: { value: unknown }) {
  const data = object(value);
  const items = Array.isArray(data.items) ? data.items : null;
  return (
    <section aria-label="Înregistrări și dovezi stocate">
      {items ? (
        <>
          <p>
            {items.length} înregistrări în pagina citită
            {data.total !== undefined ? ` din ${exact(data.total)}` : ''}. Nu reconstruim evenimente
            sau execuții lipsă.
          </p>
          <ol className="event-timeline">
            {items.map((entry, i) => {
              const row = object(entry);
              return (
                <li key={i}>
                  <strong>
                    {exact(
                      row.type ??
                        row.kind ??
                        row.event ??
                        row.action ??
                        row.at ??
                        row.timestamp ??
                        `Înregistrarea ${i + 1}`,
                    )}
                  </strong>
                  <dl>
                    {Object.entries(row)
                      .filter(([, v]) => v === null || typeof v !== 'object')
                      .slice(0, 12)
                      .map(([k, v]) => (
                        <div key={k}>
                          <dt>
                            {(
                              {
                                timestamp: 'Moment UTC',
                                at: 'Moment UTC',
                                type: 'Tip',
                                kind: 'Eveniment',
                                decision: 'Decizie de risc',
                                volume: 'Volum',
                                price: 'Preț',
                                commission: 'Comision',
                                train_start: 'Început pregătire',
                                train_end: 'Sfârșit pregătire',
                                oos_start: 'Început evaluare ulterioară',
                                oos_end: 'Sfârșit evaluare ulterioară',
                                training_net: 'Rezultat în pregătire',
                                purge_seconds: 'Separare temporală · secunde',
                                embargo_seconds: 'Interval exclus · secunde',
                              } as Record<string, string>
                            )[k] ?? k}
                          </dt>
                          <dd>{exact(v)}</dd>
                        </div>
                      ))}
                  </dl>
                  <Evidence value={entry} />
                </li>
              );
            })}
          </ol>
        </>
      ) : (
        <p>Vezi structura exactă a acestei secțiuni în detalii.</p>
      )}
      <Evidence value={value} />
    </section>
  );
}
