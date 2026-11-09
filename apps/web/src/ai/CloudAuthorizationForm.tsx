import { useState } from 'react';
import { cloudDraft, cloudFields } from './cloud-policy';
import type { CloudPolicy } from './cloud-policy';

export function CloudAuthorizationForm({
  passwordAuth = false,
  policy,
  busy,
  save,
}: {
  passwordAuth?: boolean;
  policy: CloudPolicy | null;
  busy: boolean;
  save: (data: FormData) => Promise<boolean>;
}) {
  const [draft, setDraft] = useState(() => cloudDraft(policy));
  return (
    <form
      aria-label="Autorizare OpenRouter"
      onSubmit={async (event) => {
        event.preventDefault();
        if (busy) return;
        const form = event.currentTarget;
        if (await save(new FormData(form))) form.reset();
      }}
    >
      {cloudFields.map(([field, name, label]) => (
        <label key={name}>
          {label}
          <input
            name={name}
            required
            disabled={busy}
            value={draft[field]}
            onChange={(event) =>
              setDraft((previous) => ({ ...previous, [field]: event.target.value }))
            }
            pattern={field === 'upstream_provider' ? '[a-z0-9][a-z0-9_/-]{1,79}' : undefined}
            placeholder={
              field === 'upstream_provider'
                ? 'Tag-ul verificat din catalogul OpenRouter'
                : undefined
            }
            inputMode={field === 'upstream_provider' ? 'text' : 'decimal'}
          />
        </label>
      ))}
      <p>
        Modificările din formular devin active numai după înregistrare și confirmarea de pe server.
        {passwordAuth
          ? 'Salvează formularul pentru a confirma modificările.'
          : 'Reconfirmarea MFA nu salvează automat formularul.'}
      </p>
      <p>
        Rezervările conservatoare includ și solicitările eșuate sau incerte; nu reprezintă factura.
        Configurează separat o limită mică pe cheia din OpenRouter. Fără furnizori alternativi
        automați.
      </p>
      <label>
        <input type="checkbox" name="cloud" required disabled={busy} />
        Aprob explicit procesarea în cloud public OpenRouter.
      </label>
      <label>
        <input type="checkbox" name="upstream_ack" required disabled={busy} />
        Aprob furnizorul din amonte ales și am verificat drepturile asupra datelor.
      </label>
      <label>
        <input type="checkbox" name="cost" required disabled={busy} />
        Am revizuit tarifele, limitele și eventualele costuri.
      </label>
      <label>
        <input type="checkbox" name="limits" required disabled={busy} />
        Înțeleg limitele garanțiilor ZDR și de confidențialitate declarate.
      </label>
      <button disabled={busy}>Înregistrează autorizarea cloud</button>
    </form>
  );
}
