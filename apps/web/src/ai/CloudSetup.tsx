import { useCallback, useEffect, useRef, useState } from 'react';
import { ai } from './api';
import { Evidence } from '../ui/Controls';
import { safeError } from '../management-api';
import { CloudAuthorizationForm } from './CloudAuthorizationForm';
import { cloudSaveConfirmed, cloudStatusSchema, cloudSubmission } from './cloud-policy';
import type { CloudStatus } from './cloud-policy';
export type { CloudStatus } from './cloud-policy';

type Mutate = (path: string, body: unknown, method?: string) => Promise<unknown>;

export function CloudPolicySummary({ state }: { state: CloudStatus }) {
  return (
    <p role="status">
      Furnizor aprobat pe server:{' '}
      <strong>
        {state.authorization?.policy.upstream_provider ?? 'Nicio autorizare cloud salvată'}
      </strong>
    </p>
  );
}

export function CloudSetup({
  busy,
  mutate,
  passwordAuth = false,
}: {
  busy: boolean;
  mutate: Mutate;
  passwordAuth?: boolean;
}) {
  const [state, setState] = useState<CloudStatus | null>(null);
  const [failed, setFailed] = useState(false);
  const [reading, setReading] = useState(false);
  const [notice, setNotice] = useState('');
  const reads = useRef({ mounted: true, sequence: 0 });
  const submitting = useRef(false);
  const load = useCallback(async () => {
    const lifecycle = reads.current;
    if (!lifecycle.mounted) return null;
    const current = ++lifecycle.sequence;
    setReading(true);
    try {
      const value = cloudStatusSchema.parse(await ai<unknown>('/cloud-policy'));
      if (!lifecycle.mounted || current !== lifecycle.sequence) return null;
      setState(value);
      setFailed(false);
      return value;
    } catch {
      if (lifecycle.mounted && current === lifecycle.sequence) {
        setFailed(true);
        setState(null);
      }
      return null;
    } finally {
      if (lifecycle.mounted && current === lifecycle.sequence) setReading(false);
    }
  }, []);
  useEffect(() => {
    const lifecycle = reads.current;
    lifecycle.mounted = true;
    void load();
    return () => {
      lifecycle.mounted = false;
      lifecycle.sequence++;
    };
  }, [load]);
  async function save(data: FormData) {
    if (busy || reading || submitting.current) return false;
    submitting.current = true;
    setNotice('');
    try {
      const body = cloudSubmission(data);
      const result = await mutate('/endpoints/openrouter', body);
      if (!reads.current.mounted) return false;
      if (!result) {
        setNotice(
          passwordAuth
            ? 'Salvarea nu este confirmată. Verifică sesiunea și valorile înainte de o nouă înregistrare.'
            : 'Salvarea nu este confirmată. Dacă ai reconfirmat MFA, revizuiește formularul și apasă din nou „Înregistrează autorizarea cloud”.',
        );
        return false;
      }
      const saved = await load();
      if (!reads.current.mounted) return false;
      if (!saved || !saved.authorization || !cloudSaveConfirmed(result, saved, body)) {
        setNotice(
          'Solicitarea a fost acceptată, dar nu putem confirma valorile salvate. Verifică autorizarea de pe server înainte de o nouă înregistrare.',
        );
        return false;
      }
      setNotice(
        `Salvare confirmată de server. Furnizor autorizat: ${saved.authorization.policy.upstream_provider}.`,
      );
      return true;
    } catch (failure) {
      if (reads.current.mounted) setNotice(safeError(failure));
      return false;
    } finally {
      submitting.current = false;
    }
  }
  return (
    <section id="ai-destinations" aria-label="Destinație OpenRouter">
      <h4>0. Alege unde se procesează datele</h4>
      <p>
        Furnizorii privați rămân opțiunea implicită. OpenRouter folosește cloud public și un
        furnizor din amonte; aprobarea privată nu este consimțământ pentru cloud.
      </p>
      {notice && <p role="status">{notice}</p>}
      {failed ? (
        <p role="alert">
          Nu putem citi politica cloud.{' '}
          <button type="button" disabled={busy || reading} onClick={() => void load()}>
            Reîncearcă citirea politicii
          </button>
        </p>
      ) : !state ? (
        <p role="status">Citim autorizarea cloud…</p>
      ) : !state.operator_enabled ? (
        <p>
          OpenRouter este dezactivat de operator. Urmează secțiunea OpenRouter din
          AI_DEPLOYMENT_GUIDE.md: AI_OPENROUTER_ENABLED și destinația exactă din proxy trebuie
          configurate pe API și worker. Nu există acces automat la internet.
        </p>
      ) : (
        <>
          <CloudPolicySummary state={state} />
          <button type="button" disabled={busy || reading} onClick={() => void load()}>
            {reading ? 'Citim autorizarea salvată…' : 'Verifică autorizarea salvată'}
          </button>
          <details>
            <summary>
              {state.authorization
                ? 'Revizuiește autorizarea OpenRouter'
                : 'Înregistrează destinația OpenRouter'}
            </summary>
            <p>
              Destinație fixă: https://openrouter.ai/api/v1 · protocol OpenAI compatibil. Cerem ZDR
              și fără antrenare, dar nu certificăm independent politica furnizorilor. Nu trimite
              secrete sau date fără drept de utilizare. Salvarea nu trimite nicio cerere cu plată.
            </p>
            <CloudAuthorizationForm
              key={state.authorization?.id ?? 'new'}
              policy={state.authorization?.policy ?? null}
              passwordAuth={passwordAuth}
              busy={busy || reading}
              save={save}
            />
            <Evidence title="Autorizare și rezervări cloud · fără chei" value={state} />
          </details>
        </>
      )}
    </section>
  );
}

export function CredentialEditor({
  connection,
  busy,
  mutate,
  close,
}: {
  connection: string;
  busy: boolean;
  mutate: Mutate;
  close: () => void;
}) {
  return (
    <form
      aria-label="Cheie OpenRouter"
      onSubmit={async (e) => {
        e.preventDefault();
        const form = e.currentTarget;
        const token = String(new FormData(form).get('api_key') ?? '');
        form.reset();
        close();
        await mutate(`/connections/${connection}/credential`, { api_key: token });
      }}
    >
      <p>
        Cheia este criptată pe server. Nu este salvată în browser și nu poate fi recitită. După
        schimbare, verifică din nou modelele. Capturile și urmele de autentificare rămân
        dezactivate.
      </p>
      <label>
        Cheie API OpenRouter
        <input
          type="password"
          name="api_key"
          autoComplete="off"
          required
          minLength={16}
          maxLength={4096}
        />
      </label>
      <button disabled={busy}>Salvează cheia numai pe server</button>
      <button type="button" onClick={close}>
        Renunță
      </button>
    </form>
  );
}
