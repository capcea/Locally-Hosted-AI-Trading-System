import { useCallback, useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { api, ApiError, parseSession, safeError } from './management-api';
import { Link } from './navigation/history';
import { ConfirmDialog, Field as InputField, SelectField } from './ui/Controls';
import { useAuth } from './auth/AuthProvider';
import type {
  AuditEvent,
  RecordBody,
  RecordItem,
  RecordPage,
  Session,
  User,
} from './management-api';
import { managementRo as t } from './management-locale';
import MarketData from './MarketData';
import BrokerCenter from './BrokerCenter';
import RiskCenter from './RiskCenter';
import StrategyLab from './StrategyLab';

export type Tab = keyof typeof t.tabs;
type FieldName = keyof typeof t.fields;
type Options = { value: string; label: string }[];

function Field({
  name,
  label,
  type = 'text',
  value,
  onChange,
  options,
  required = true,
}: {
  name: string;
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  options?: Options;
  required?: boolean;
}) {
  return options ? (
    <SelectField
      label={label}
      name={name}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
    >
      <option value="">Alege…</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </SelectField>
  ) : (
    <InputField
      name={name}
      label={label}
      type={type}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
      autoComplete={
        name === 'bootstrap_token'
          ? 'off'
          : name === 'username'
            ? 'username'
            : name === 'code'
              ? 'one-time-code'
              : type === 'password'
                ? name.includes('new')
                  ? 'new-password'
                  : 'current-password'
                : undefined
      }
    />
  );
}

function ErrorNotice({ error }: { error: string | null }) {
  return error ? (
    <p role="alert" className="error-banner">
      {error}
    </p>
  ) : null;
}
function message(error: unknown) {
  return safeError(error);
}

export function Authentication({
  session,
  setSession,
}: {
  session: Session | null;
  setSession: (session: Session | null) => void;
}) {
  const [initialized, setInitialized] = useState<boolean | null>(null);
  const [available, setAvailable] = useState(false);
  const [fields, setFields] = useState({
    username: '',
    password: '',
    display_name: '',
    bootstrap_token: '',
    code: '',
  });
  const [enrollment, setEnrollment] = useState<{ secret: string; provisioning_uri: string } | null>(
    null,
  );
  const [recovery, setRecovery] = useState<string[]>([]);
  const [pendingSession, setPendingSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    api<{ initialized: boolean; setup_available: boolean }>('/auth/status')
      .then((value) => {
        if (live) {
          setInitialized(value.initialized);
          setAvailable(value.setup_available);
        }
      })
      .catch((error) => {
        if (live) setError(message(error));
      });
    return () => {
      live = false;
    };
  }, []);
  const act = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  };
  const authenticate = (event: FormEvent) => {
    event.preventDefault();
    void act(async () => {
      const result = await api<unknown>(initialized ? '/auth/login' : '/auth/bootstrap', {
        method: 'POST',
        body: initialized
          ? { username: fields.username, password: fields.password }
          : { ...fields, code: undefined },
      });
      setFields({ ...fields, password: '', bootstrap_token: '', code: '' });
      setSession(parseSession(result));
    });
  };
  const confirm = (recover = false) =>
    act(async () => {
      if (!session) return;
      if (session.state === 'ENROLLMENT') {
        const result = await api<{ session: unknown; recovery_codes: string[] }>(
          '/auth/mfa/confirm',
          { method: 'POST', csrf: session.csrf_token, body: { code: fields.code } },
        );
        setRecovery(result.recovery_codes);
        setPendingSession(parseSession(result.session));
        setEnrollment(null);
      } else {
        const result = await api<unknown>(recover ? '/auth/mfa/recover' : '/auth/mfa/verify', {
          method: 'POST',
          csrf: session.csrf_token,
          body: { code: fields.code },
        });
        setSession(parseSession(result));
      }
      setFields({ ...fields, code: '' });
    });
  if (recovery.length)
    return (
      <section className="panel management-panel">
        <h2>Coduri de recuperare</h2>
        <p>
          Păstrează-le într-un manager de parole. Fiecare cod poate fi folosit o singură dată,
          împreună cu parola.
        </p>
        <div className="recovery-codes">
          {recovery.map((code) => (
            <code key={code}>{code}</code>
          ))}
        </div>
        <button
          className="secondary-button"
          onClick={() => {
            setRecovery([]);
            setSession(pendingSession);
            setPendingSession(null);
          }}
        >
          Am salvat codurile
        </button>
      </section>
    );
  return (
    <section className="panel management-panel">
      <h2>{session ? 'Verificare în doi pași' : initialized ? t.login : t.setup}</h2>
      <ErrorNotice error={error} />
      {!session ? (
        <form onSubmit={authenticate} className="management-form">
          <Field
            name="username"
            label={t.username}
            value={fields.username}
            onChange={(username) => setFields({ ...fields, username })}
          />
          <Field
            name="password"
            label={t.password}
            type="password"
            value={fields.password}
            onChange={(password) => setFields({ ...fields, password })}
          />
          {!initialized && (
            <>
              <Field
                name="display_name"
                label={t.displayName}
                value={fields.display_name}
                onChange={(display_name) => setFields({ ...fields, display_name })}
              />
              <Field
                name="bootstrap_token"
                label={t.bootstrapToken}
                type="password"
                value={fields.bootstrap_token}
                onChange={(bootstrap_token) => setFields({ ...fields, bootstrap_token })}
              />
              <p>
                Codul privat este generat local de administrator. Parola trebuie să aibă cel puțin
                15 caractere.
              </p>
            </>
          )}
          <button
            className="secondary-button"
            disabled={busy || initialized === null || (!initialized && !available)}
          >
            {initialized ? 'Continuă cu parola' : 'Creează proprietarul'}
          </button>
          {initialized === false && !available && (
            <p>
              Configurarea proprietarului nu este disponibilă. Administratorul trebuie să
              pregătească identitatea și codul privat pe server; nu le presupunem.
            </p>
          )}
        </form>
      ) : (
        <>
          <p>
            {session.user.display_name} · {session.user.role}. Accesul la administrare necesită MFA.
          </p>
          {session.state === 'ENROLLMENT' && !enrollment && (
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  setEnrollment(
                    await api('/auth/mfa/enroll', {
                      method: 'POST',
                      csrf: session.csrf_token,
                      body: {},
                    }),
                  );
                })
              }
            >
              Configurează autentificatorul
            </button>
          )}
          {enrollment && (
            <div className="enrollment-secret">
              <p>Adaugă manual această cheie în aplicația de autentificare TOTP:</p>
              <code>{enrollment.secret}</code>
              <p>Trade Research · cod de 6 cifre · perioadă de 30 secunde</p>
            </div>
          )}
          {(enrollment || session.state === 'MFA') && (
            <form
              className="management-form"
              onSubmit={(event) => {
                event.preventDefault();
                void confirm();
              }}
            >
              <Field
                name="code"
                label={t.code}
                value={fields.code}
                onChange={(code) => setFields({ ...fields, code })}
              />
              <button className="secondary-button" disabled={busy}>
                Verifică MFA
              </button>
              {session.state === 'MFA' && (
                <button
                  type="button"
                  className="text-button"
                  disabled={busy}
                  onClick={() => void confirm(true)}
                >
                  Folosește cod de recuperare
                </button>
              )}
            </form>
          )}
        </>
      )}
    </section>
  );
}

function RecordForm({
  kind,
  fields,
  selections = {},
  session,
  editing,
  onSaved,
}: {
  kind: RecordBody['kind'];
  fields: FieldName[];
  selections?: Partial<Record<FieldName, Options>>;
  session: Session;
  editing?: RecordItem | null;
  onSaved: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    if (!editing) return {};
    return Object.fromEntries(
      Object.entries(editing.data).map(([key, value]) => [
        key,
        Array.isArray(value) ? String(value[0] ?? '') : String(value ?? ''),
      ]),
    );
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { kind, ...values };
      if (kind === 'accounts') {
        body.environment = 'SIMULATED';
        body.program_id = values.program_id || null;
        body.archived = editing?.data.kind === 'accounts' ? editing.data.archived : false;
      }
      if (kind === 'policies') {
        body.version = Number(values.version);
        body.source_references = [values.source_references];
        body.effective_at = new Date(values.effective_at).toISOString();
        body.expires_at = new Date(values.expires_at).toISOString();
      }
      const path = `/records/${kind}${editing ? `/${editing.id}?expected_revision=${editing.revision}` : ''}`;
      await api(path, { method: editing ? 'PUT' : 'POST', body, csrf: session.csrf_token });
      setValues({});
      onSaved();
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form className="management-form" onSubmit={(event) => void submit(event)}>
      <h3>{editing ? 'Editează înregistrarea' : 'Adaugă înregistrare'}</h3>
      <ErrorNotice error={error} />
      <Field
        name="source"
        label="Originea înregistrării"
        value={values.source ?? 'USER_ENTERED'}
        options={[
          { value: 'USER_ENTERED', label: 'Înregistrare introdusă de utilizator' },
          { value: 'SYNTHETIC_TEST_FIXTURE', label: 'Date sintetice de test' },
        ]}
        onChange={(source) => setValues({ ...values, source })}
      />
      {fields.map((field) => (
        <Field
          key={field}
          name={field}
          label={t.fields[field]}
          value={values[field] ?? ''}
          options={selections[field]}
          required={!(kind === 'accounts' && field === 'program_id')}
          type={field.endsWith('_at') ? 'datetime-local' : 'text'}
          onChange={(value) => setValues({ ...values, [field]: value })}
        />
      ))}
      <button className="secondary-button" disabled={busy || session.user.role === 'VIEWER'}>
        {t.save}
      </button>
      {editing && (
        <button className="text-button" type="button" onClick={onSaved}>
          {t.cancel}
        </button>
      )}
    </form>
  );
}

function Cards({
  items,
  actions,
}: {
  items: RecordItem[];
  actions?: (item: RecordItem) => ReactNode;
}) {
  return (
    <div className="management-cards">
      {items.length === 0 && <p>{t.empty}</p>}
      {items.map((item) => (
        <article className="management-record" key={item.id}>
          <h3>{item.data.name}</h3>
          {item.data.kind === 'accounts' && (
            <>
              <p>
                Capital declarat pentru simulare, nu sold de broker. Siguranța și politica se
                verifică separat.
              </p>
              <Link href={`/conturi/${item.id}/siguranta`}>Vezi siguranța {item.data.name}</Link>
            </>
          )}
          <p className="record-source">
            {item.data.source === 'SYNTHETIC_TEST_FIXTURE'
              ? 'Date sintetice de test'
              : 'Înregistrare introdusă de utilizator'}{' '}
            · rev. {item.revision}
          </p>
          {Object.entries(item.data)
            .filter(([key]) => !['kind', 'name', 'source'].includes(key))
            .map(([key, value]) => (
              <p key={key}>
                <strong>{t.fields[key as FieldName] ?? key}: </strong>
                <span>{Array.isArray(value) ? value.join(', ') : String(value ?? '—')}</span>
              </p>
            ))}
          {item.state && (
            <p>
              <strong>Stare: {item.state}</strong>
            </p>
          )}
          {item.policy_attestation && (
            <p>
              <strong>{t.attestation}: </strong>
              {item.policy_attestation.verified_at
                ? new Date(item.policy_attestation.verified_at).toLocaleString('ro-RO')
                : t.unverified}
              {' · '}
              {t.verifiedBy}: {item.policy_attestation.verified_by ?? '—'}
              {' · '}
              {t.scopeRevisions}: {item.policy_attestation.account_revision}/
              {item.policy_attestation.program_revision}
            </p>
          )}
          {actions?.(item)}
        </article>
      ))}
    </div>
  );
}

export function Security({
  session,
  setSession,
  mode = 'personal',
}: {
  session: Session;
  setSession: (value: Session | null) => void;
  mode?: 'personal' | 'users';
}) {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState('');
  const [fields, setFields] = useState({
    password: '',
    new_password: '',
    code: '',
    username: '',
    display_name: '',
    role: 'VIEWER',
  });
  const [users, setUsers] = useState<User[]>([]);
  const load = useCallback(async () => {
    if (session.user.role === 'OWNER') setUsers(await api<User[]>('/auth/users'));
  }, [session.user.role]);
  useEffect(() => {
    void load().catch((error) => setError(message(error)));
  }, [load]);
  const [review, setReview] = useState<{
    operation: () => Promise<void>;
    consequence: string;
  } | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const act = async (operation: () => Promise<void>, consequence?: string) => {
    if (consequence) {
      setReview({ operation, consequence });
      return;
    }
    setError(null);
    setNotice('');
    try {
      await operation();
    } catch (error) {
      setError(message(error));
    }
  };
  return (
    <section className="panel management-panel">
      <h2>{mode === 'users' ? 'Utilizatori și roluri' : 'Securitatea contului'}</h2>
      <ErrorNotice error={error} />
      {notice && <p role="status">{notice}</p>}
      <p>
        {session.user.username} · {session.user.role} · MFA verificat
      </p>
      {mode === 'personal' && (
        <>
          <form
            className="management-form"
            onSubmit={(event) => {
              event.preventDefault();
              void act(async () => {
                const result = await api('/auth/reauthenticate', {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: { password: fields.password, code: fields.code },
                });
                setFields({ ...fields, password: '', code: '' });
                setSession(parseSession(result));
                setNotice('MFA reconfirmat.');
              });
            }}
          >
            <h3>Reconfirmă MFA pentru acțiuni sensibile</h3>
            <Field
              name="password"
              label="Parola curentă"
              type="password"
              value={fields.password}
              onChange={(password) => setFields({ ...fields, password })}
            />
            <Field
              name="code"
              label={t.code}
              value={fields.code}
              onChange={(code) => setFields({ ...fields, code })}
            />
            <button className="secondary-button">Reconfirmă</button>
          </form>
          <form
            className="management-form"
            onSubmit={(event) => {
              event.preventDefault();
              void act(async () => {
                await api('/auth/password', {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: { current_password: fields.password, new_password: fields.new_password },
                });
                setFields({ ...fields, password: '', new_password: '' });
                setSession(null);
              }, 'Schimbarea parolei închide toate sesiunile, inclusiv aceasta. Verifică identitatea și consecințele înainte de confirmare.');
            }}
          >
            <h3>Schimbă parola și închide toate sesiunile</h3>
            <Field
              name="current_password"
              label="Parola curentă pentru schimbare"
              type="password"
              value={fields.password}
              onChange={(password) => setFields({ ...fields, password })}
            />
            <Field
              name="new_password"
              label="Parolă nouă"
              type="password"
              value={fields.new_password}
              onChange={(new_password) => setFields({ ...fields, new_password })}
            />
            <button className="secondary-button">Schimbă parola</button>
          </form>
          <button
            className="secondary-button"
            onClick={() =>
              void act(async () => {
                await api('/auth/sessions/revoke-all', {
                  method: 'POST',
                  body: {},
                  csrf: session.csrf_token,
                });
                setSession(null);
              }, 'Vei fi deconectat din toate sesiunile, inclusiv aceasta. Aceasta nu oprește automat testele deja înregistrate.')
            }
          >
            Închide toate sesiunile
          </button>
        </>
      )}
      {mode === 'users' && session.user.role !== 'OWNER' && (
        <p>
          Doar proprietarul poate administra identități și roluri. Drepturile nu se schimbă prin
          navigare.
        </p>
      )}
      {mode === 'users' && session.user.role === 'OWNER' && (
        <>
          <form
            className="management-form"
            onSubmit={(event) => {
              event.preventDefault();
              void act(async () => {
                await api('/auth/users', {
                  method: 'POST',
                  csrf: session.csrf_token,
                  body: {
                    username: fields.username,
                    display_name: fields.display_name,
                    password: fields.new_password,
                    role: fields.role,
                  },
                });
                setFields({ ...fields, new_password: '', username: '', display_name: '' });
                await load();
                setNotice(
                  'Utilizator creat. Acesta trebuie să configureze MFA la prima autentificare.',
                );
              });
            }}
          >
            <h3>Creează utilizator</h3>
            <Field
              name="username"
              label={t.username}
              value={fields.username}
              onChange={(username) => setFields({ ...fields, username })}
            />
            <Field
              name="display_name"
              label={t.displayName}
              value={fields.display_name}
              onChange={(display_name) => setFields({ ...fields, display_name })}
            />
            <Field
              name="new_user_password"
              label="Parola inițială a utilizatorului"
              type="password"
              value={fields.new_password}
              onChange={(new_password) => setFields({ ...fields, new_password })}
            />
            <Field
              name="role"
              label="Rol"
              value={fields.role}
              options={[
                { value: 'OPERATOR', label: 'Operator' },
                { value: 'VIEWER', label: 'Doar citire' },
              ]}
              onChange={(role) => setFields({ ...fields, role })}
            />
            <button className="secondary-button">Creează utilizator</button>
          </form>
          <div className="management-cards">
            {users.map((user) => (
              <article key={user.id} className="management-record">
                <h3>{user.display_name}</h3>
                <p>
                  {user.username} · {user.role} · {user.active ? 'Activ' : 'Suspendat'}
                </p>
                {user.role !== 'OWNER' && (
                  <>
                    <button
                      className="text-button"
                      onClick={() =>
                        void act(async () => {
                          await api(`/auth/users/${user.id}`, {
                            method: 'PATCH',
                            csrf: session.csrf_token,
                            body: { role: user.role, active: !user.active },
                          });
                          await load();
                        }, `Modifici accesul sau rolul pentru ${user.display_name} (${user.username}). Sesiunile și drepturile acestei persoane sunt afectate imediat, conform regulilor serverului.`)
                      }
                    >
                      {user.active ? 'Suspendă accesul' : 'Restabilește accesul'}
                    </button>
                    <button
                      className="text-button"
                      onClick={() =>
                        void act(async () => {
                          await api(`/auth/users/${user.id}`, {
                            method: 'PATCH',
                            csrf: session.csrf_token,
                            body: {
                              role: user.role === 'VIEWER' ? 'OPERATOR' : 'VIEWER',
                              active: user.active,
                            },
                          });
                          await load();
                        }, `Modifici accesul sau rolul pentru ${user.display_name} (${user.username}). Sesiunile și drepturile acestei persoane sunt afectate imediat, conform regulilor serverului.`)
                      }
                    >
                      Schimbă rolul
                    </button>
                  </>
                )}
              </article>
            ))}
          </div>
        </>
      )}
      {review && (
        <ConfirmDialog
          title="Verifică acțiunea sensibilă"
          onClose={() => {
            if (!reviewBusy) setReview(null);
          }}
        >
          <p>{review.consequence}</p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (reviewBusy) return;
              setReviewBusy(true);
              void act(review.operation).finally(() => {
                setReviewBusy(false);
                setReview(null);
              });
            }}
          >
            <label className="management-check">
              <input type="checkbox" required />
              Confirm identitatea, persoana și consecințele afișate. Serverul verifică rolul și MFA
              recent.
            </label>
            <button disabled={reviewBusy}>Confirmă modificarea</button>
          </form>
        </ConfirmDialog>
      )}
    </section>
  );
}

export function Workspace({
  session,
  setSession,
  initialSection,
}: {
  session: Session;
  setSession: (value: Session | null) => void;
  initialSection: Tab;
}) {
  const tab = initialSection;
  const [records, setRecords] = useState<Record<string, RecordItem[]>>({});
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<RecordItem | null>(null);
  const [notice, setNotice] = useState('');
  const [page, setPage] = useState(0);
  const [more, setMore] = useState(false);
  const [query, setQuery] = useState('');
  const kind = tab === 'accounts' ? 'accounts' : tab === 'risks' ? 'risk-profiles' : 'policies';
  const load = useCallback(async () => {
    setError(null);
    try {
      if (
        tab === 'security' ||
        tab === 'market' ||
        tab === 'broker' ||
        tab === 'riskCenter' ||
        tab === 'research'
      )
        return;
      if (tab === 'audit') {
        const values = await api<AuditEvent[]>(`/audit?after_sequence=${page}&limit=50`);
        setAudit(values);
        setMore(values.length === 50);
        return;
      }
      const main = await api<RecordPage>(
        `/records/${kind}?offset=${page * 20}&limit=20&q=${encodeURIComponent(query)}`,
      );
      const result: Record<string, RecordItem[]> = { [kind]: main.items };
      for (const related of ['accounts', 'programs', 'firms'])
        if (related !== kind)
          result[related] = (await api<RecordPage>(`/records/${related}?limit=100`)).items;
      setRecords(result);
      setMore((page + 1) * 20 < main.total);
    } catch (error) {
      setError(message(error));
      if (error instanceof ApiError && error.status === 401) setSession(null);
    }
  }, [tab, kind, page, query, setSession]);
  useEffect(() => {
    void load();
  }, [load]);
  const options = (kind: string): Options =>
    (records[kind] ?? []).map((item) => ({ value: item.id, label: item.data.name }));
  const saved = () => {
    setEditing(null);
    setNotice('Înregistrarea a fost salvată în PostgreSQL.');
    void load();
  };
  const selections = {
    account_id: options('accounts'),
    program_id: options('programs'),
    firm_id: options('firms'),
  };
  const fields: FieldName[] =
    tab === 'accounts'
      ? ['name', 'currency', 'initial_capital', 'program_id']
      : tab === 'risks'
        ? [
            'name',
            'account_id',
            'per_trade_pct',
            'daily_loss_pct',
            'total_loss_pct',
            'aggregate_risk_pct',
          ]
        : [
            'name',
            'account_id',
            'program_id',
            'version',
            'source_references',
            'document_digest',
            'effective_at',
            'expires_at',
          ];
  return (
    <>
      <ErrorNotice error={error} />
      {notice && <p role="status">{notice}</p>}
      {tab === 'risks' && (
        <div className="notice">
          <strong>Înregistrări descriptive — nu aplică limite.</strong>
          <p>
            Aceste valori de catalog nu sunt profiluri active ale Risk Gateway. Limitele aplicate se
            revizuiesc separat în Siguranța contului.
          </p>
        </div>
      )}
      {tab === 'policies' && (
        <div className="notice">
          Verificarea documentului sursă nu autorizează tranzacționarea. Politicile efective se
          verifică separat, pentru contul și programul exact.
        </div>
      )}
      {session.user.role === 'VIEWER' && (
        <p>
          Rolul Doar citire permite inspectarea înregistrărilor, nu salvarea sau schimbarea lor.
        </p>
      )}
      {tab === 'research' ? (
        <StrategyLab session={session} onExpired={() => setSession(null)} />
      ) : tab === 'riskCenter' ? (
        <RiskCenter session={session} onExpired={() => setSession(null)} />
      ) : tab === 'broker' ? (
        <BrokerCenter session={session} onExpired={() => setSession(null)} />
      ) : tab === 'market' ? (
        <MarketData session={session} onExpired={() => setSession(null)} />
      ) : tab === 'security' ? (
        <Security session={session} setSession={setSession} />
      ) : tab === 'audit' ? (
        <section className="panel management-panel">
          <h2>Activitate de audit</h2>
          <p>
            Evenimente persistente, ordonate și legate criptografic. Administratorul bazei de date
            și gazda rămân limite de încredere.
          </p>
          {session.user.role === 'OWNER' && (
            <button
              className="secondary-button"
              onClick={() => {
                void api<{ valid: boolean; sequence: number }>('/audit/verify')
                  .then((result) =>
                    setNotice(
                      result.valid
                        ? `Lanț verificat: ${result.sequence} evenimente.`
                        : 'Verificarea integrității a eșuat. Investighează înainte de a continua.',
                    ),
                  )
                  .catch((error) => setError(message(error)));
              }}
            >
              Verifică integritatea
            </button>
          )}
          <ol className="audit-timeline">
            {audit.map((event) => (
              <li key={event.id}>
                <strong>
                  #{event.sequence} · {event.event_type}
                </strong>
                <span>
                  {new Date(event.timestamp).toLocaleString('ro-RO')} · {event.actor_role} · MFA{' '}
                  {event.mfa_verified ? 'da' : 'nu'}
                </span>
                <code>{event.entity_id ?? event.correlation_id}</code>
              </li>
            ))}
          </ol>
          <button className="text-button" disabled={!page} onClick={() => setPage(0)}>
            Început
          </button>
          <button
            className="text-button"
            disabled={!more}
            onClick={() => setPage(audit.at(-1)?.sequence ?? 0)}
          >
            Evenimente următoare
          </button>
        </section>
      ) : (
        <section className="panel management-panel">
          <h2>{t.tabs[tab]}</h2>
          <p>{t.simulation}</p>
          <Field
            name="filter"
            label="Caută înregistrări"
            required={false}
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(0);
            }}
          />
          <button className="text-button" onClick={() => void load()}>
            {t.refresh}
          </button>
          <Cards
            items={records[kind] ?? []}
            actions={(item) =>
              tab !== 'policies' ? (
                <button
                  className="text-button"
                  disabled={session.user.role === 'VIEWER'}
                  onClick={() => setEditing(item)}
                >
                  Editează {item.data.name}
                </button>
              ) : session.user.role === 'OWNER' ? (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void api(`/policies/${item.id}/verify`, {
                      method: 'POST',
                      csrf: session.csrf_token,
                      body: {
                        decision: 'VERIFIED',
                        source_review_acknowledged: true,
                        expected_revision: item.revision,
                      },
                    })
                      .then(saved)
                      .catch((error) => setError(message(error)));
                  }}
                >
                  <label className="management-check">
                    <input type="checkbox" required /> Am verificat documentul, programul, contul și
                    perioada. Această atestare nu permite tranzacționarea.
                  </label>
                  <button className="text-button">Înregistrează verificarea sursei</button>
                </form>
              ) : null
            }
          />
          <div className="management-toolbar">
            <button className="text-button" disabled={page === 0} onClick={() => setPage(page - 1)}>
              Anterior
            </button>
            <span>Pagina {page + 1}</span>
            <button className="text-button" disabled={!more} onClick={() => setPage(page + 1)}>
              Următor
            </button>
          </div>
          <RecordForm
            key={`${kind}-${editing?.id ?? 'new'}`}
            kind={kind}
            fields={fields}
            selections={selections}
            session={session}
            editing={editing}
            onSaved={saved}
          />
          {tab === 'policies' && (
            <>
              <h3>Firme și programe</h3>
              <p>
                FTMO, FundedNext și The5ers sunt doar nume de catalog. Regulile curente nu sunt
                presupuse sau importate automat.
              </p>
              <Cards items={records.programs ?? []} />
              <RecordForm
                kind="programs"
                fields={['name', 'firm_id', 'phase', 'platform']}
                selections={selections}
                session={session}
                onSaved={saved}
              />
              <RecordForm
                kind="firms"
                fields={['name', 'website']}
                session={session}
                onSaved={saved}
              />
            </>
          )}
        </section>
      )}
    </>
  );
}

export default function Management({ initialSection = 'accounts' }: { initialSection?: Tab }) {
  const { session, setSession, loading, unavailable, refresh } = useAuth();
  if (loading) return <p role="status">Verificăm sesiunea…</p>;
  return (
    <div className="management">
      {unavailable && (
        <p role="alert">
          Nu putem verifica sesiunea.{' '}
          <button onClick={() => void refresh()}>Reîncearcă verificarea</button>
        </p>
      )}
      {session?.state === 'FULL' ? (
        <Workspace
          key={initialSection}
          session={session}
          setSession={setSession}
          initialSection={initialSection}
        />
      ) : (
        <Authentication session={session} setSession={setSession} />
      )}
    </div>
  );
}
