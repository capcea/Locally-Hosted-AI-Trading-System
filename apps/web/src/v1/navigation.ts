import type { Route } from '../navigation/routes';
export const researchLinks = [
  { href: '/testeaza/strategii', label: 'Strategii' },
  { href: '/testeaza/nou', label: 'Backtesting' },
  { href: '/testeaza/activitate', label: 'Experimente' },
  { href: '/testeaza/ai', label: 'AI Center' },
  { href: '/testeaza/campanii', label: 'Campanii' },
];
export const platformLinks = [
  { href: '/setari/ai', label: 'Modele AI' },
  { href: '/setari/surse', label: 'Date și piață' },
  { href: '/conturi/conexiuni', label: 'Conexiuni' },
  { href: '/conturi/avansat/simulator', label: 'Simulator' },
  { href: '/setari/utilizatori', label: 'Utilizatori și acces' },
  { href: '/setari', label: 'Platformă' },
];
export const pageTitles = (route: Route): string => {
  if (route.screen === 'home') return 'Acasă';
  if (route.screen === 'campaigns') return 'Campanii de cercetare';
  if (route.screen === 'ai') return route.area === 'settings' ? 'Setări · Modele AI' : 'AI Center';
  if (route.screen === 'research') {
    if (route.area === 'results')
      return route.section === 'compare' ? 'Compară rezultate' : 'Rezultate';
    return (
      (
        {
          strategii: 'Strategii',
          activitate: 'Experimente',
          progress: 'Progresul testului',
          'evaluare-finala': 'Evaluare finală protejată',
        } as Record<string, string>
      )[route.section ?? ''] ?? 'Backtesting'
    );
  }
  if (route.area === 'accounts') return 'Conturi și siguranță';
  if (route.screen === 'settings') return 'Setări · Platformă';
  if (route.screen === 'data')
    return route.section === 'import' ? 'Adaugă date istorice' : 'Date și piață';
  if (route.screen === 'security')
    return route.section === 'utilizatori' ? 'Utilizatori și acces' : 'Securitate și MFA';
  if (route.screen === 'audit') return 'Istoric verificabil';
  if (route.screen === 'not-found') return 'Pagina nu există';
  // Retained diagnostic modules own their detailed h2 heading, avoiding duplicate exact landmarks.
  if (route.area === 'settings') return 'Setări';
  return 'Autentificare';
};
