import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Home,
  FlaskConical,
  ChartNoAxesCombined,
  ShieldCheck,
  Settings,
  Moon,
  Sun,
} from 'lucide-react';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import { Authentication, Workspace, Security } from './Management';
import type { Tab } from './Management';
import { getOverview, isStale } from './api';
import type { Overview } from './api';
import { api } from './management-api';
import type { RecordItem } from './management-api';
import { allRecords } from './records';
import { primary } from './navigation/routes';
import { Link, navigate, useRoute } from './navigation/history';
import RiskBanner from './RiskBanner';
import RiskCenter from './RiskCenter';
import MarketData from './MarketData';
import BrokerCenter from './BrokerCenter';
import StrategyLab from './StrategyLab';
import HomePage from './home/HomePage';
import { InfrastructurePage, GovernancePage, RoadmapPage } from './LegacyPublic';
import { Evidence } from './ui/Controls';
import { PublicReadTime } from './ui/PublicReadTime';

const icons = [Home, FlaskConical, ChartNoAxesCombined, ShieldCheck, Settings];
const settingsLinks = [
  ['/setari/aspect', 'Aspect'],
  ['/setari/securitate', 'Securitate și MFA'],
  ['/setari/utilizatori', 'Utilizatori și roluri'],
  ['/setari/istoric', 'Istoric verificabil'],
  ['/setari/surse', 'Surse de date'],
  ['/setari/catalog', 'Catalog de instrumente'],
  ['/setari/registru-tehnic', 'Registru tehnic'],
  ['/setari/diagnostic', 'Starea serviciilor'],
  ['/setari/despre', 'Capabilități și limite'],
  ['/setari/despre/plan', 'Plan de dezvoltare'],
];
const accountLinks = [
  ['/conturi', 'Conturi pentru simulare'],
  ['/conturi/siguranta', 'Siguranță, limite și politici aplicate'],
  ['/conturi/documente', 'Documente și programe'],
  ['/conturi/conexiuni', 'Observații broker · numai citire'],
  ['/conturi/avansat/inregistrari-risc', 'Înregistrări descriptive de risc'],
  ['/conturi/avansat/simulator', 'Simulator manual avansat'],
];
const researchLinks = [
  ['/testeaza/nou', 'Test nou'],
  ['/testeaza/strategii', 'Strategii revizuite'],
  ['/testeaza/activitate', 'Activitatea testelor'],
  ['/testeaza/date', 'Date pentru teste'],
  ['/testeaza/date/import', 'Adaugă date istorice'],
  ['/testeaza/evaluare-finala', 'Evaluare finală protejată'],
];
function Shell() {
  const route = useRoute();
  const {
    session,
    setSession,
    loading: authLoading,
    unavailable,
    refresh: refreshSession,
    expire,
  } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [overviewError, setOverviewError] = useState(false);
  const [lastSuccess, setLastSuccess] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [accountError, setAccountError] = useState(false);
  const [accountId, setAccountId] = useState('');
  const [accountsOwner, setAccountsOwner] = useState('');
  const [contextOwner, setContextOwner] = useState('');
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('research-theme') ?? 'system';
    } catch {
      return 'system';
    }
  });
  const [systemLight, setSystemLight] = useState(
    () => matchMedia('(prefers-color-scheme: light)').matches,
  );
  const titleRef = useRef<HTMLHeadingElement>(null);
  const request = useRef<AbortController | null>(null);
  const full = session?.state === 'FULL';
  const ownerId = session?.user.id ?? '';
  const selectedAccount = route.accountId ?? (contextOwner === ownerId ? accountId : '');
  const chooseAccount = useCallback(
    (id: string) => {
      setContextOwner(ownerId);
      setAccountId(id);
    },
    [ownerId],
  );
  const visibleAccounts = accountsOwner === session?.user.id ? accounts : [];
  const refresh = useCallback(async () => {
    request.current?.abort();
    const c = new AbortController();
    request.current = c;
    const timeout = setTimeout(() => c.abort(), 10000);
    try {
      const value = await getOverview(c.signal);
      if (request.current === c) {
        setOverview(value);
        setOverviewError(false);
        setLastSuccess(Date.now());
      }
    } catch {
      if (request.current === c) setOverviewError(true);
    } finally {
      clearTimeout(timeout);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const poll = setInterval(() => {
      setNow(Date.now());
      void refresh();
    }, 15000);
    return () => {
      clearInterval(poll);
      request.current?.abort();
    };
  }, [refresh]);
  useEffect(() => {
    const media = matchMedia('(prefers-color-scheme: light)');
    const update = () => setSystemLight(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);
  const light = theme === 'light' || (theme === 'system' && systemLight);
  useEffect(() => {
    document.documentElement.dataset.theme = light ? 'light' : 'dark';
    try {
      localStorage.setItem('research-theme', theme);
    } catch {
      /* Nonessential preference. */
    }
  }, [light, theme]);
  useEffect(() => {
    titleRef.current?.focus();
    window.scrollTo({ top: 0 });
  }, [route.path]);
  useEffect(() => {
    if (!full) {
      setAccounts([]);
      setAccountId('');
      setAccountsOwner('');
      setContextOwner('');
      return;
    }
    let active = true;
    void allRecords('accounts')
      .then((a) => {
        if (active) {
          setAccounts(a);
          setAccountsOwner(ownerId);
          setAccountError(false);
        }
      })
      .catch(() => {
        if (active) setAccountError(true);
      });
    return () => {
      active = false;
    };
  }, [full, ownerId, route.path]);
  const stale = overviewError || isStale(lastSuccess, now);
  const publicPage = ['home', 'diagnostics', 'about', 'roadmap', 'not-found'].includes(
    route.screen,
  );
  const title =
    route.screen === 'home'
      ? 'Acasă'
      : route.screen === 'not-found'
        ? 'Pagina nu există'
        : (primary.find((p) => p.area === route.area)?.label ?? 'Autentificare');
  const links =
    route.area === 'settings'
      ? settingsLinks
      : route.area === 'accounts'
        ? accountLinks
        : route.area === 'research'
          ? researchLinks
          : route.area === 'results'
            ? [
                ['/rezultate', 'Rezultate stocate'],
                ['/rezultate/compara', 'Compară două teste'],
                ['/rezultate/simulari', 'Jurnale de simulare manuală'],
              ]
            : [];
  const tab: Tab =
    route.screen === 'audit'
      ? 'audit'
      : route.screen === 'security'
        ? 'security'
        : ((route.section ?? 'accounts') as Tab);
  return (
    <div className="product-shell">
      <a className="skip-link" href="#main-content">
        Mergi la conținut
      </a>
      <aside className="product-sidebar">
        <Link href="/" className="product-brand">
          <ChartNoAxesCombined aria-hidden="true" />
          <span>
            Trade Research<small>Cercetare. Dovezi. Control.</small>
          </span>
        </Link>
        <nav className="primary-nav" aria-label="Navigare principală">
          {primary.map((p, i) => {
            const Icon = icons[i];
            return (
              <Link
                key={p.path}
                href={p.path}
                aria-current={route.area === p.area ? 'page' : undefined}
                aria-label={p.label}
              >
                <Icon aria-hidden="true" size={20} />
                <span>{p.label}</span>
              </Link>
            );
          })}
        </nav>
        <p className="sidebar-mode">
          SIMULATED / DENY_ALL
          <br />
          Fără ordine către brokeri externi
        </p>
      </aside>
      <div className="product-main">
        <header className="product-header">
          <span>Platformă de cercetare</span>
          <div className="header-controls">
            <button
              type="button"
              className="icon-button"
              aria-label={light ? 'Activează tema întunecată' : 'Activează tema luminoasă'}
              onClick={() => setTheme(light ? 'dark' : 'light')}
            >
              {light ? <Moon /> : <Sun />}
            </button>
            {full ? (
              <>
                <span>
                  {session.user.display_name} · {session.user.role}
                </span>
                <button
                  className="text-button"
                  onClick={() =>
                    void api('/auth/logout', { method: 'POST', csrf: session.csrf_token, body: {} })
                      .then(() => {
                        setAccountId('');
                        setSession(null);
                      })
                      .catch(() => refreshSession())
                  }
                >
                  Deconectare
                </button>
              </>
            ) : (
              <Link href="/autentificare">Autentificare</Link>
            )}
          </div>
        </header>
        <main id="main-content" tabIndex={-1}>
          <header className="page-heading">
            <div>
              <h1 ref={titleRef} tabIndex={-1}>
                {title}
              </h1>
              <p>
                {route.area === 'research'
                  ? 'Teste istorice, cu ipoteze clare și rezultate verificabile.'
                  : route.area === 'results'
                    ? 'Ce s-a întâmplat în simulare și ce nu putem concluziona.'
                    : 'Starea platformei și următorul pas.'}
              </p>
            </div>
            {full && (
              <label className="account-context">
                Contul de lucru
                <select
                  aria-label="Contul de lucru"
                  value={selectedAccount}
                  onChange={(e) => {
                    chooseAccount(e.target.value);
                    if (route.area === 'accounts' && e.target.value)
                      navigate(`/conturi/${e.target.value}/siguranta`);
                  }}
                >
                  <option value="">Alege contul când este necesar</option>
                  {visibleAccounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.data.name}
                    </option>
                  ))}
                </select>
                {accountError && (
                  <small>UNKNOWN · lista conturilor nu poate fi citită complet.</small>
                )}
              </label>
            )}
          </header>
          <div className="mode-strip">
            SIMULARE · ordine externe blocate <span>SIMULATED / DENY_ALL</span>
          </div>
          {full && <RiskBanner key={session.user.id} />}
          {links.length > 0 && (
            <nav className="section-navigation" aria-label="În această secțiune">
              {links.map(([href, label]) => (
                <Link
                  key={href}
                  href={href}
                  aria-current={route.path === href ? 'page' : undefined}
                >
                  {label}
                </Link>
              ))}
            </nav>
          )}
          {unavailable && (
            <p role="alert" className="error-banner">
              UNAVAILABLE · nu putem verifica sesiunea. Nu presupunem că accesul este confirmat.{' '}
              <button onClick={() => void refreshSession()}>Verifică sesiunea</button>
            </p>
          )}
          {overviewError && ['home', 'diagnostics'].includes(route.screen) && (
            <p className="error-banner" role="alert">
              Conexiunea cu API-ul nu este disponibilă. Starea publică este neverificată;
              autentificarea și siguranța se verifică separat.
            </p>
          )}
          {authLoading && !publicPage ? (
            <p role="status">Verificăm sesiunea…</p>
          ) : !full && !publicPage ? (
            <Authentication session={session} setSession={setSession} />
          ) : (
            <>
              {route.screen === 'home' && (
                <HomePage
                  key={session?.user.id ?? 'public'}
                  overview={overview}
                  stale={stale}
                  refresh={() => void refresh()}
                />
              )}
              {route.screen === 'auth' && (
                <>
                  <p>Identitatea este confirmată în doi pași.</p>
                  {full ? (
                    <Link href="/testeaza/nou">Continuă cu un test</Link>
                  ) : (
                    <Authentication session={session} setSession={setSession} />
                  )}
                </>
              )}
              {full && route.screen === 'records' && (
                <Workspace
                  key={route.section}
                  session={session}
                  setSession={setSession}
                  initialSection={tab}
                />
              )}
              {full && route.screen === 'security' && (
                <Security
                  session={session}
                  setSession={setSession}
                  mode={route.section === 'utilizatori' ? 'users' : 'personal'}
                />
              )}
              {full && route.screen === 'audit' && (
                <Workspace session={session} setSession={setSession} initialSection="audit" />
              )}
              {full && route.screen === 'risk' && (
                <RiskCenter
                  key={selectedAccount}
                  session={session}
                  onExpired={expire}
                  initialAccount={selectedAccount}
                  onAccountChange={(id) => {
                    chooseAccount(id);
                    if (route.accountId && id) navigate(`/conturi/${id}/siguranta`);
                  }}
                />
              )}
              {full && route.screen === 'broker' && (
                <BrokerCenter session={session} onExpired={expire} />
              )}
              {full && route.screen === 'data' && (
                <MarketData session={session} onExpired={expire} />
              )}
              {full && route.screen === 'research' && (
                <StrategyLab
                  session={session}
                  onExpired={expire}
                  initialAccount={selectedAccount}
                  onAccountChange={chooseAccount}
                />
              )}
              {full && route.screen === 'registry' && (
                <section className="panel">
                  <h2>Registru tehnic · operațiuni API</h2>
                  <p>
                    Înregistrările descriptive nu sunt strategii revizuite, experimente reale sau
                    aprobări de execuție.
                  </p>
                  <Evidence
                    value={[
                      'firms',
                      'programs',
                      'venues',
                      'instruments',
                      'accounts',
                      'brokers',
                      'risk-profiles',
                      'policies',
                      'strategies',
                      'strategy-versions',
                      'experiments',
                      'approvals',
                      'incidents',
                    ]}
                  />
                  <a href="/openapi.json">Inspectează contractul și operațiunile autorizate</a>
                </section>
              )}
              {route.screen === 'settings' && (
                <section className="panel">
                  <h2>Preferințe și acces</h2>
                  <label>
                    Aspect
                    <select
                      aria-label="Aspect"
                      value={theme}
                      onChange={(e) => setTheme(e.target.value)}
                    >
                      <option value="system">Urmează sistemul</option>
                      <option value="light">Luminos</option>
                      <option value="dark">Întunecat</option>
                    </select>
                  </label>
                  <p>Limba produsului: română. Setările vizuale nu schimbă drepturile de acces.</p>
                  <ul>
                    {settingsLinks.map(([href, label]) => (
                      <li key={href}>
                        <Link href={href}>{label}</Link>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
              {route.screen === 'diagnostics' && (
                <>
                  <h2>Starea serviciilor</h2>
                  <button className="secondary-button" onClick={() => void refresh()}>
                    Actualizează starea publică
                  </button>
                  {overview ? (
                    <InfrastructurePage data={overview} stale={stale} />
                  ) : (
                    <p>UNKNOWN · Nu există un răspuns public verificat.</p>
                  )}
                </>
              )}
              {route.screen === 'about' && (
                <>
                  <section className="panel">
                    <h2>Capabilități și limite</h2>
                    <p>
                      Teste cantitative pe date admise, execuție simulată și control independent al
                      riscului. AI, promovarea automată și ordinele externe nu sunt disponibile.
                    </p>
                    <a href="/openapi.json">Contract API</a>
                  </section>
                  {overview && (
                    <>
                      <GovernancePage data={overview} />
                      <section className="panel">
                        <h2>Exemplu de configurație · nu se aplică</h2>
                        <p>
                          Valorile de referință sunt exemple din configurația publică. Nu sunt
                          solduri de broker, performanță sau limite aplicate conturilor tale.
                        </p>
                        <Evidence
                          title="Configurația de referință, fără autoritate de risc"
                          value={overview.reference_profile}
                        />
                      </section>
                    </>
                  )}
                </>
              )}
              {route.screen === 'roadmap' &&
                (overview ? (
                  <RoadmapPage data={overview} />
                ) : (
                  <p>Planul nu poate fi citit acum. Aceasta nu indică activitate de cercetare.</p>
                ))}
              {route.screen === 'not-found' && (
                <section className="panel">
                  <p>Verifică legătura. Nu afișăm date sau identități dintr-un cont neautorizat.</p>
                  <Link href="/">Revino acasă</Link>
                </section>
              )}
            </>
          )}
          <footer className="main-footer">
            Trade Research · Execuție simulată ·{' '}
            {lastSuccess ? (
              <>
                Stare publică citită la <PublicReadTime at={lastSuccess} />
              </>
            ) : (
              'Stare publică necunoscută'
            )}
          </footer>
        </main>
      </div>
    </div>
  );
}
export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
