import { expect, test } from '@playwright/test';

test('public AI Cockpit keeps exact dark design tokens, safe states and mobile navigation', async ({
  page,
}) => {
  await page.goto('/');
  const cockpit = page.frameLocator('iframe[title="Local AI — AI Cockpit"]');
  await expect(cockpit.getByRole('heading', { name: 'Inteligență. Fără zgomot.' })).toBeVisible();
  await expect(cockpit.locator('.mode-banner')).toContainText('SIMULATED / DENY_ALL');
  await expect(page.locator('input[type=password],.enrollment-secret,.recovery-codes')).toHaveCount(
    0,
  );
  for (const theme of ['light', 'dark']) {
    await page.evaluate((value) => localStorage.setItem('research-theme', value), theme);
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    const bodyBackground = await cockpit
      .locator('body')
      .evaluate((element) => getComputedStyle(element).backgroundColor);
    expect(bodyBackground).toBe('rgb(9, 13, 20)');
    await expect(cockpit.locator('.sidebar')).toBeVisible();
    await expect(cockpit.locator('.hero')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(
      false,
    );
  }
  // Public availability is still verifiable and manually refreshable without authentication.
  await page.goto('/setari/diagnostic');
  await expect(
    page.getByRole('heading', { name: 'Starea serviciilor', exact: true }),
  ).toBeVisible();
  const refreshed = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === '/api/v1/overview' &&
      response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: 'Actualizează starea publică', exact: true }).click();
  expect((await refreshed).status()).toBe(200);

  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  const nav = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  const primary = nav.locator('.cockpit-nav-link');
  await expect(primary).toHaveCount(5);
  for (const link of await primary.all()) {
    const bounds = await link.boundingBox();
    expect(bounds?.height).toBeGreaterThanOrEqual(44);
  }
});
