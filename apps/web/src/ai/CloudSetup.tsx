import { useEffect, useState } from 'react';
import { ai } from './api';
import { Evidence } from '../ui/Controls';

export type CloudStatus = {
  operator_enabled: boolean;
  authorization: { id: string; policy: Record<string, unknown> } | null;
  billing_reservations: unknown[];
};
type Mutate = (path: string, body: unknown, method?: string) => Promise<unknown>;

export function CloudSetup({ busy, mutate }: { busy: boolean; mutate: Mutate }) {
  const [state, setState] = useState<CloudStatus | null>(null);
  const [failed, setFailed] = useState(false);
  async function load() {
    try {
      setState(await ai<CloudStatus>('/cloud-policy'));
      setFailed(false);
    } catch {
      setState(null);
      setFailed(true);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  return (
    <section id="ai-destinations" aria-label="Destinație OpenRouter">
      <h4>0. Alege unde se procesează datele</h4>
      <p>
        Furnizorii privați rămân opțiunea implicită. OpenRouter folosește cloud public și un
        furnizor din amonte; aprobarea privată nu este consimțământ pentru cloud.
      </p>
      {failed ? (
        <p role="alert">
          Nu putem citi politica cloud.{' '}
          <button type="button" onClick={() => void load()}>
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
        <details>
          <summary>
            {state.authorization
              ? 'Revizuiește autorizarea OpenRouter'
              : 'Înregistrează destinația OpenRouter'}
          </summary>
          <p>
            Destinație fixă: https://openrouter.ai/api/v1 · protocol OpenAI compatibil. Cerem ZDR și
            fără antrenare, dar nu certificăm independent politica furnizorilor. Nu trimite secrete
            sau date fără drept de utilizare. Salvarea nu trimite nicio cerere cu plată.
          </p>
          <form
            aria-label="Autorizare OpenRouter"
            onSubmit={async (e) => {
              e.preventDefault();
              const data = new FormData(e.currentTarget);
              const result = await mutate('/endpoints/openrouter', {
                upstream_provider: String(data.get('upstream')),
                input_usd_per_million: String(data.get('input_price')),
                output_usd_per_million: String(data.get('output_price')),
                request_usd: String(data.get('request_budget')),
                daily_usd: String(data.get('daily_budget')),
                acknowledged_public_cloud: data.has('cloud'),
                acknowledged_upstream_processing: data.has('upstream_ack'),
                acknowledged_cost: data.has('cost'),
                acknowledged_provider_policy_limits: data.has('limits'),
              });
              if (result) await load();
            }}
          >
            <label>
              Identificatorul exact al furnizorului din amonte
              <input
                name="upstream"
                required
                pattern="[a-z0-9][a-z0-9_/-]{1,79}"
                placeholder="Tag-ul verificat din catalogul OpenRouter"
              />
            </label>
            <label>
              Preț maxim intrare · USD / milion tokenuri
              <input name="input_price" required defaultValue="1" inputMode="decimal" />
            </label>
            <label>
              Preț maxim ieșire · USD / milion tokenuri
              <input name="output_price" required defaultValue="4" inputMode="decimal" />
            </label>
            <label>
              Rezervare maximă / solicitare · USD
              <input name="request_budget" required defaultValue="0.01" inputMode="decimal" />
            </label>
            <label>
              Rezervări maxime / zi UTC · USD
              <input name="daily_budget" required defaultValue="0.50" inputMode="decimal" />
            </label>
            <p>
              Rezervările conservatoare includ și solicitările eșuate sau incerte; nu reprezintă
              factura. Configurează separat o limită mică pe cheia din OpenRouter. Fără furnizori
              alternativi automați.
            </p>
            <label>
              <input type="checkbox" name="cloud" required />
              Aprob explicit procesarea în cloud public OpenRouter.
            </label>
            <label>
              <input type="checkbox" name="upstream_ack" required />
              Aprob furnizorul din amonte ales și am verificat drepturile asupra datelor.
            </label>
            <label>
              <input type="checkbox" name="cost" required />
              Am revizuit tarifele, limitele și eventualele costuri.
            </label>
            <label>
              <input type="checkbox" name="limits" required />
              Înțeleg limitele garanțiilor ZDR și de confidențialitate declarate.
            </label>
            <button disabled={busy}>Înregistrează autorizarea cloud</button>
          </form>
          <Evidence title="Autorizare și rezervări cloud · fără chei" value={state} />
        </details>
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
