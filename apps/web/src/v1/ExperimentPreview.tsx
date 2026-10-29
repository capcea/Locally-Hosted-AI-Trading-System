import { ChartNoAxesCombined, Activity, CircleDollarSign, ShieldCheck, Target } from 'lucide-react';
import { EquityChart, exact, object } from '../results/ResultView';
import type { Point } from '../results/ResultView';
import { Link } from '../navigation/history';
import { resultPath } from '../navigation/routes';
import { sourceLabels } from '../copy/ro';
import { useOwnedRead } from './data';
import { EmptyState, Kpi } from './components';

export function storedTrial(result: unknown, index = 0) {
  const trials = object(result).trials;
  return object(Array.isArray(trials) ? trials[index] : null);
}
export const percent = (value: unknown) =>
  typeof value === 'number' && Number.isFinite(value)
    ? `${(value * 100).toLocaleString('ro-RO', { maximumFractionDigits: 2 })}%`
    : 'Indisponibil';
/** Mount only after the existing matched-comparison endpoint succeeds. No client eligibility/ranking. */
export function MatchedComparison({
  comparison,
  leftProvenance,
  rightProvenance,
}: {
  comparison: unknown;
  leftProvenance: unknown;
  rightProvenance: unknown;
}) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label="Comparație acceptată de server"
      tabIndex={0}
    >
      <table>
        <caption>
          Scenariul 1 al fiecărui test · condiții comparabile conform serverului, fără clasament de
          profitabilitate
        </caption>
        <thead>
          <tr>
            <th scope="col">Test</th>
            <th scope="col">Rezultat net simulat</th>
            <th scope="col">Profit Factor</th>
            <th scope="col">Tranzacții câștigătoare</th>
            <th scope="col">Cea mai mare scădere</th>
            <th scope="col">Stres costuri</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['left', 'Experiment A', leftProvenance],
            ['right', 'Experiment B', rightProvenance],
          ].map(([side, label, provenance]) => {
            const trial = storedTrial(object(comparison)[String(side)]),
              metrics = object(trial.metrics),
              currency = object(object(object(provenance).plan).assumptions).account_currency;
            return (
              <tr key={String(side)}>
                <th scope="row">
                  {String(label)}
                  {object(object(comparison)[String(side)]).engine === 'SCREEN' && (
                    <small> · explorare aproximativă, risc nevalidat</small>
                  )}
                </th>
                <td>
                  {exact(metrics.net_profit ?? trial.approximate_net)}{' '}
                  {typeof currency === 'string' ? currency : 'monedă neconfirmată'}
                </td>
                <td>{exact(metrics.profit_factor)}</td>
                <td>{percent(metrics.win_rate)}</td>
                <td>
                  {exact(metrics.max_drawdown)}{' '}
                  {typeof currency === 'string' ? currency : 'monedă neconfirmată'}
                </td>
                <td>{exact(trial.cost_multiplier)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p>
        Condițiile identice nu elimină selecția dintre încercări sau incertitudinea. Inspectează și
        celelalte scenarii și sursele de mai jos.
      </p>
    </div>
  );
}
export function ResultTiles({
  result,
  currency,
  trial = 0,
}: {
  result: unknown;
  currency: string;
  trial?: number;
}) {
  const chosen = storedTrial(result, trial),
    metrics = object(chosen.metrics);
  const approximate = object(result).engine === 'SCREEN';
  return (
    <div className="v1-kpis" aria-label="Indicatorii scenariului selectat">
      <Kpi
        label={approximate ? 'Explorare aproximativă' : 'Rezultat net simulat'}
        value={exact(metrics.net_profit ?? chosen.approximate_net)}
        help={currency + (approximate ? ' · risc nevalidat' : ' · scenariul selectat')}
        icon={CircleDollarSign}
      />
      <Kpi
        label="Profit Factor"
        value={metrics.profit_factor == null ? 'Indisponibil' : exact(metrics.profit_factor)}
        help="Câștiguri / pierderi în test; nu o garanție"
        icon={Target}
        tone="violet"
      />
      <Kpi
        label="Tranzacții câștigătoare"
        value={percent(metrics.win_rate)}
        help="Proporție în eșantion, nu probabilitate viitoare"
        icon={ChartNoAxesCombined}
        tone="green"
      />
      <Kpi
        label="Cea mai mare scădere"
        value={exact(metrics.max_drawdown)}
        help={currency + ' · valoare calculată de motor'}
        icon={ShieldCheck}
        tone="amber"
      />
    </div>
  );
}

export function ExperimentPreview({ id, compact = false }: { id: string; compact?: boolean }) {
  const summary = useOwnedRead<unknown>(`/research/experiments/${encodeURIComponent(id)}/results`);
  const curve = useOwnedRead<{ items: Point[]; total: number }>(
    `/research/experiments/${encodeURIComponent(id)}/results?section=equity&trial=0&limit=500&chart=true`,
  );
  const provenance = useOwnedRead<unknown>(
    `/research/experiments/${encodeURIComponent(id)}/provenance`,
  );
  const datasetPins = object(object(provenance.data).plan).datasets;
  const firstDataset = Array.isArray(datasetPins) ? object(datasetPins[0]).dataset_id : null;
  const source = useOwnedRead<{ spec: { provenance: string } }>(
    typeof firstDataset === 'string'
      ? `/market/datasets/${encodeURIComponent(firstDataset)}`
      : null,
  );
  if (summary.failed || curve.failed || provenance.failed)
    return (
      <EmptyState
        icon={Activity}
        title="Rezultatul nu poate fi citit acum"
        href={resultPath(id)}
        action="Verifică accesul și dovezile"
      >
        UNKNOWN · accesul, integritatea sau perioada protejată trebuie verificate. Nu afișăm valori
        parțiale ca rezultat confirmat.
      </EmptyState>
    );
  if (!summary.data || !curve.data || !provenance.data)
    return (
      <div className="v1-empty" role="status">
        Citim rezultatul și proveniența experimentului…
      </div>
    );
  const plan = object(object(provenance.data).plan),
    assumptions = object(plan.assumptions);
  const currency =
    typeof assumptions.account_currency === 'string'
      ? assumptions.account_currency
      : 'monedă neconfirmată';
  const chosen = storedTrial(summary.data),
    metrics = object(chosen.metrics);
  const approximate = object(summary.data).engine === 'SCREEN';
  return (
    <div className={compact ? 'v1-preview v1-preview-compact' : 'v1-preview'}>
      {approximate && (
        <p className="notice v1-preview-note">
          Explorare aproximativă · acest rezultat nu validează execuția sau riscul.
        </p>
      )}
      {!compact && <ResultTiles result={summary.data} currency={currency} />}
      {compact && (
        <dl className="v1-chart-summary">
          <div>
            <dt>
              {approximate ? 'Rezultat aproximativ · risc nevalidat' : 'Rezultat net (simulat)'}
            </dt>
            <dd>
              {exact(metrics.net_profit ?? chosen.approximate_net)} <small>{currency}</small>
            </dd>
          </div>
          {[
            ['Profit Factor', metrics.profit_factor],
            ['Tranzacții încheiate', metrics.trade_count],
            ['Cea mai mare scădere', metrics.max_drawdown],
          ].map(([label, value]) => (
            <div key={String(label)}>
              <dt>{String(label)}</dt>
              <dd>{exact(value)}</dd>
            </div>
          ))}
        </dl>
      )}
      <div className="v1-preview-chart">
        <EquityChart points={curve.data.items} total={curve.data.total} currency={currency} />
      </div>
      <p className="v1-preview-note">
        Originea primului flux:{' '}
        {sourceLabels[source.data?.spec.provenance ?? ''] ??
          'UNKNOWN · sursa nu poate fi confirmată'}
        .{' '}
        {Array.isArray(datasetPins) && datasetPins.length > 1
          ? `Sunt ${datasetPins.length} fluxuri; verifică fiecare origine în raport. `
          : ''}
        Un singur experiment · scenariul 1 ·{' '}
        {String(object(summary.data).phase ?? 'etapă neconfirmată')} · costurile și originea datelor
        sunt în protocolul fixat. Rezultatul nu demonstrează profit viitor.
      </p>
      <Link href={resultPath(id)}>Vezi rezultatul și dovezile exacte →</Link>
    </div>
  );
}
