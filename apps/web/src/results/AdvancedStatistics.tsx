import { useState } from 'react';
import { api, safeError } from '../management-api';
import type { Session } from '../management-api';
import { Evidence, Field } from '../ui/Controls';
import { object } from './ResultView';
import { Link } from '../navigation/history';

export default function AdvancedStatistics({
  session,
  experimentId,
  trial,
}: {
  session: Session;
  experimentId: string;
  trial: number;
}) {
  const [answer, setAnswer] = useState<unknown>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <details>
      <summary>Statistici avansate · selecție repetată</summary>
      <p>
        Deflated Sharpe depinde de ipotezele declarate despre încercări independente. Nu reprezintă
        probabilitatea de a câștiga bani și nu autorizează promovarea.
      </p>
      {session.user.role === 'OWNER' ? (
        <form
          aria-label="Ipoteze Deflated Sharpe"
          onSubmit={(e) => {
            e.preventDefault();
            if (busy) return;
            const f = new FormData(e.currentTarget);
            setError('');
            setAnswer(null);
            setBusy(true);
            void api(`/research/experiments/${experimentId}/statistics/deflated-sharpe`, {
              method: 'POST',
              csrf: session.csrf_token,
              body: {
                trial,
                independent_trials: Number(f.get('independent')),
                trial_sharpe_variance: String(f.get('variance')),
                independence_model_reference: String(f.get('reference')),
                acknowledged_assumption_not_certification: true,
              },
            })
              .then(setAnswer)
              .catch((e) => setError(safeError(e)))
              .finally(() => setBusy(false));
          }}
        >
          <Field
            name="independent"
            label="Încercări independente conform modelului declarat"
            type="number"
            min={2}
            max={1000000}
            required
          />
          <Field name="variance" label="Varianța Sharpe estimată conform modelului" required />
          <Field
            name="reference"
            label="Sursa și justificarea modelului de independență"
            minLength={10}
            maxLength={1000}
            required
          />
          <label className="management-check">
            <input type="checkbox" required />
            Confirm că acestea sunt ipoteze declarate, nu o certificare a independenței.
          </label>
          <Link href="/setari/securitate">Reconfirmă MFA dacă este necesar</Link>
          <button disabled={busy}>Evaluează ipotezele declarate</button>
        </form>
      ) : (
        <p>
          Evaluarea necesită proprietar și MFA recent; drepturile nu se obțin prin modul avansat.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {answer !== null && (
        <>
          <p>
            {object(answer).value === null
              ? 'Nu există suficiente randamente zilnice nedegenerate pentru acest indicator.'
              : 'Valoare calculată sub ipotezele declarate, fără eligibilitate de tranzacționare.'}
          </p>
          <Evidence value={answer} />
        </>
      )}
    </details>
  );
}
