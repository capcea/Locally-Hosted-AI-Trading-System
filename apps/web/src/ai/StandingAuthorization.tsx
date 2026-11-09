import { useCallback, useEffect, useRef, useState } from 'react';
import { ai, roles, roleLabels } from './api';
import type { Connection } from './api';
import { Evidence } from '../ui/Controls';
import { safeError } from '../management-api';

type Policy = {
  connection_ids: string[];
  roles: string[];
  data_categories: string[];
  operations: string[];
  request_usd: string;
  daily_usd: string;
  monthly_usd: string;
  grants: unknown[];
};
export type Standing = {
  authorization: { id: string; revision: number; active: boolean; policy: Policy } | null;
};
export function StandingAuthorization({
  passwordAuth = false,
  connections,
  busy,
  mutate,
}: {
  passwordAuth?: boolean;
  connections: Connection[];
  busy: boolean;
  mutate: (path: string, body: unknown) => Promise<unknown>;
}) {
  const [state, setState] = useState<Standing | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const reads = useRef({ mounted: true, sequence: 0 });
  const load = useCallback(async () => {
    const lifecycle = reads.current,
      current = ++lifecycle.sequence;
    try {
      const value = await ai<Standing>('/standing-authorization');
      if (!lifecycle.mounted || current !== lifecycle.sequence) return null;
      setState(value);
      setError('');
      return value;
    } catch (failure) {
      if (lifecycle.mounted && current === lifecycle.sequence) {
        setState(null);
        setError(safeError(failure));
      }
      return null;
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
  const row = state?.authorization;
  const policy = row?.policy;
  return (
    <section className="panel" aria-label="Autorizări permanente">
      <h3>Autorizări permanente</h3>
      <p>
        Autorizează cercetarea AI 24/7, până la revocare, numai în scopul și limitele de mai jos.
        Autentificarea, verificarea modelelor și protecțiile datelor rămân obligatorii. Această
        aprobare nu pornește un agent automat.
      </p>
      <p>
        Fără ordine către brokeri, modificări ale riscului, execuție de cod sau publicare. Datele
        temporare și răspunsurile criptate expiră conform politicii conexiunii.
      </p>
      <p role="status">
        {state
          ? row?.active
            ? `Activă · versiunea ${row.revision}`
            : 'Nicio autorizare permanentă activă.'
          : error
            ? 'Autorizarea nu poate fi citită.'
            : 'Citim autorizarea…'}
      </p>
      {error && (
        <p role="alert">
          {error}{' '}
          <button type="button" onClick={() => void load()}>
            Reîncearcă
          </button>
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {policy && (
        <>
          <p>
            Limite autorizate: {policy.request_usd} USD / solicitare · {policy.daily_usd} USD / zi ·{' '}
            {policy.monthly_usd} USD / lună. Se aplică și limitele mai stricte ale politicii
            OpenRouter.
          </p>
          <p>
            Bugetele folosesc rezervări conservatoare, inclusiv eșecuri și rezultate incerte;
            factura furnizorului poate diferi. Resetare la 00:00 UTC, respectiv prima zi a lunii.
          </p>
          <Evidence title="Domeniul exact și destinațiile fixate" value={row} />
        </>
      )}
      {row?.active && (
        <button
          type="button"
          disabled={busy}
          onClick={async () => {
            const result = await mutate('/standing-authorization/revoke', {});
            if (result) {
              const confirmed = await load();
              if (confirmed?.authorization?.active !== false) {
                setNotice(
                  'Revocarea nu poate fi confirmată. Recitește autorizarea înainte de altă acțiune.',
                );
                return;
              }
              setNotice(
                'Revocare înregistrată. Solicitările noi necesită o nouă autorizare; worker-ul revalidează lucrul activ.',
              );
            }
          }}
        >
          Revocă autorizarea permanentă
        </button>
      )}
      {state && (
        <details>
          <summary>
            {row?.active
              ? 'Revizuiește sau schimbă autorizarea'
              : 'Activează autorizarea permanentă'}
          </summary>
          <form
            key={row?.id ?? 'new'}
            aria-label="Autorizare permanentă AI"
            onSubmit={async (event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              setNotice('');
              const result = await mutate('/standing-authorization', {
                version: 'ai-standing-v1',
                connection_ids: data.getAll('connection_ids'),
                roles: data.getAll('roles'),
                data_categories: data.getAll('data_categories'),
                operations: data.getAll('operations'),
                request_usd: data.get('request_usd'),
                daily_usd: data.get('daily_usd'),
                monthly_usd: data.get('monthly_usd'),
              });
              if (result) {
                const confirmed = await load();
                const expected = (result as Standing).authorization;
                if (
                  !expected ||
                  confirmed?.authorization?.id !== expected.id ||
                  confirmed.authorization.active !== true
                ) {
                  setNotice(
                    'Activarea nu poate fi confirmată. Recitește autorizarea înainte de o nouă activare.',
                  );
                  return;
                }
                setNotice(
                  'Autorizarea a fost înregistrată. Cererile din AI Center folosesc domeniul aprobat, fără bife repetate.',
                );
              } else
                setNotice(
                  passwordAuth
                    ? 'Activarea nu este confirmată. Verifică sesiunea și reîncearcă înregistrarea.'
                    : 'Activarea nu este confirmată. După reconfirmarea MFA, revizuiește și apasă din nou butonul de activare.',
                );
            }}
          >
            <label>
              Conexiuni aprobate (selecție multiplă)
              <select
                name="connection_ids"
                aria-label="Conexiuni aprobate (selecție multiplă)"
                multiple
                required
                defaultValue={policy?.connection_ids ?? []}
                disabled={busy}
              >
                {connections
                  .filter((c) => c.enabled)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} · {c.provider ?? 'privat'} · {c.endpoint_id ?? c.id}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Roluri permise
              <select
                name="roles"
                aria-label="Roluri permise"
                multiple
                required
                defaultValue={policy?.roles ?? roles}
                disabled={busy}
              >
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {roleLabels[r]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Categorii de date permise
              <select
                name="data_categories"
                aria-label="Categorii de date permise"
                multiple
                required
                defaultValue={policy?.data_categories ?? ['documentation', 'strategy']}
                disabled={busy}
              >
                {[
                  ['documentation', 'Documentație'],
                  ['strategy', 'Strategii revizuite'],
                  ['dataset', 'Date istorice proprii admise'],
                  ['experiment', 'Experimente proprii'],
                  ['ai_artifact', 'Răspunsuri AI proprii'],
                ].map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Operațiuni permise
              <select
                name="operations"
                aria-label="Operațiuni permise"
                multiple
                required
                defaultValue={policy?.operations ?? ['INFER', 'PROBE', 'DISCOVER']}
                disabled={busy}
              >
                <option value="INFER">Analize AI</option>
                <option value="PROBE">Verificări de model (pot avea costuri)</option>
                <option value="DISCOVER">Citirea catalogului</option>
              </select>
            </label>
            {(
              [
                ['request_usd', 'Limită pe solicitare · USD', '0.01'],
                ['daily_usd', 'Limită zilnică · USD', '0.50'],
                ['monthly_usd', 'Limită lunară · USD', '5'],
              ] as const
            ).map(([name, label, value]) => (
              <label key={name}>
                {label}
                <input
                  name={name}
                  required
                  inputMode="decimal"
                  defaultValue={policy?.[name] ?? value}
                  disabled={busy}
                />
              </label>
            ))}
            <p>
              Prin activare confirmi dreptul de a trimite categoriile selectate și procesarea lor la
              destinațiile aprobate, inclusiv cloud dacă ai selectat OpenRouter. Aprobi costurile
              numai în limitele configurate. Schimbarea politicii cloud sau destinației necesită o
              nouă revizuire. Nicio cerere cu plată nu pornește prin activare.
            </p>
            <button disabled={busy || !connections.some((c) => c.enabled)}>
              {passwordAuth
                ? 'Activează autorizarea permanentă'
                : 'Activează autorizarea permanentă cu MFA'}
            </button>
            {!connections.some((c) => c.enabled) && <p>Creează mai întâi o conexiune aprobată.</p>}
          </form>
        </details>
      )}
    </section>
  );
}

export function standingAction(
  state: Standing | null | undefined,
  operation: string,
  connection: string,
): string | undefined {
  const row = state?.authorization;
  return row?.active &&
    row.policy.operations.includes(operation) &&
    row.policy.roles.includes('LIGHTWEIGHT') &&
    row.policy.connection_ids.includes(connection)
    ? row.id
    : undefined;
}
