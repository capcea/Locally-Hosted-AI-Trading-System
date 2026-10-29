import { Link } from './history';
import type { Route } from './routes';
import { activeSection, sectionItems, settingsGroups } from './sections';

export function SectionNavigation({
  route,
  authenticated,
}: {
  route: Route;
  authenticated: boolean;
}) {
  let items = sectionItems[route.area];
  if (!items?.length || (route.screen === 'settings' && authenticated)) return null;
  const active = activeSection(route);
  if (route.screen === 'settings') {
    // Keep public diagnostic/about/roadmap navigation reachable without exposing protected settings.
    items = settingsGroups.find((group) => group.title === 'Platformă')!.items;
  } else if (route.area === 'settings') {
    const group = settingsGroups.find((g) => g.items.some((item) => item.href === active));
    if (group) items = [{ href: '/setari', label: 'Toate setările' }, ...group.items];
  }
  return (
    <nav className="section-navigation" aria-label="În această secțiune">
      <ul>
        {items.map(({ href, label }) => (
          <li key={href}>
            <Link href={href} aria-current={active === href ? 'page' : undefined}>
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
