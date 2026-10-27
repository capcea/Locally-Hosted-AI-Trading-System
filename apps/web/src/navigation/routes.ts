export type Area = 'home' | 'research' | 'results' | 'accounts' | 'settings' | 'auth';
export type Screen =
  | 'home'
  | 'research'
  | 'data'
  | 'broker'
  | 'risk'
  | 'records'
  | 'security'
  | 'audit'
  | 'settings'
  | 'diagnostics'
  | 'about'
  | 'roadmap'
  | 'registry'
  | 'auth'
  | 'not-found';
export type Route = {
  path: string;
  area: Area;
  screen: Screen;
  section?: string;
  accountId?: string;
  experimentId?: string;
  datasetId?: string;
  jobId?: string;
  runId?: string;
};
const uuid = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}';
export const primary = [
  { area: 'home', path: '/', label: 'Acasă' },
  { area: 'research', path: '/testeaza', label: 'Testează' },
  { area: 'results', path: '/rezultate', label: 'Rezultate' },
  { area: 'accounts', path: '/conturi', label: 'Conturi și siguranță' },
  { area: 'settings', path: '/setari', label: 'Setări' },
] as const;

/** Finite allowlist: never use arbitrary URL/query input as an auth return destination. */
export function resolveRoute(pathname: string): Route {
  const path = pathname === '/' ? '/' : pathname.replace(/\/$/, '');
  const route = (area: Area, screen: Screen, extra: Partial<Route> = {}): Route => ({
    path,
    area,
    screen,
    ...extra,
  });
  if (path === '/') return route('home', 'home');
  if (['/autentificare', '/configurare-proprietar', '/securizare-cont'].includes(path))
    return route('auth', 'auth');
  if (/^\/testeaza(?:\/(nou|strategii|activitate|evaluare-finala))?$/.test(path))
    return route('research', 'research', { section: path.split('/')[2] ?? 'index' });
  let m = path.match(new RegExp(`^/testeaza/(${uuid})/progres$`));
  if (m) return route('research', 'research', { experimentId: m[1], section: 'progress' });
  if (new RegExp(`^/testeaza/evaluare-finala/${uuid}$`).test(path))
    return route('research', 'research', { section: 'evaluare-finala' });
  if (/^\/testeaza\/date(?:\/(import))?$/.test(path))
    return route('research', 'data', { section: path.endsWith('/import') ? 'import' : 'catalog' });
  m = path.match(new RegExp(`^/testeaza/date/importuri/(${uuid})$`));
  if (m) return route('research', 'data', { jobId: m[1], section: 'jobs' });
  m = path.match(
    new RegExp(`^/testeaza/date/(${uuid})(?:/(previzualizare|provenienta|versiuni))?$`),
  );
  if (m) return route('research', 'data', { datasetId: m[1], section: m[2] ?? 'detail' });
  if (path === '/rezultate' || path === '/rezultate/compara')
    return route('results', 'research', {
      section: path.endsWith('compara') ? 'compare' : 'results',
    });
  if (path === '/rezultate/simulari') return route('results', 'broker', { section: 'journal' });
  m = path.match(new RegExp(`^/rezultate/simulari/(${uuid})/jurnal$`));
  if (m) return route('results', 'broker', { runId: m[1], section: 'journal' });
  m = path.match(
    new RegExp(`^/rezultate/(${uuid})(?:/(tranzactii|decizii|validare|provenienta))?$`),
  );
  if (m) return route('results', 'research', { experimentId: m[1], section: m[2] ?? 'result' });
  if (path === '/conturi') return route('accounts', 'records', { section: 'accounts' });
  if (path === '/conturi/siguranta') return route('accounts', 'risk');
  if (path === '/conturi/conexiuni' || path === '/conturi/avansat/simulator')
    return route('accounts', 'broker');
  if (path === '/conturi/documente') return route('accounts', 'records', { section: 'policies' });
  if (path === '/conturi/avansat/inregistrari-risc')
    return route('accounts', 'records', { section: 'risks' });
  m = path.match(
    new RegExp(
      `^/conturi/(${uuid})(?:/(siguranta|inchidere-simulata|limite|politici|ipoteze|verificare-risc|alocari-incidente|conexiuni|avansat)(?:/.*)?)?$`,
    ),
  );
  if (m) {
    const section = path.split('/').slice(3).join('/');
    const screen: Screen = section.includes('inregistrari-risc')
      ? 'records'
      : section.includes('simulator') || section.startsWith('conexiuni')
        ? 'broker'
        : 'risk';
    // Only documented suffixes; arbitrary paths are not valid return destinations.
    const suffixValid =
      !section ||
      /^(siguranta|inchidere-simulata|limite|ipoteze|verificare-risc|alocari-incidente|politici|conexiuni|avansat\/inregistrari-risc|avansat\/simulator\/nou)$/.test(
        section,
      ) ||
      new RegExp(
        `^(politici/${uuid}|conexiuni/${uuid}/observatii|avansat/simulator/${uuid}/(date|ordine))$`,
      ).test(section);
    if (suffixValid)
      return route('accounts', screen, {
        accountId: m[1],
        runId: section.match(new RegExp(`^avansat/simulator/(${uuid})/`))?.[1],
        section: screen === 'records' ? 'risks' : section,
      });
  }
  const settings: Record<string, Screen> = {
    '': 'settings',
    aspect: 'settings',
    securitate: 'security',
    utilizatori: 'security',
    istoric: 'audit',
    surse: 'data',
    catalog: 'data',
    'registru-tehnic': 'registry',
    diagnostic: 'diagnostics',
    despre: 'about',
    'despre/plan': 'roadmap',
  };
  if (path === '/setari' || path.startsWith('/setari/')) {
    const section = path.slice('/setari'.length).replace(/^\//, '');
    if (Object.hasOwn(settings, section)) return route('settings', settings[section], { section });
  }
  return route('home', 'not-found');
}

export function resultPath(id: string, tab = '') {
  return `/rezultate/${encodeURIComponent(id)}${tab ? `/${tab}` : ''}`;
}
export function progressPath(id: string) {
  return `/testeaza/${encodeURIComponent(id)}/progres`;
}
