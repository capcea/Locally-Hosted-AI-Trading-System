import { useCallback, useEffect, useRef, useState } from 'react';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import { AuthFeedback, MfaStepUp } from './auth/MfaStepUp';
import { Authentication, Workspace, Security } from './Management';
import type { Tab } from './Management';
import { useOverview } from './useOverview';
import { api } from './management-api';
import type { RecordItem } from './management-api';
import { allRecords } from './records';
import { settingsGroups } from './navigation/sections';
import { SectionNavigation } from './navigation/SectionNavigation';
import { Link, navigate, useRoute } from './navigation/history';
import RiskBanner from './RiskBanner';
import RiskCenter from './RiskCenter';
import MarketData from './MarketData';
import BrokerCenter from './BrokerCenter';
import StrategyLab from './StrategyLab';
import AICenter from './ai/AICenter';
import CampaignCenter from './campaigns/CampaignCenter';
import CockpitPage from './cockpit/CockpitPage';
import { InfrastructurePage, GovernancePage, RoadmapPage } from './LegacyPublic';
import { Evidence } from './ui/Controls';
import { PublicReadTime } from './ui/PublicReadTime';
import { AccountsOverview } from './v1/AccountsOverview';
import {
  CockpitNavigation,
  CockpitTopbar,
  CockpitPageHeading,
  CockpitSimulationNotice,
} from './cockpit/PlatformChrome';

function Shell() {
  const route = useRoute();
  const cockpitHome = route.screen === 'home';
  const {
    session,
    setSession,
    loading: authLoading,
    unavailable,
    refresh: refreshSession,
    expire,
  } = useAuth();
  const {
    overview,
    error: overviewError,
    receivedAt: lastSuccess,
    loading: overviewLoading,
    now,
    stale,
    refresh,
  } = useOverview();
  const [accounts, setAccounts] = useState<RecordItem[]>([]);
  const [accountError, setAccountError] = useState(false);
  const [accountId, setAccountId] = useState('');
  const [accountsOwner, setAccountsOwner] = useState('');
  const [contextOwner, setContextOwner] = useState('');
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('research-theme') ?? 'dark';
    } catch {
      return 'dark';
    }
  });
  const [systemLight, setSystemLight] = useState(
    () => matchMedia('(prefers-color-scheme: light)').matches,
  );
  const titleRef = useRef<HTMLHeadingElement>(null);
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
  const publicPage = ['home', 'diagnostics', 'about', 'roadmap', 'not-found'].includes(
    route.screen,
  );
  const tab: Tab =
    route.screen === 'audit'
      ? 'audit'
      : route.screen === 'security'
        ? 'security'
        : ((route.section ?? 'accounts') as Tab);
  return (
    <div className={cockpitHome ? 'product-shell cockpit-root' : 'product-shell ai-platform'}>
      <a className="skip-link" href="#main-content">
        Mergi la conținut
      </a>
      {!cockpitHome && (
        <CockpitNavigation
          route={route}
          overview={overview}
          stale={stale}
          now={now}
          error={Boolean(overviewError)}
          loading={overviewLoading}
          refresh={() => void refresh()}
        />
      )}
      <div className="product-main">
        {!cockpitHome && (
          <CockpitTopbar
            route={route}
            session={session}
            titleRef={titleRef}
            onLogout={() => {
              if (session?.state !== 'FULL') return;
              void api('/auth/logout', { method: 'POST', csrf: session.csrf_token, body: {} })
                .then(() => {
                  setAccountId('');
                  setSession(null);
                })
                .catch(() => refreshSession());
            }}
          />
        )}
        {cockpitHome ? (
          <main id="main-content" tabIndex={-1} className="cockpit-main">
            <CockpitPage overview={overview} stale={stale} />
          </main>
        ) : (
          <main id="main-content" tabIndex={-1}>
            <CockpitPageHeading route={route} />
            {full && (
              <label className="account-context cockpit-account-context">
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
                  <option value="">
                    {accountError
                      ? 'Lista conturilor nu este disponibilă'
                      : accountsOwner !== ownerId
                        ? 'Verificăm conturile…'
                        : visibleAccounts.length
                          ? 'Alege un cont'
                          : 'Niciun cont în lista citită'}
                  </option>
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
            <CockpitSimulationNotice />
            {full && <RiskBanner key={session.user.id} />}
            <details key={route.path} className="cockpit-page-tools">
              <summary>Secțiuni și instrumente avansate</summary>
              <SectionNavigation route={route} authenticated={full} />
            </details>
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
            <AuthFeedback />
            {authLoading && !publicPage ? (
              <p role="status">Verificăm sesiunea…</p>
            ) : !full && !publicPage ? (
              <Authentication
                key={session?.session_id ?? 'anonymous'}
                session={session}
                setSession={setSession}
              />
            ) : (
              <>
                {route.screen === 'auth' && (
                  <>
                    <p>Identitatea este confirmată în doi pași.</p>
                    {full ? (
                      <Link href="/testeaza/nou">Continuă cu un test</Link>
                    ) : (
                      <Authentication
                        key={session?.session_id ?? 'anonymous'}
                        session={session}
                        setSession={setSession}
                      />
                    )}
                  </>
                )}
                {full && route.screen === 'records' && route.section === 'accounts' && (
                  <AccountsOverview
                    accounts={visibleAccounts}
                    ready={accountsOwner === ownerId}
                    failed={accountError}
                    selected={selectedAccount}
                    choose={chooseAccount}
                  />
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
                {full && route.screen === 'ai' && (
                  <AICenter session={session} advanced={route.area === 'settings'} />
                )}
                {full && route.screen === 'campaigns' && (
                  <CampaignCenter key={`${session.user.id}:${route.campaignId ?? 'new'}`} />
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
                {full && route.screen === 'settings' && route.section !== 'aspect' && (
                  <MarketData session={session} onExpired={expire} settingsView="surse" />
                )}
                {route.screen === 'settings' && (
                  <section className="panel preferences-panel">
                    <h2>Preferințe și acces</h2>
                    <label className="management-field">
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
                    <p>
                      Limba produsului: română. Setările vizuale nu schimbă drepturile de acces.
                    </p>
                  </section>
                )}
                {route.screen === 'settings' && (
                  <div className="settings-groups">
                    {settingsGroups.map((group) => (
                      <section className="panel" key={group.title} aria-label={group.title}>
                        <h2>{group.title}</h2>
                        <ul className="settings-links">
                          {group.items.map((item) => (
                            <li key={item.href}>
                              <Link
                                href={item.href}
                                aria-label={item.label}
                                aria-describedby={`setting-help-${item.href.replaceAll('/', '-')}`}
                              >
                                <strong>{item.label}</strong>
                                <span id={`setting-help-${item.href.replaceAll('/', '-')}`}>
                                  {item.description}
                                </span>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </section>
                    ))}
                  </div>
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
                        Teste cantitative pe date admise, execuție simulată și control independent
                        al riscului. Analiza AI necesită un model privat verificat. Cercetarea
                        autonomă, promovarea automată și ordinele externe nu sunt disponibile.
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
                    <p>
                      Verifică legătura. Nu afișăm date sau identități dintr-un cont neautorizat.
                    </p>
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
        )}
      </div>
    </div>
  );
}
export default function App() {
  return (
    <AuthProvider>
      <Shell />
      <MfaStepUp />
    </AuthProvider>
  );
}
