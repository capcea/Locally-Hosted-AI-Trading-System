import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Beaker,
  BookOpen,
  Box,
  Braces,
  ChartNoAxesCombined,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  Fingerprint,
  FlaskConical,
  Layers3,
  LayoutDashboard,
  LockKeyhole,
  Menu,
  Moon,
  Network,
  RefreshCw,
  Route,
  Search,
  Server,
  ShieldCheck,
  ShieldOff,
  Sun,
  Workflow,
  X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { getOverview, isStale, readinessSummary } from './api';
import type { Overview, Service } from './api';
import { locale, ro } from './locale';
import Management from './Management';
import RiskBanner from './RiskBanner';

type Page =
  | 'overview'
  | 'infrastructure'
  | 'governance'
  | 'roadmap'
  | 'management'
  | 'market'
  | 'broker'
  | 'riskCenter'
  | 'research';
const navigation: { id: Page; icon: LucideIcon }[] = [
  { id: 'overview', icon: LayoutDashboard },
  { id: 'infrastructure', icon: Server },
  { id: 'governance', icon: ShieldCheck },
  { id: 'roadmap', icon: Route },
  { id: 'management', icon: Fingerprint },
  { id: 'market', icon: Database },
  { id: 'broker', icon: Network },
  { id: 'riskCenter', icon: ShieldCheck },
  { id: 'research', icon: FlaskConical },
];
const serviceIcons: Record<string, LucideIcon> = {
  api: Braces,
  postgres: Database,
  redis: Layers3,
  storage: Box,
  mt5: ChartNoAxesCombined,
  ctrader: Network,
  ollama: Workflow,
  executor: ShieldOff,
};

function Badge({ children, tone = '' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function ServiceRow({ service, stale }: { service: Service; stale: boolean }) {
  const Icon = serviceIcons[service.id] || Server;
  return (
    <div className="service-row">
      <div className="service-icon">
        <Icon size={19} />
      </div>
      <div className="service-copy">
        <strong>{service.name}</strong>
        <span>{service.detail}</span>
      </div>
      <span className={`service-status ${stale ? 'stale' : service.status.toLowerCase()}`}>
        <i />
        {stale ? 'Neverificat' : ro.statuses[service.status]}
      </span>
    </div>
  );
}

function SafetyNotice() {
  return (
    <div className="safety-notice">
      <ShieldCheck size={19} />
      <div>
        <strong>Mediu de cercetare izolat</strong>
        <span>
          Tranzacționarea live și trimiterea ordinelor sunt dezactivate în această versiune.
        </span>
      </div>
      <Badge>SIMULATED</Badge>
    </div>
  );
}

function OverviewPage({
  data,
  stale,
  navigate,
}: {
  data: Overview;
  stale: boolean;
  navigate: (page: Page) => void;
}) {
  const profile = data.reference_profile;
  const readiness = readinessSummary(data.services);
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">
            <span className="small-dot" /> WORKSPACE / 001
          </span>
          <h2>
            Cercetare riguroasă.
            <br />
            <span>Fiecare decizie, verificabilă.</span>
          </h2>
          <p>
            Un spațiu pentru ipoteze, experimente reproductibile și strategii validate înainte de
            execuție.
          </p>
          <button className="primary-button" onClick={() => navigate('roadmap')}>
            Explorează planul de dezvoltare <ArrowUpRight size={17} />
          </button>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="orbit orbit-1" />
          <div className="orbit orbit-2" />
          <div className="orbit orbit-3" />
          <div className="orbital-label label-1">
            <Beaker size={14} /> IPOTEZĂ
          </div>
          <div className="orbital-label label-2">
            <ShieldCheck size={14} /> VALIDARE
          </div>
          <div className="orbital-label label-3">
            <Fingerprint size={14} /> TRASABILITATE
          </div>
          <div className="visual-core">
            <ChartNoAxesCombined size={44} strokeWidth={1.2} />
          </div>
          <div className="visual-caption">RESEARCH FIRST. ALWAYS.</div>
        </div>
        <span className="hero-phase">
          FAZA 04 <span>/ RISC INDEPENDENT · SIMULATED</span>
        </span>
      </section>

      <div className="section-heading">
        <h2>
          Profil de referință <span>USD</span>
        </h2>
        <span className="muted text-xs">Exemplu de configurare · fără cont conectat</span>
      </div>
      <section className="metrics" aria-label="Profil de referință, nu valori de cont">
        <Metric
          label="Capital de referință"
          value={new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0,
          }).format(Number(profile.equity))}
          icon={Layers3}
          footer="Configurație inițială, nu sold real"
        />
        <Metric
          label="Risc per tranzacție"
          value={`${profile.risk_per_trade_pct}%`}
          icon={ArrowUpRight}
          footer="Prag propus · motorul de risc urmează"
        />
        <Metric
          label="Limită pierdere zilnică"
          value={`${profile.daily_loss_pct}%`}
          icon={ArrowDownRight}
          footer="Prag propus · include P&L flotant"
        />
        <Metric
          label="Drawdown total"
          value={`${profile.total_drawdown_pct}%`}
          icon={ShieldCheck}
          footer="Prag propus · bază de calcul de definit"
        />
      </section>

      <div className="dashboard-grid">
        <section className="panel pipeline-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">DE LA IDEE LA DOVEZI</span>
              <h2>Fluxul de cercetare</h2>
            </div>
            <Badge>Planificat</Badge>
          </div>
          <div className="pipeline">
            {[
              { Icon: Search, name: 'Descoperire', note: 'Surse & ipoteze' },
              { Icon: Braces, name: 'Experiment', note: 'Cod izolat' },
              { Icon: Activity, name: 'Validare', note: 'OOS & risc' },
              { Icon: FlaskConical, name: 'Paper trading', note: 'Observație' },
            ].map(({ Icon, name, note }, index) => (
              <div className="pipeline-step" key={name}>
                <div className="step-icon">
                  <Icon size={23} />
                  {index < 3 && <ChevronRight className="step-arrow" size={17} />}
                </div>
                <strong>{name}</strong>
                <span>{note}</span>
                <small>0{index + 1}</small>
              </div>
            ))}
          </div>
          <div className="empty-research">
            <div className="empty-symbol">
              <FlaskConical size={22} />
            </div>
            <div>
              <h3>Primul experiment începe cu date verificate.</h3>
              <p>
                Nu există experimente rulate sau rezultate de performanță. Conectarea datelor și
                agenții sunt în planul de implementare.
              </p>
            </div>
          </div>
          <div className="panel-bottom">
            <span>
              <LockKeyhole size={13} /> Promovarea live va necesita aprobarea proprietarului.
            </span>
            <button className="text-button" onClick={() => navigate('governance')}>
              Vezi regulile <ArrowRight size={14} />
            </button>
          </div>
        </section>

        <section className="panel infrastructure-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">VERIFICARE DIRECTĂ</span>
              <h2>Starea infrastructurii</h2>
            </div>
            <span className="status-count">
              {stale ? '—' : `${readiness.healthy}/${readiness.total}`}
            </span>
          </div>
          {data.services.slice(0, 4).map((service) => (
            <ServiceRow key={service.id} service={service} stale={stale} />
          ))}
          <button className="wide-link" onClick={() => navigate('infrastructure')}>
            Toate serviciile și integrările <ArrowUpRight size={15} />
          </button>
        </section>
      </div>

      <div className="bottom-grid">
        <section className="panel instruments-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">UNIVERS DE CERCETARE</span>
              <h2>Clase de instrumente</h2>
            </div>
            <Badge>Fără feed</Badge>
          </div>
          <div className="instrument-list">
            {[
              ['FX', 'Forex', 'EURUSD · GBPUSD · USDJPY'],
              ['AU', 'Metale', 'XAUUSD · XAGUSD'],
              ['IX', 'Indici', 'Mapare specifică brokerului'],
              ['₿', 'Crypto', 'Disponibilitate de verificat'],
            ].map(([symbol, title, description]) => (
              <div className="instrument" key={title}>
                <span className="instrument-symbol">{symbol}</span>
                <div>
                  <strong>{title}</strong>
                  <span>{description}</span>
                </div>
                <span className="dash">—</span>
              </div>
            ))}
          </div>
          <p className="panel-note">
            Lista este orientativă. Niciun simbol nu este confirmat ca tranzacționabil.
          </p>
        </section>
        <section className="next-panel">
          <span className="eyebrow">CHECKPOINT CURENT</span>
          <div className="next-phase">
            02 <ArrowUpRight size={27} />
          </div>
          <h2>
            Date, timp
            <br />
            și proveniență.
          </h2>
          <p>
            Importuri și verificări persistente disponibile. Acceptarea în browser rămâne necesară.
          </p>
          <button className="text-button" onClick={() => navigate('roadmap')}>
            Vezi criteriile de acceptare <ArrowRight size={16} />
          </button>
        </section>
      </div>
    </>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
  footer,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  footer: string;
}) {
  return (
    <article className="metric">
      <div>
        <span>{label}</span>
        <Icon size={17} />
      </div>
      <strong>{value}</strong>
      <small>{footer}</small>
    </article>
  );
}

function InfrastructurePage({ data, stale }: { data: Overview; stale: boolean }) {
  const [filter, setFilter] = useState('');
  const services = data.services.filter((service) =>
    `${service.name} ${service.detail}`
      .toLocaleLowerCase(locale)
      .includes(filter.toLocaleLowerCase(locale)),
  );
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">DEPENDENȚE & INTEGRĂRI</span>
        <h2>
          Conexiuni explicite.
          <br />
          <span>Stare verificată.</span>
        </h2>
        <p>
          Fiecare serviciu își raportează starea. O dependență indisponibilă blochează verificarea
          de pregătire.
        </p>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Servicii</h2>
          <label className="search-box">
            <Search size={16} />
            <input
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Caută un serviciu…"
              aria-label="Caută un serviciu"
            />
          </label>
        </div>
        <div className="full-service-list">
          {services.map((service) => (
            <ServiceRow key={service.id} service={service} stale={stale} />
          ))}
          {services.length === 0 && <p className="no-results">Niciun serviciu găsit.</p>}
        </div>
        <div className="panel-bottom">
          <span>
            <Clock3 size={14} /> Actualizare automată la 15 secunde. Starea devine neverificată la
            pierderea conexiunii.
          </span>
        </div>
      </section>
      <div className="info-callout">
        <CircleHelp size={20} />
        <div>
          <h3>Pornire locală</h3>
          <p>
            Rulează <code>make dev</code> pentru PostgreSQL, Redis, stocare și aplicație. MT5,
            cTrader și gateway-ul AI necesită implementarea etapelor următoare.
          </p>
        </div>
      </div>
    </>
  );
}

function GovernancePage({ data }: { data: Overview }) {
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">LIMITE DE ÎNCREDERE</span>
        <h2>
          Siguranța este
          <br />
          <span>o proprietate a sistemului.</span>
        </h2>
        <p>Administrarea necesită autentificare și MFA. Nu există un flux de activare live.</p>
      </div>
      <div className="governance-grid">
        {[
          {
            icon: ShieldCheck,
            name: 'Execuție refuzată',
            value: data.safety.executor_capability,
            text: 'API-ul și contractul executorului refuză toate ordinele. Variabilele de mediu nu pot activa tranzacționarea.',
          },
          {
            icon: Fingerprint,
            name: 'Aprobări umane',
            value: 'IDENTITATE & MFA · FAZA 1',
            text: 'Conturile și configurările sunt protejate prin autentificare, roluri și MFA. Aprobările pentru execuție live nu sunt implementate.',
          },
          {
            icon: LockKeyhole,
            name: 'Cercetare izolată',
            value: 'EXECUȚIE COD DEZACTIVATĂ',
            text: 'Nu este instalat un runner pentru cod generat. Niciun agent nu poate executa strategii în acest mediu.',
          },
          {
            icon: BookOpen,
            name: 'Politici verificate',
            value: 'NEVERIFICATE',
            text: 'FTMO, FundedNext și The5ers necesită politici versionate pentru programul și contul exact. Nicio permisiune de trading nu este presupusă.',
          },
        ].map(({ icon: Icon, name, value, text }) => (
          <section className="panel rule-card" key={name}>
            <div className="rule-icon">
              <Icon size={23} />
            </div>
            <h3>{name}</h3>
            <Badge>{value}</Badge>
            <p>{text}</p>
          </section>
        ))}
      </div>
      <section className="panel block-reasons">
        <div className="panel-heading">
          <h2>Motivele blocării execuției</h2>
          <Badge tone="amber">4 controale active</Badge>
        </div>
        {data.safety.reasons.map((reason) => (
          <div key={reason}>
            <LockKeyhole size={16} />
            <code>{reason}</code>
            <Check size={17} />
          </div>
        ))}
      </section>
    </>
  );
}

function RoadmapPage({ data }: { data: Overview }) {
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">DEZVOLTARE ÎN ETAPE</span>
        <h2>
          Fiecare etapă are
          <br />
          <span>o condiție de trecere.</span>
        </h2>
        <p>
          Extindem platforma numai după verificarea etapei curente. Conectarea reală și rezultatele
          nu sunt presupuse.
        </p>
      </div>
      <div className="roadmap-list">
        {data.roadmap.map((phase) => (
          <section
            className={`panel roadmap-item ${phase.status === 'CURRENT' ? 'current' : ''}`}
            key={phase.number}
          >
            <span className="phase-number">{String(phase.number).padStart(2, '0')}</span>
            <div>
              <h3>{phase.title}</h3>
              <p>{phase.acceptance}</p>
            </div>
            <Badge tone={phase.status === 'CURRENT' ? 'green' : ''}>
              {phase.status === 'CURRENT' ? 'Etapa curentă' : 'Planificat'}
            </Badge>
          </section>
        ))}
      </div>
    </>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>('overview');
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastSuccess, setLastSuccess] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [mobileOpen, setMobileOpen] = useState(false);
  const [light, setLight] = useState(() => {
    try {
      return localStorage.getItem('research-theme') === 'light';
    } catch {
      return false;
    }
  });
  const request = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    const timeout = window.setTimeout(() => controller.abort('timeout'), 10_000);
    try {
      const snapshot = await getOverview(controller.signal);
      if (request.current !== controller) return;
      setData(snapshot);
      setError(null);
      setLastSuccess(Date.now());
      setNow(Date.now());
    } catch {
      if (
        request.current === controller &&
        (!controller.signal.aborted || controller.signal.reason === 'timeout')
      )
        setError('Conexiunea cu API-ul nu este disponibilă.');
    } finally {
      clearTimeout(timeout);
      if (request.current === controller) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => {
      setNow(Date.now());
      void refresh();
    }, 15_000);
    return () => {
      clearInterval(interval);
      request.current?.abort();
      request.current = null;
    };
  }, [refresh]);
  useEffect(() => {
    document.documentElement.dataset.theme = light ? 'light' : 'dark';
    try {
      localStorage.setItem('research-theme', light ? 'light' : 'dark');
    } catch {
      /* Nonessential preference. */
    }
  }, [light]);

  const stale = Boolean(error) || isStale(lastSuccess, now);
  const navigate = (target: Page) => {
    setPage(target);
    setMobileOpen(false);
    window.scrollTo({ top: 0 });
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Mergi la conținut
      </a>
      {mobileOpen && (
        <button
          className="sidebar-scrim"
          onClick={() => setMobileOpen(false)}
          aria-label="Închide meniul"
        />
      )}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark">
            <ChartNoAxesCombined size={23} />
          </span>
          <div>
            Trade<span>RESEARCH PLATFORM</span>
          </div>
          <button
            className="icon-button mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Închide navigarea"
          >
            <X size={19} />
          </button>
        </div>
        <div className="workspace-selector">
          <span className="workspace-avatar">R</span>
          <div>
            Research workspace<span>Mediu local</span>
          </div>
          <Badge>SIM</Badge>
        </div>
        <span className="nav-label">CENTRUL DE CONTROL</span>
        <nav aria-label="Navigare principală">
          {navigation.map(({ id, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${page === id ? 'active' : ''}`}
              aria-current={page === id ? 'page' : undefined}
              onClick={() => navigate(id)}
            >
              <Icon size={18} />
              <span>{ro[id]}</span>
              {page === id && <span className="nav-active-dot" />}
            </button>
          ))}
        </nav>
        <span className="nav-label future-label">ÎN DEZVOLTARE</span>
        <div className="future-navigation">
          {[
            { Icon: ChartNoAxesCombined, name: 'Backtesting', phase: '05' },
            { Icon: Workflow, name: 'Agenți AI', phase: '06' },
            { Icon: Activity, name: 'Execuție & audit', phase: '08' },
          ].map(({ Icon, name, phase }) => (
            <button
              key={name}
              className="nav-item future"
              onClick={() => navigate('roadmap')}
              title={`Planificat în faza ${phase}`}
            >
              <Icon size={18} />
              <span>{name}</span>
              <LockKeyhole size={12} />
            </button>
          ))}
        </div>
        <div className="sidebar-bottom">
          <div className="isolation-card">
            <ShieldCheck size={20} />
            <strong>Cercetare în siguranță</strong>
            <p>
              Nicio conexiune la bani reali.
              <br />
              Niciun ordin executabil.
            </p>
            <span>
              <i /> SIMULATION ONLY
            </span>
          </div>
          <a className="documentation" href="/openapi.json" target="_blank" rel="noreferrer">
            <BookOpen size={17} /> Contract API <ArrowUpRight size={14} />
          </a>
          <div className="sidebar-footer">
            <span className="local-avatar">L</span>
            <div>
              Stare publică<span>Administrare cu autentificare</span>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              onClick={() => setMobileOpen(true)}
              aria-label="Deschide meniul"
              aria-expanded={mobileOpen}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{ro[page]}</strong>
          </div>
          <div className="topbar-actions">
            <span className="environment-indicator">
              <i /> SIMULARE
            </span>
            <span className="top-divider" />
            <button
              className="icon-button"
              onClick={() => setLight(!light)}
              aria-label={light ? 'Activează tema întunecată' : 'Activează tema luminoasă'}
            >
              {light ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            <span
              className="user-avatar"
              title="Mediu local; identitatea se verifică în administrare"
            >
              L
            </span>
          </div>
        </header>
        <main id="main-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">AI TRADING RESEARCH</span>
              <h1>{page === 'overview' ? 'Centrul de cercetare' : ro[page]}</h1>
              <p>
                {page === 'overview'
                  ? 'Vizibilitate completă. Control înainte de execuție.'
                  : 'Un sistem construit pentru verificare și trasabilitate.'}
              </p>
            </div>
            <button className="secondary-button" onClick={() => void refresh()} disabled={loading}>
              <RefreshCw size={15} className={loading ? 'spin' : ''} />{' '}
              {loading ? 'Se verifică…' : 'Actualizează'}
            </button>
          </div>
          {data && !stale && <SafetyNotice />}
          {error && (
            <div className="error-banner" role="alert">
              <ShieldOff size={19} />
              <div>
                <strong>Conexiunea cu API-ul nu este disponibilă.</strong>
                <span>
                  {data
                    ? 'Stările afișate anterior sunt neverificate. Reîncercare automată la 15 secunde.'
                    : 'Pornește API-ul cu make local-api, apoi actualizează pagina.'}
                </span>
              </div>
            </div>
          )}
          {!data && loading && (
            <div className="loading-panel" role="status">
              <RefreshCw size={25} className="spin" />
              <h2>Verificăm mediul de cercetare…</h2>
              <p>Stările sunt citite direct din API.</p>
            </div>
          )}
          {data && (
            <>
              <RiskBanner onOpen={() => setPage('riskCenter')} />
              {page === 'overview' && (
                <OverviewPage data={data} stale={stale} navigate={navigate} />
              )}
              {page === 'infrastructure' && <InfrastructurePage data={data} stale={stale} />}
              {page === 'governance' && <GovernancePage data={data} />}
              {page === 'roadmap' && <RoadmapPage data={data} />}
              {page === 'management' && <Management />}
              {page === 'market' && <Management key="market" initialSection="market" />}
              {page === 'broker' && <Management key="broker" initialSection="broker" />}
              {page === 'research' && <Management key="research" initialSection="research" />}
              {page === 'riskCenter' && <Management key="riskCenter" initialSection="riskCenter" />}
            </>
          )}
          <footer className="main-footer">
            <span>
              Trade Research <span className="footer-dot">·</span> Identitate & date
            </span>
            <span>
              <span className={`footer-status-dot ${stale ? 'stale' : ''}`} />
              {lastSuccess
                ? `Ultima verificare ${new Date(lastSuccess).toLocaleTimeString(locale)}`
                : 'În așteptarea API-ului'}{' '}
              <span className="footer-dot">·</span> v0.1.0
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}
