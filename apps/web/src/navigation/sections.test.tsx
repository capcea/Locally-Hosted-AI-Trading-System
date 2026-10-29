import { expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { resolveRoute } from './routes';
import { activeSection, sectionItems, settingsGroups } from './sections';
import { SectionNavigation } from './SectionNavigation';

const id = '11111111-1111-4111-8111-111111111111';
it.each([
  ['/testeaza', '/testeaza/nou'],
  [`/testeaza/${id}/progres`, '/testeaza/activitate'],
  [`/testeaza/date/importuri/${id}`, '/testeaza/date/import'],
  [`/testeaza/date/${id}/provenienta`, '/testeaza/date'],
  [`/conturi/${id}/politici`, '/conturi/siguranta'],
  [`/conturi/${id}/avansat/simulator/${id}/ordine`, '/conturi/avansat/simulator'],
  [`/rezultate/${id}/provenienta`, '/rezultate'],
  ['/setari/despre/plan', '/setari/despre/plan'],
])('keeps the current task identifiable on deep/reloaded route %s', (path, expected) => {
  const route = resolveRoute(path);
  expect(activeSection(route)).toBe(expected);
  const markup = renderToStaticMarkup(<SectionNavigation route={route} authenticated />);
  const current = markup.match(/<a\b[^>]*aria-current="page"[^>]*>/g);
  expect(current).toHaveLength(1);
  expect(current![0]).toContain(`href="${expected}"`);
});
it('keeps every grouped destination on the finite route allowlist', () => {
  for (const item of Object.values(sectionItems).flat())
    expect(resolveRoute(item.href).screen).not.toBe('not-found');
  expect(settingsGroups.flatMap((g) => g.items)).toHaveLength(10);
  expect(resolveRoute('/testeaza/ai').screen).toBe('ai');
  expect(resolveRoute('/setari/ai').screen).toBe('ai');
});
it('offers the current settings group and a way back to all settings', () => {
  const markup = renderToStaticMarkup(
    <SectionNavigation route={resolveRoute('/setari/securitate')} authenticated />,
  );
  expect(markup).toContain('href="/setari"');
  expect(markup).toContain('Utilizatori și roluri');
  expect(markup).toContain('Istoric verificabil');
  expect(markup).not.toContain('href="/setari/surse"');
});

it('keeps public diagnostic/about/roadmap links reachable from signed-out Settings', () => {
  const markup = renderToStaticMarkup(
    <SectionNavigation route={resolveRoute('/setari')} authenticated={false} />,
  );
  for (const path of ['/setari/diagnostic', '/setari/despre', '/setari/despre/plan'])
    expect(markup).toContain(`href="${path}"`);
  expect(markup).not.toContain('href="/setari/securitate"');
});
