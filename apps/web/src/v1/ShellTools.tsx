import { useEffect, useRef, useState } from 'react';
import { Search, ChevronRight, CircleCheck, CircleHelp, CircleAlert } from 'lucide-react';
import type { Overview } from '../api';
import type { Route } from '../navigation/routes';
import { Link, navigate } from '../navigation/history';
import { sectionItems, activeSection } from '../navigation/sections';
import { researchLinks, platformLinks } from './navigation';
import { infrastructureHealth } from '../infrastructure-health';

export const searchPages = [
  { href: '/', label: 'Acasă' },
  ...Object.values(sectionItems).flat(),
  { href: '/autentificare', label: 'Autentificare' },
];
export function QuickSearch() {
  const [query, setQuery] = useState('');
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        input.current?.focus();
      }
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, []);
  const matches = query.trim()
    ? searchPages
        .filter((p) =>
          p.label.toLocaleLowerCase('ro-RO').includes(query.trim().toLocaleLowerCase('ro-RO')),
        )
        .slice(0, 8)
    : [];
  return (
    <div
      className="v1-search"
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          setQuery('');
          input.current?.focus();
        }
      }}
    >
      <form
        role="search"
        aria-label="Caută pagini și instrumente"
        onSubmit={(e) => {
          e.preventDefault();
          if (matches[0]) {
            navigate(matches[0].href);
            setQuery('');
          }
        }}
      >
        <Search size={17} aria-hidden="true" />
        <input
          ref={input}
          aria-label="Caută pagini și instrumente"
          placeholder="Caută pagini și instrumente…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') setQuery('');
          }}
          aria-describedby="v1-search-help"
        />
        <kbd>⌘ K</kbd>
      </form>
      <span id="v1-search-help" className="sr-only">
        Caută destinații din platformă. Nu caută în conținutul privat al experimentelor. Enter
        deschide primul rezultat; Escape închide lista.
      </span>
      {query.trim() && (
        <div className="v1-search-results">
          <ul aria-label="Pagini găsite">
            {matches.map((p) => (
              <li key={p.href}>
                <Link href={p.href} onClick={() => setQuery('')}>
                  {p.label}
                  <ChevronRight size={14} aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
          {!matches.length && (
            <p role="status">Nicio pagină găsită. Încearcă „date”, „risc” sau „AI”.</p>
          )}
          <button
            className="text-button"
            onClick={() => {
              setQuery('');
              input.current?.focus();
            }}
          >
            Închide căutarea
          </button>
        </div>
      )}
    </div>
  );
}
export function SidebarSections({ route }: { route: Route }) {
  const active = activeSection(route);
  return (
    <>
      <nav className="v1-sidebar-research" aria-label="Subsecțiuni Testează">
        {researchLinks.map((p) => (
          <Link key={p.href} href={p.href} aria-current={active === p.href ? 'page' : undefined}>
            <ChevronRight size={14} aria-hidden="true" />
            {p.label}
          </Link>
        ))}
      </nav>
      {route.area === 'settings' && (
        <nav className="v1-sidebar-settings" aria-label="Subsecțiuni Setări">
          {platformLinks.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              aria-current={(route.canonicalPath ?? route.path) === p.href ? 'page' : undefined}
            >
              <ChevronRight size={14} aria-hidden="true" />
              {p.label}
            </Link>
          ))}
        </nav>
      )}
    </>
  );
}
export function SidebarStatus({
  overview,
  stale,
  now = Date.now(),
  error = false,
  loading = false,
  refresh,
}: {
  overview: Overview | null;
  stale: boolean;
  now?: number;
  error?: boolean;
  loading?: boolean;
  refresh?: () => void;
}) {
  const health = infrastructureHealth(overview, stale || error, now);
  const message = error
    ? 'UNKNOWN · date indisponibile sau invalide'
    : loading && !overview
      ? 'UNKNOWN · verificăm starea…'
      : stale
        ? 'UNKNOWN · observație expirată sau neverificată'
        : {
            HEALTHY: 'Ultima observație tehnică',
            DEGRADED: 'DEGRADED · unele servicii sunt indisponibile',
            DOWN: 'DOWN · serviciile sunt indisponibile',
            UNKNOWN: 'UNKNOWN · observație incompletă sau neverificată',
          }[health.status];
  return (
    <section
      className="v1-system-status"
      aria-label="Starea tehnică a sistemului"
      data-status={health.status}
    >
      <h2>Status sistem</h2>
      <p role="status">{message}</p>
      <ul>
        {health.rows.map((row) => {
          const Icon =
            row.status === 'HEALTHY'
              ? CircleCheck
              : row.status === 'DOWN'
                ? CircleAlert
                : CircleHelp;
          return (
            <li key={row.id} data-service={row.id} data-status={row.status}>
              <Icon size={15} aria-hidden="true" />
              <span>{row.label}</span>
              <strong title={row.detail}>{row.text}</strong>
            </li>
          );
        })}
      </ul>
      {refresh && health.status !== 'HEALTHY' && (
        <button type="button" className="text-button" disabled={loading} onClick={refresh}>
          {loading ? 'Verificăm…' : 'Verifică din nou'}
        </button>
      )}
      <Link href="/setari/diagnostic">Diagnostic tehnic</Link>
      <small>
        Disponibilitatea serviciilor nu autorizează tranzacții. Worker și AI: verificare separată.
      </small>
    </section>
  );
}
