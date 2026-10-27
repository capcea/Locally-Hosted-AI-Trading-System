import { expect, test } from '@playwright/test';
import { parseOverview } from '../src/schema';

test.beforeEach(async ({ request }) => {
  const response = await request.get('/api/v1/overview');
  expect(response.ok()).toBe(true);
  parseOverview(await response.json());
});

test('browse real status, filter services, inspect governance and roadmap', async ({
  page,
}, info) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Centrul de cercetare' })).toBeVisible();
  await expect(page.getByText('Nu există experimente rulate', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Toate serviciile și integrările' }).click();
  await page.getByRole('textbox', { name: 'Caută un serviciu' }).fill('MetaTrader');
  await expect(page.getByText('MetaTrader 5', { exact: true })).toBeVisible();
  await expect(page.getByText('cTrader Open API', { exact: true })).toHaveCount(0);
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Deschide meniul' }).click();
  await page.getByRole('button', { name: 'Siguranță & guvernanță', exact: true }).click();
  await expect(page.getByText('DENY_ALL', { exact: true })).toBeVisible();
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Deschide meniul' }).click();
  await page.getByRole('button', { name: 'Plan de implementare', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Cloud → local' })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
});

test('API outage is explicit and clears confidence in previous health', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Starea infrastructurii' })).toBeVisible();
  await page.route('**/api/v1/overview', (route) => route.abort());
  await page.getByRole('button', { name: 'Actualizează', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Conexiunea cu API-ul nu este disponibilă');
  await expect(page.locator('.service-status').first()).toHaveText('Neverificat');
});

test('orders and activation remain refused through frontend proxy', async ({ request }) => {
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate']) {
    const response = await request.post(endpoint, {
      data: { mode: 'SIMULATED', audit_probe: true },
    });
    expect(response.status()).toBe(403);
  }
});
