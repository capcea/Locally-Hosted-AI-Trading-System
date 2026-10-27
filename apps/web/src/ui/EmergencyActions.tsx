import { useState } from 'react';
import type { components } from '../generated/api';
import type { Session } from '../management-api';
import { api } from '../management-api';
import { ConfirmDialog } from './Controls';
import { Link } from '../navigation/history';

type Action = 'STOP_NEW_ENTRIES' | 'CLEAR_STOP' | 'FLATTEN';
const actions: { action: Action; title: string; consequence: string }[] = [
  {
    action: 'STOP_NEW_ENTRIES',
    title: 'Oprește intrările noi simulate',
    consequence:
      'Intrările noi sunt oprite pentru acest cont. Pozițiile existente nu se închid automat.',
  },
  {
    action: 'CLEAR_STOP',
    title: 'Revizuiește și deblochează intrările',
    consequence:
      'Datele, contextul, limitele și politica trebuie să fie valide. Serverul verifică fiecare condiție; deblocarea nu permite ordine externe.',
  },
  {
    action: 'FLATTEN',
    title: 'Închide pozițiile simulate',
    consequence:
      'Se încearcă numai închiderea pozițiilor simulate ale acestui cont, folosind cotațiile și lichiditatea disponibile. Închiderea poate rămâne incompletă. Nu închide poziții reale.',
  },
];
export default function EmergencyActions({
  accountId,
  accountName,
  status,
  session,
  onDone,
  onError,
}: {
  accountId: string;
  accountName: string;
  status: components['schemas']['AccountStatus'] | null;
  session: Session;
  onDone: (message: string) => Promise<void>;
  onError: (error: unknown) => void;
}) {
  const [review, setReview] = useState<((typeof actions)[number] & { key: string }) | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <section aria-label="Comenzi distincte de siguranță">
      <h3>Controlul intrărilor și al pozițiilor simulate</h3>
      <p>
        Cont: <strong>{accountName}</strong>. Fiecare acțiune necesită confirmare explicită și MFA
        recent verificat de server.
      </p>
      <Link href="/setari/securitate">Reconfirmă identitatea înaintea unei acțiuni sensibile</Link>
      <div className="emergency-actions">
        {actions.map((a) => (
          <article key={a.action}>
            <h4>{a.title}</h4>
            <p>{a.consequence}</p>
            <button
              type="button"
              className={a.action === 'STOP_NEW_ENTRIES' ? 'danger-button' : 'secondary-button'}
              onClick={() => setReview({ ...a, key: crypto.randomUUID() })}
            >
              {a.title}
            </button>
          </article>
        ))}
      </div>
      <button
        className="secondary-button"
        disabled={busy}
        onClick={() => {
          setBusy(true);
          void api(`/risk/accounts/${accountId}/monitor`, {
            method: 'POST',
            csrf: session.csrf_token,
            body: {},
          })
            .then(() =>
              onDone(
                'Monitorul a verificat datele persistente; verifică motivele și momentul observației.',
              ),
            )
            .catch(onError)
            .finally(() => setBusy(false));
        }}
      >
        Actualizează starea riscului
      </button>
      {review && (
        <ConfirmDialog
          title={review.title}
          onClose={() => {
            if (!busy) setReview(null);
          }}
        >
          <p>
            <strong>Cont: {accountName}</strong> · {accountId} · SIMULATED / DENY_ALL
          </p>
          <p>{review.consequence}</p>
          {!status && (
            <p role="alert">
              UNKNOWN: nu există o revizie verificată a contului. Reîncarcă starea înainte de
              confirmare.
            </p>
          )}
          <form
            aria-label={`Confirmă ${review.action}`}
            onSubmit={(e) => {
              e.preventDefault();
              if (!status || busy) return;
              setBusy(true);
              void api<{ completed: boolean; remaining_positions: number; reasons?: string[] }>(
                `/risk/accounts/${accountId}/emergency`,
                {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: {
                    key: review.key,
                    action: review.action,
                    expected_revision: status.revision,
                    acknowledged_simulated_only: true,
                  },
                },
              )
                .then(async (result) => {
                  const message = result.completed
                    ? 'Operațiune persistentă confirmată. Ordinele externe rămân interzise.'
                    : `Închidere incompletă. Poziții simulate rămase: ${result.remaining_positions}. Verifică incidentele și dovezile.`;
                  setReview(null);
                  await onDone(message);
                })
                .catch(onError)
                .finally(() => setBusy(false));
            }}
          >
            <label className="management-check">
              <input type="checkbox" required />
              Confirm acțiunea afișată pentru acest cont, exclusiv în simulare. Nu închid poziții
              reale.
            </label>
            <button type="submit" className="danger-button" disabled={!status || busy}>
              {busy
                ? 'Așteptăm răspunsul serverului…'
                : `Confirmă ${review.title.toLocaleLowerCase('ro-RO')}`}
            </button>
            {busy && (
              <p role="status">
                Așteptăm confirmarea reală. Închiderea ferestrei nu anulează o solicitare trimisă.
              </p>
            )}
          </form>
        </ConfirmDialog>
      )}
    </section>
  );
}
