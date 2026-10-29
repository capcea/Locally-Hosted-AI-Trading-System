import { useState } from 'react';
import type { RefObject } from 'react';
import {
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronDown,
  ChevronRight,
  FlaskConical,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Settings2,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from 'lucide-react';
import type { Route } from '../navigation/routes';
import { Link } from '../navigation/history';
import { activeSection } from '../navigation/sections';
import { pageTitles } from '../v1/navigation';
import type { Session } from '../management-api';

type MenuItem = {
  href: string;
  label: string;
};
const research: MenuItem[] = [
  { href: '/testeaza/ai', label: 'AI Center' },
  { href: '/testeaza/strategii', label: 'Strategii' },
  { href: '/testeaza/nou', label: 'Backtesting' },
  { href: '/testeaza/activitate', label: 'Experimente' },
  { href: '/testeaza/campanii', label: 'Campanii' },
  { href: '/testeaza/date', label: 'Date istorice' },
];
const results: MenuItem[] = [
  { href: '/rezultate', label: 'Toate rezultatele' },
  { href: '/rezultate/compara', label: 'Compară teste' },
  { href: '/rezultate/simulari', label: 'Jurnale simulare' },
];
const safety: MenuItem[] = [
  { href: '/conturi/siguranta', label: 'Centru de risc' },
  { href: '/conturi', label: 'Conturi' },
  { href: '/conturi/documente', label: 'Politici și documente' },
  { href: '/conturi/conexiuni', label: 'Conexiuni broker' },
];
const settings: MenuItem[] = [
  { href: '/setari/ai', label: 'Modele AI' },
  { href: '/setari/surse', label: 'Surse de date' },
  { href: '/setari/securitate', label: 'Securitate și MFA' },
  { href: '/setari/utilizatori', label: 'Utilizatori' },
  { href: '/setari/diagnostic', label: 'Diagnostic' },
  { href: '/setari', label: 'Toate setările' },
];
const submenus = { research, results, accounts: safety, settings };
const matches = (route: Route, href: string) =>
  route.path === href ||
  route.canonicalPath === href ||
  (href !== '/' && route.path.startsWith(href + '/'));

export function CockpitNavigation({ route }: { route: Route }) {
  const active = activeSection(route);
  const [expanded, setExpanded] = useState<string | null>(null);
  const sections = [
    { id: 'home', title: 'Cockpit', href: '/', icon: LayoutDashboard },
    { id: 'research', title: 'AI & Teste', href: '/testeaza', icon: BrainCircuit },
    { id: 'results', title: 'Rezultate', href: '/rezultate', icon: ChartNoAxesCombined },
    { id: 'accounts', title: 'Siguranță', href: '/conturi/siguranta', icon: ShieldCheck },
    { id: 'settings', title: 'Setări', href: '/setari', icon: Settings2 },
  ] as const;
  return (
    <aside className="cockpit-sidebar" aria-label="Navigare AI Cockpit">
      <Link href="/" className="cockpit-brand" aria-label="Local AI — Cockpit">
        <span className="cockpit-brand-mark"><Sparkles size={23} aria-hidden="true" /></span>
        <span><strong>LOCAL AI</strong><small>TRADING SYSTEM</small></span>
      </Link>
      <div className="cockpit-nav-label">WORKSPACE</div>
      <nav className="cockpit-nav" aria-label="Navigare principală">
        {sections.map(({ id, title, href, icon: Icon }) => {
          const selected = route.area === id || (id === 'home' && route.screen === 'home');
          const children = submenus[id as keyof typeof submenus];
          const opened = expanded === id || (expanded === null && selected && id !== 'home');
          return (
            <div className="cockpit-nav-group" key={id}>
              <div className="cockpit-nav-entry">
                <Link className={'cockpit-nav-link' + (selected ? ' is-active' : '')}
                  href={href} aria-current={selected ? 'page' : undefined}>
                  <Icon size={19} strokeWidth={1.8} aria-hidden="true" />
                  <span>{title}</span>
                </Link>
                {children && (
                  <button type="button" className="cockpit-nav-expander"
                    aria-label={(opened ? 'Ascunde ' : 'Arată ') + 'submeniul ' + title}
                    aria-expanded={opened}
                    onClick={() => setExpanded(opened ? 'closed' : id)}>
                    {opened ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                  </button>
                )}
              </div>
              {children && opened && (
                <div className="cockpit-subnav">
                  {children.map(item =>
                    <Link key={item.href} href={item.href}
                      className={'cockpit-subnav-link' + (active === item.href || matches(route, item.href) && item.href !== href ? ' is-active' : '')}>
                      {item.label}
                    </Link>)}
                </div>
              )}
              {id === 'accounts' && <div className="cockpit-nav-divider" />}
            </div>
          );
        })}
      </nav>
      <div className="cockpit-sidebar-bottom">
        <div className="cockpit-guard">
          <span className="cockpit-micro">EXECUTION GUARD</span>
          <strong><i aria-hidden="true" /> Broker orders blocked</strong>
          <p>Modul de execuție externă este dezactivat.</p>
        </div>
        <small className="cockpit-version">LOCAL AI · Research workspace</small>
      </div>
    </aside>
  );
}

export function CockpitTopbar({
  route,
  session,
  titleRef,
  onLogout,
}: {
  route: Route;
  session: Session | null;
  titleRef: RefObject<HTMLHeadingElement | null>;
  onLogout: () => void;
}) {
  const title = pageTitles(route);
  const initials = session?.state === 'FULL'
    ? session.user.display_name.split(/\s+/).filter(Boolean).slice(0, 2).map(x => x[0]).join('').toUpperCase()
    : 'AI';
  const date = new Intl.DateTimeFormat('ro-RO', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date());
  return (
    <header className="cockpit-topbar">
      <div className="cockpit-breadcrumb">
        <span>Workspace</span><span aria-hidden="true">/</span>
        <h1 tabIndex={-1} ref={titleRef}>{title}</h1>
      </div>
      <div className="cockpit-top-actions">
        <time dateTime={new Date().toISOString().slice(0, 10)} className="cockpit-top-date">{date}</time>
        <span className="cockpit-mode"><i aria-hidden="true" /> SIMULATED</span>
        {session?.state === 'FULL' ? (
          <button type="button" onClick={onLogout} className="cockpit-avatar"
            title="Deconectare" aria-label="Deconectare">
            <span>{initials}</span><LogOut size={13} aria-hidden="true" />
          </button>
        ) : <Link className="cockpit-login" href="/autentificare"><LockKeyhole size={14} /> Autentificare</Link>}
      </div>
    </header>
  );
}

export function CockpitPageHeading({ route }: { route: Route }) {
  return (
    <div className="cockpit-page-heading">
      <div>
        <div className="cockpit-eyebrow">WORKSPACE / {route.area === 'settings' ? 'CONFIGURATION' : route.area === 'accounts' ? 'RISK CONTROL' : route.area === 'results' ? 'ANALYTICS' : 'RESEARCH'}</div>
        <h2>{pageTitles(route)} <span aria-hidden="true">✳</span></h2>
        <p>{route.area === 'research'
          ? 'Strategii, modele AI și experimente — fără informații inutile.'
          : route.area === 'results'
            ? 'Rezultate simulate și dovezile lor.'
            : route.area === 'accounts'
              ? 'Monitorizează conturile, limitele și siguranța.'
              : route.area === 'settings'
                ? 'Configurarea și diagnosticul platformei.'
                : 'Acces securizat la Local AI Trading.'}</p>
      </div>
      <Link className="cockpit-page-action" href={route.area === 'accounts' ? '/conturi/siguranta' : '/testeaza/nou'}>
        {route.area === 'accounts' ? <ShieldCheck size={15} /> : <FlaskConical size={15} />}
        {route.area === 'accounts' ? 'Verifică riscul' : 'Test nou'}
      </Link>
    </div>
  );
}

export function CockpitSimulationNotice() {
  return (
    <div className="cockpit-simulation-notice" role="note">
      <TriangleAlert size={16} aria-hidden="true" />
      <strong>SIMULATED / DENY_ALL</strong>
      <span>Ordine externe blocate</span>
      <small>Research only · No live trading</small>
    </div>
  );
}
