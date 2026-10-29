import type { Area, Route } from './routes';

export type SectionItem = { href: string; label: string; description?: string };

export const settingsGroups = [
  {
    title: 'Cont și acces',
    items: [
      {
        href: '/setari/securitate',
        label: 'Securitate și MFA',
        description: 'Parolă, autentificare în doi pași și sesiuni.',
      },
      {
        href: '/setari/utilizatori',
        label: 'Utilizatori și roluri',
        description: 'Cine poate vedea și administra platforma.',
      },
      {
        href: '/setari/istoric',
        label: 'Istoric verificabil',
        description: 'Acțiuni înregistrate și dovezile lor.',
      },
    ],
  },
  {
    title: 'Date și cercetare',
    items: [
      {
        href: '/setari/surse',
        label: 'Surse de date',
        description: 'Furnizori, drepturi de utilizare și atribuire.',
      },
      {
        href: '/setari/ai',
        label: 'Modele AI și roluri',
        description: 'Conexiuni private, verificări reale și limite de analiză.',
      },
      {
        href: '/setari/catalog',
        label: 'Catalog de instrumente',
        description: 'Instrumentele folosite în importuri și teste.',
      },
      {
        href: '/setari/registru-tehnic',
        label: 'Registru tehnic',
        description: 'Identificatori și operațiuni disponibile prin API.',
      },
    ],
  },
  {
    title: 'Platformă',
    items: [
      {
        href: '/setari/diagnostic',
        label: 'Starea serviciilor',
        description: 'Disponibilitate și diagnostic tehnic.',
      },
      {
        href: '/setari/despre',
        label: 'Capabilități și limite',
        description: 'Ce este disponibil și ce nu este implementat.',
      },
      {
        href: '/setari/despre/plan',
        label: 'Plan de dezvoltare',
        description: 'Etapele planificate, separate de funcțiile actuale.',
      },
    ],
  },
] satisfies { title: string; items: SectionItem[] }[];

export const sectionItems: Partial<Record<Area, SectionItem[]>> = {
  settings: [
    { href: '/setari/aspect', label: 'Aspect' },
    ...settingsGroups.flatMap((group) => group.items),
  ],
  accounts: [
    { href: '/conturi', label: 'Conturi pentru simulare' },
    { href: '/conturi/siguranta', label: 'Siguranță, limite și politici aplicate' },
    { href: '/conturi/documente', label: 'Documente și programe' },
    { href: '/conturi/conexiuni', label: 'Observații broker · numai citire' },
    { href: '/conturi/avansat/inregistrari-risc', label: 'Înregistrări descriptive de risc' },
    { href: '/conturi/avansat/simulator', label: 'Simulator manual avansat' },
  ],
  research: [
    { href: '/testeaza/campanii', label: 'Campanii de cercetare' },
    { href: '/testeaza/nou', label: 'Test nou' },
    { href: '/testeaza/strategii', label: 'Strategii revizuite' },
    { href: '/testeaza/activitate', label: 'Activitatea testelor' },
    { href: '/testeaza/ai', label: 'Analizează cu AI' },
    { href: '/testeaza/date', label: 'Date pentru teste' },
    { href: '/testeaza/date/import', label: 'Adaugă date istorice' },
    { href: '/testeaza/evaluare-finala', label: 'Evaluare finală protejată' },
  ],
  results: [
    { href: '/rezultate', label: 'Rezultate stocate' },
    { href: '/rezultate/compara', label: 'Compară două teste' },
    { href: '/rezultate/simulari', label: 'Jurnale de simulare manuală' },
  ],
};

/** Visual location only; authorization remains in the authenticated modules and API. */
export function activeSection(route: Route): string | undefined {
  if (route.canonicalPath)
    return activeSection({ ...route, path: route.canonicalPath, canonicalPath: undefined });
  if (route.screen === 'ai') return route.area === 'settings' ? '/setari/ai' : '/testeaza/ai';
  if (route.area === 'research' && route.jobId) return '/testeaza/date/import';
  const items = sectionItems[route.area] ?? [];
  const direct = [...items]
    .sort((a, b) => b.href.length - a.href.length)
    .find(
      (item) =>
        route.path === item.href ||
        (item.href !== '/conturi' && route.path.startsWith(`${item.href}/`)),
    );
  if (direct) return direct.href;
  if (route.area === 'settings') return '/setari/aspect';
  if (route.area === 'research') {
    if (route.experimentId) return '/testeaza/activitate';
    return '/testeaza/nou';
  }
  if (route.area === 'accounts' && route.accountId) {
    if (route.screen === 'records') return '/conturi/avansat/inregistrari-risc';
    if (route.screen === 'broker')
      return route.path.includes('/simulator')
        ? '/conturi/avansat/simulator'
        : '/conturi/conexiuni';
    return '/conturi/siguranta';
  }
  return undefined;
}

export const areaDescriptions: Record<Area, string> = {
  home: 'Starea platformei și următorul pas.',
  research: 'Testează o idee pe date istorice, pas cu pas.',
  results: 'Înțelege rezultatele simulate și limitele lor.',
  accounts: 'Conturi de simulare, limite și verificări de siguranță.',
  settings: 'Configurează accesul, sursele de date și platforma.',
  auth: 'Acces protejat prin parolă și autentificare în doi pași.',
};
