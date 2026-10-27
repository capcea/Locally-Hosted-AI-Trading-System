import { useState } from 'react';
import type { components } from './generated/api';
import { api, safeError } from './management-api';
import type { RecordItem, Session } from './management-api';
import type { JobSummary } from './home/HomePage';
import { Evidence } from './ui/Controls';
import { Link, navigate } from './navigation/history';
import { progressPath } from './navigation/routes';

type Plan = components['schemas']['packages__research__contracts__ExperimentInput'];
type Dataset = components['schemas']['DatasetView'];
type Seal = { id: string; dataset_id: string; prior_exposure: string };
export default function FinalEvaluation({
  session,
  accounts,
  datasets,
  seals,
  jobs,
  account,
  dataset,
  setAccount,
  setDataset,
  onChanged,
}: {
  session: Session;
  accounts: RecordItem[];
  datasets: Dataset[];
  seals: Seal[];
  jobs: JobSummary[];
  account: string;
  dataset: string;
  setAccount: (id: string) => void;
  setDataset: (id: string) => void;
  onChanged: () => Promise<void>;
}) {
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [base, setBase] = useState<Plan | null>(null);
  const [frozen, setFrozen] = useState<Plan | null>(null);
  const [released, setReleased] = useState<{ id: string; plan: Plan } | null>(null);
  const [busy, setBusy] = useState(false);
  const act = async (work: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await work();
    } catch (e) {
      setError(safeError(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel" aria-label="Evaluare finală protejată">
      <h2>Evaluare finală protejată · numai proprietar</h2>
      <p>
        Rezervarea restricționează accesul obișnuit, inclusiv prin seturi suprapuse ale aceluiași
        proprietar. Expunerea anterioară este necunoscută: nu certificăm că datele sunt nevăzute.
        Este permisă o singură evaluare cu configurația înghețată.
      </p>
      <Link href="/setari/securitate">Reconfirmă MFA înainte de autorizare</Link>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <details>
        <summary>1. Rezervă intenționat o perioadă</summary>
        <form
          aria-label="Sigilează holdout"
          onSubmit={(e) => {
            e.preventDefault();
            const fields = new FormData(e.currentTarget);
            void act(async () => {
              await api('/research/holdouts', {
                method: 'POST',
                csrf: session.csrf_token,
                body: {
                  dataset_id: dataset,
                  reason: String(fields.get('reason')),
                  acknowledged_prior_exposure_unknown: true,
                },
              });
              setNotice('Perioada a fost rezervată. Accesul obișnuit este blocat.');
              await onChanged();
            });
          }}
        >
          <label>
            Contul testului
            <select
              aria-label="Contul testului"
              value={account}
              onChange={(e) => {
                setAccount(e.target.value);
                setDataset('');
              }}
              required
            >
              <option value="">Alege…</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.data.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Set de date principal
            <select
              aria-label="Set de date principal"
              value={dataset}
              onChange={(e) => setDataset(e.target.value)}
              required
            >
              <option value="">Alege un set VALID…</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.symbol} · {d.spec.start} → {d.spec.end}
                </option>
              ))}
            </select>
          </label>
          <label>
            Motivul rezervării
            <input name="reason" required minLength={10} maxLength={1000} />
          </label>
          <label className="management-check">
            <input type="checkbox" required />
            Confirm că expunerea anterioară este necunoscută și accesul obișnuit va fi
            restricționat.
          </label>
          <button disabled={busy || !dataset}>Rezervă perioada selectată</button>
          {!dataset && (
            <p>Alege un set admis. Nu citim rânduri protejate pentru a facilita selecția.</p>
          )}
        </form>
      </details>
      <h3>2. Alege o configurație deja înregistrată</h3>
      <p>
        Preluăm setările unui test existent, fără a citi rândurile perioadei protejate. Alegerea nu
        constituie autorizare. Regulile serverului verifică fiecare flux și interval.
      </p>
      <label>
        Test de referință
        <select
          aria-label="Test de referință pentru evaluarea finală"
          disabled={busy || !!released}
          onChange={(e) => {
            setBase(null);
            setFrozen(null);
            if (e.target.value)
              void act(async () => {
                const p = await api<{ plan: Plan }>(
                  `/research/experiments/${e.target.value}/provenance`,
                );
                setBase(p.plan);
              });
          }}
        >
          <option value="">Alege…</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.name} · {j.id}
            </option>
          ))}
        </select>
      </label>
      {base && !released && (
        <form
          aria-label="Pregătește configurația finală"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            const index = Number(f.get('parameter'));
            setFrozen({
              ...base,
              key: crypto.randomUUID(),
              name: String(f.get('name')),
              phase: 'FINAL_HOLDOUT',
              engine: 'EVENT',
              parameters: [base.parameters[index]],
              cost_multipliers: ['1'],
              holdout_release_id: null,
            });
          }}
        >
          <label>
            Denumire evaluare finală
            <input
              name="name"
              required
              maxLength={120}
              defaultValue={`${base.name.slice(0, 90)} · evaluare finală`}
            />
          </label>
          <label>
            Configurația de parametri
            <select name="parameter" aria-label="Configurația finală de parametri">
              {base.parameters.map((_, i) => (
                <option key={i} value={i}>
                  Configurația {i + 1} din testul sursă
                </option>
              ))}
            </select>
          </label>
          <p>
            Un singur scenariu EVENT, costurile de bază (multiplicator1), aceleași
            date/cronologie/risc și ipoteze. Nu schimbăm faptele financiare și nu presupunem
            independența datelor.
          </p>
          <Evidence value={base} />
          <button>Pregătește revizuirea finală</button>
        </form>
      )}
      {frozen && !released && (
        <form
          aria-label="Eliberează evaluarea finală"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            void act(async () => {
              const release = await api<{ id: string }>(
                `/research/holdouts/${String(f.get('seal'))}/release`,
                {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: {
                    experiment: frozen,
                    acknowledged_single_final_evaluation: true,
                    acknowledged_not_certified_untouched: true,
                  },
                },
              );
              setReleased({ id: release.id, plan: frozen });
              setNotice(
                'Autorizarea unică a fost înregistrată. Urmează înregistrarea exact a configurației autorizate. Nu autoriza o altă variantă.',
              );
            });
          }}
        >
          <h3>3. Revizuiește și autorizează o singură evaluare</h3>
          <label>
            Holdout sigilat
            <select aria-label="Holdout sigilat" name="seal" required>
              <option value="">Alege perioada protejată…</option>
              {seals.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.dataset_id} · {s.id}
                </option>
              ))}
            </select>
          </label>
          <p>
            Cont: {frozen.source_account_id}; strategie: {frozen.strategy}; perioadă:{' '}
            {frozen.chronology.start} → {frozen.chronology.end}; parametri: un singur scenariu.
          </p>
          <Evidence title="Configurația exactă înghețată" value={frozen} />
          <label className="management-check">
            <input type="checkbox" required />
            Autorizez o singură evaluare finală; rezultatul nu va fi folosit pentru tuning repetat
            prezentat drept test independent.
          </label>
          <label className="management-check">
            <input type="checkbox" required />
            Înțeleg că expunerea anterioară nu este certificată și că această evaluare nu permite
            promovarea sau ordinele externe.
          </label>
          <button disabled={busy}>Autorizează evaluarea finală unică</button>
        </form>
      )}
      {released && (
        <section className="notice">
          <h3>4. Înregistrează configurația autorizată</h3>
          <p>
            Autorizare: {released.id}. Nu modificăm configurația înghețată. Dacă răspunsul la
            înregistrare este incert, aceeași configurație și aceeași cheie sunt retransmise.
          </p>
          <button
            disabled={busy}
            onClick={() =>
              void act(async () => {
                const job = await api<{ id: string }>('/research/experiments', {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: { ...released.plan, holdout_release_id: released.id },
                });
                navigate(progressPath(job.id));
              })
            }
          >
            Înregistrează evaluarea autorizată
          </button>
          <Evidence value={released} />
        </section>
      )}
      <details>
        <summary>Avansat · configurație completă sau reluare cu autorizare existentă</summary>
        <p>
          Contractul exact rămâne disponibil. O autorizare existentă poate fi inspectată în
          istoricul verificabil. Serverul refuză altă configurație sau reutilizarea interzisă; nu
          genera o nouă autorizare pentru a ocoli refuzul.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            void act(async () => {
              const experiment = JSON.parse(String(f.get('frozen'))) as Plan;
              if (experiment.phase !== 'FINAL_HOLDOUT') throw new Error('Invalid final phase');
              const id = String(f.get('release'));
              if (id) {
                setReleased({ id, plan: experiment });
              } else {
                setFrozen(experiment);
              }
            });
          }}
        >
          <label>
            Configurație finală înghețată (JSON)
            <textarea name="frozen" required maxLength={250000} />
          </label>
          <label>
            Identificator autorizare existentă (opțional)
            <input name="release" pattern="[0-9a-fA-F-]{36}" />
          </label>
          <button disabled={busy}>Pregătește revizuirea configurației exacte</button>
        </form>
      </details>
      <Evidence title="Perioade protejate · maximum100 din contractul curent" value={seals} />
    </section>
  );
}
