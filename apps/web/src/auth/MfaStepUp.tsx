import { useState } from 'react';
import { api, parseSession, safeError } from '../management-api';
import { ConfirmDialog, Field } from '../ui/Controls';
import { useAuth } from './AuthProvider';
import { MFA_MESSAGE } from './lifecycle';

export function AuthFeedback() {
  const { mfaRequired, requestMfa, notice } = useAuth();
  return (
    <>
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {mfaRequired && (
        <p role="alert" className="notice">
          {MFA_MESSAGE}{' '}
          <button type="button" onClick={requestMfa}>
            Reconfirmă MFA
          </button>
        </p>
      )}
    </>
  );
}

function Challenge() {
  const { session, setSession, dismissMfa, announce } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  return (
    <ConfirmDialog
      title="Reconfirmă autentificarea în doi pași"
      onClose={() => {
        if (!busy) dismissMfa();
      }}
    >
      <p>{MFA_MESSAGE}</p>
      <p>
        Folosește parola curentă și un cod nou din autentificator. Acțiunea inițială nu va fi
        trimisă automat.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <form
        className="management-form"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!session || busy) return;
          const form = event.currentTarget;
          const data = new FormData(form);
          form.reset();
          setBusy(true);
          setError('');
          try {
            const value = parseSession(
              await api('/auth/reauthenticate', {
                method: 'POST',
                csrf: session.csrf_token,
                body: { password: String(data.get('password')), code: String(data.get('code')) },
              }),
            );
            setSession(value);
            announce(
              'Autentificarea în doi pași a fost reconfirmată. Revizuiește și retrimite acțiunea inițială.',
            );
          } catch (failure) {
            setError(safeError(failure));
          } finally {
            setBusy(false);
          }
        }}
      >
        <Field
          label="Parola curentă"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          disabled={busy}
        />
        <Field
          label="Cod MFA nou"
          name="code"
          type="password"
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="[0-9]{6}"
          maxLength={6}
          required
          disabled={busy}
        />
        <button disabled={busy}>{busy ? 'Verificăm…' : 'Reconfirmă autentificarea'}</button>
      </form>
    </ConfirmDialog>
  );
}

export function MfaStepUp() {
  const { session, stepUpOpen } = useAuth();
  return stepUpOpen && session?.state === 'FULL' ? <Challenge key={session.session_id} /> : null;
}
