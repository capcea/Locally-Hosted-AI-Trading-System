import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { expect, test } from '@playwright/test';
import { seedRiskFixture } from './risk-fixture';

test('approved V1 nine screens retain real setup, scoped search, navigation and responsive safety', async ({
  page,
}, info) => {
  test.setTimeout(240000);
  const captures = process.env.E2E_V1_CAPTURES === '1';
  const folder = resolve(process.cwd(), '../../.cache/redesign-v1-captures');
  if (captures) {
    expect(process.env.E2E_PHASE1_ISOLATED).toBe('1');
    await mkdir(folder, { recursive: true });
    // Capture the approved signed-out Cockpit, never authentication or recovery pages.
    await page.goto('/');
    const cockpit = page.frameLocator('iframe[title="Local AI — AI Cockpit"]');
    await expect(cockpit.locator('.mode-banner')).toContainText('SIMULATED / DENY_ALL');
    await expect(page.locator('input[type=password],.enrollment-secret,.recovery-codes')).toHaveCount(0);
    await page.screenshot({
      path: resolve(folder, `PUBLIC-REVIEW-cockpit-${info.project.name}-${process.platform}.png`),
      fullPage: true,
      animations: 'disabled',
    });
  }
  const { account } = await seedRiskFixture(page, info.project.name === 'mobile');
  const library = await page.request.get('/api/v1/research/strategies');
  expect(library.status()).toBe(200);
  const definitions: { id: string }[] = await library.json();
  expect(definitions.length).toBeGreaterThan(0);
  await page.goto('/testeaza/strategii');
  const table = page.getByRole('region', { name: 'Biblioteca strategiilor', exact: true });
  await expect(table.locator('tbody tr')).toHaveCount(definitions.length);
  const search = page.getByLabel('Caută o strategie', { exact: true });
  await search.fill(definitions[0].id);
  await expect(table.locator('tbody tr')).toHaveCount(1);
  await table.getByRole('button', { name: 'Testează strategia', exact: true }).click();
  await expect(page).toHaveURL(/\/testeaza\/nou$/);
  const wizard = page.getByRole('form', { name: 'Configurează testul istoric', exact: true });
  await expect(wizard).toBeVisible();
  await wizard.getByLabel('Contul testului', { exact: true }).selectOption(account.id);
  await expect(wizard.getByRole('button', { name: 'Continuă', exact: true })).toBeDisabled();
  await expect(
    page.getByRole('complementary', { name: 'Revizuirea testului', exact: true }),
  ).toContainText('Necesită verificare');
  await page.goBack();
  await expect(page).toHaveURL(/\/testeaza\/strategii$/);
  await page.goForward();
  await expect(wizard).toBeVisible();
  // The simplified Cockpit navigation replaces the legacy global search panel.
  const mainNav = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  await expect(mainNav.locator('.cockpit-nav-link')).toHaveCount(5);
  await expect(mainNav.getByRole('link', { name: 'AI & Teste', exact: true })).toBeVisible();

  const screens = [
    ['home', '/', 'Inteligență. Fără zgomot.'],
    ['strategii', '/testeaza/strategii', 'Strategii'],
    ['backtesting', '/testeaza/nou', 'Backtesting'],
    ['experimente', '/testeaza/activitate', 'Experimente'],
    ['ai', '/testeaza/ai', 'AI Center'],
    ['rezultate', '/rezultate', 'Rezultate'],
    ['conturi', `/conturi/${account.id}/siguranta`, 'Conturi și siguranță'],
    ['modele', '/setari/ai', 'Setări · Modele AI'],
    ['platforma', '/setari', 'Setări · Platformă'],
  ];
  for (const theme of ['light', 'dark']) {
    await page.evaluate((value) => localStorage.setItem('research-theme', value), theme);
    for (const viewport of [
      { width: 1672, height: 941 },
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 390, height: 844 },
      { width: 360, height: 800 },
    ]) {
      await page.setViewportSize(viewport);
      for (const [name, path, title] of screens) {
        await test.step(`${theme} ${viewport.width} ${name}`, async () => {
          await page.goto(path);
          if (name === 'home') {
            const cockpit = page.frameLocator('iframe[title="Local AI — AI Cockpit"]');
            await expect(cockpit.getByRole('heading', { name: title, exact: true })).toBeVisible();
            await expect(cockpit.locator('.mode-banner')).toContainText('SIMULATED / DENY_ALL');
            await expect(cockpit.locator('.nav-list .nav-item')).toHaveCount(5);
          } else {
            await expect(page.getByRole('heading', { name: title, exact: true, level: 1 })).toBeVisible();
            await expect(page.getByRole('complementary', { name: 'Siguranță risc globală', exact: true })).toBeVisible();
            await expect(page.locator('.cockpit-simulation-notice')).toContainText('SIMULATED / DENY_ALL');
            await expect(page.getByRole('navigation', { name: 'Navigare principală', exact: true }).locator('.cockpit-nav-link')).toHaveCount(5);
          }
          await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
          expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
          if (name === 'ai')
            await expect(
              page.getByRole('button', { name: 'Solicită analiza', exact: true }),
            ).toBeDisabled();
          if (name === 'home' && viewport.width >= 1280) {
            const cockpit = page.frameLocator('iframe[title="Local AI — AI Cockpit"]');
            await expect(cockpit.locator('.hero')).toBeVisible();
            const hero = await cockpit.locator('.hero').boundingBox();
            const stats = await cockpit.locator('.stats').boundingBox();
            expect(hero).not.toBeNull();
            expect(stats).not.toBeNull();
            expect(stats!.y).toBeGreaterThan(hero!.y);
          }
          if (name === 'conturi')
            for (const label of [
              'Oprește intrările noi simulate',
              'Revizuiește și deblochează intrările',
              'Închide pozițiile simulate',
            ])
              await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible();
          // Explicit owner-local opt-in only. Disposable fixture data, no authentication/recovery captures.
          if (captures) {
            expect(process.env.E2E_PHASE1_ISOLATED).toBe('1');
            expect((await (await page.request.get('/api/v1/auth/me')).json()).state).toBe('FULL');
            await expect(
              page.locator(
                'input[type=password],.enrollment-secret,.recovery-codes,input[autocomplete="one-time-code"]',
              ),
            ).toHaveCount(0);
            await page.evaluate(() => document.fonts.ready);
            await page.screenshot({
              path: resolve(
                folder,
                `SYNTHETIC_FIXTURE-${info.project.name}-${name}-${theme}-${viewport.width}x${viewport.height}.png`,
              ),
              fullPage: true,
              animations: 'disabled',
                          });
          }
        });
      }
    }
  }
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Setări · Platformă', level: 1, exact: true }),
  ).toBeVisible();
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate'])
    expect((await page.request.post(endpoint, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
});
