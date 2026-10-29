import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { parseOverview } from '../src/schema';
import type { Overview } from '../src/api';

async function assertObservedSidebar(page: Page, overview: Overview) {
  const sidebar = page.getByRole('region', { name: 'Starea tehnică a sistemului', exact: true });
  for (const id of ['api', 'postgres', 'redis', 'storage']) {
    const service = overview.services.find((item) => item.id === id);
    const expected =
      service?.status === 'HEALTHY'
        ? 'HEALTHY'
        : ['UNAVAILABLE', 'DISABLED'].includes(service?.status ?? '')
          ? 'DOWN'
          : 'UNKNOWN';
    await expect(sidebar.locator(`[data-service="${id}"]`)).toHaveAttribute(
      'data-status',
      expected,
    );
  }
}

test.beforeEach(async ({ request }) => {
  const response = await request.get('/api/v1/overview');
  expect(response.ok()).toBe(true);
  parseOverview(await response.json());
});

test('browse real status, filter services, inspect governance and roadmap', async ({ page }) => {
  const observed = page.waitForResponse((r) => r.url().endsWith('/api/v1/overview') && r.ok());
  await page.goto('/');
  await assertObservedSidebar(page, parseOverview(await (await observed).json()));
  await expect(page.getByRole('heading', { name: 'Acasă', exact: true })).toBeVisible();
  const primary = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  await expect(primary.getByRole('link')).toHaveCount(5);
  await expect(
    page.getByText('Nu afișăm rezultate sau solduri presupuse.', { exact: false }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'Vezi diagnostic', exact: true }).click();
  await page.getByRole('textbox', { name: 'Caută un serviciu' }).fill('MetaTrader');
  await expect(page.getByText('MetaTrader 5', { exact: true })).toBeVisible();
  await expect(page.getByText('cTrader Open API', { exact: true })).toHaveCount(0);
  await primary.getByRole('link', { name: 'Setări', exact: true }).click();
  await page
    .getByRole('navigation', { name: 'În această secțiune' })
    .getByRole('link', { name: 'Capabilități și limite', exact: true })
    .click();
  await expect(page.getByText('DENY_ALL', { exact: true })).toBeVisible();
  await page
    .getByRole('navigation', { name: 'În această secțiune' })
    .getByRole('link', { name: 'Plan de dezvoltare', exact: true })
    .click();
  await expect(page.getByRole('heading', { name: 'Cloud → local' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
});

test('API outage is explicit and clears confidence in previous health', async ({ page }) => {
  await page.goto('/setari/diagnostic');
  await expect(
    page.getByRole('heading', { name: 'Starea serviciilor', exact: true }),
  ).toBeVisible();
  await expect(page.locator('.service-status').first()).toBeVisible();
  await page.route('**/api/v1/overview', (route) => route.abort());
  await page.getByRole('button', { name: 'Actualizează starea publică', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Conexiunea cu API-ul nu este disponibilă');
  await expect(page.locator('.service-status').first()).toHaveText('Neverificat');
  const sidebar = page.getByRole('region', { name: 'Starea tehnică a sistemului', exact: true });
  await expect(sidebar.locator('[data-service][data-status="UNKNOWN"]')).toHaveCount(4);
  await page.unroute('**/api/v1/overview');
  const recovered = page.waitForResponse((r) => r.url().endsWith('/api/v1/overview') && r.ok());
  await sidebar.getByRole('button', { name: 'Verifică din nou', exact: true }).click();
  await assertObservedSidebar(page, parseOverview(await (await recovered).json()));
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('orders and activation remain refused through frontend proxy', async ({ request }) => {
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate']) {
    const response = await request.post(endpoint, {
      data: { mode: 'SIMULATED', audit_probe: true },
    });
    expect(response.status()).toBe(403);
  }
});
