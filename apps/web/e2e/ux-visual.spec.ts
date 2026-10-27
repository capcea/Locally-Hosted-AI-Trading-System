import { expect, test } from '@playwright/test';

test('non-secret public Home has reviewed light/dark visual baselines and reflows', async ({
  page,
}) => {
  // Capture ONLY the signed-out public page. Auth/recovery capture remains globally disabled.
  const clock = page.locator('time[data-visual-clock]');
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Acasă', exact: true })).toBeVisible();
  await expect(clock).toBeVisible();
  await expect(page.locator('input[type=password],.enrollment-secret,.recovery-codes')).toHaveCount(
    0,
  );
  for (const theme of ['light', 'dark']) {
    await page.evaluate((value) => {
      localStorage.setItem('research-theme', value);
    }, theme);
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(clock).toBeVisible();
    await expect(clock).toHaveText(/^[0-9]{2}:[0-9]{2}:[0-9]{2}$/);
    await expect(clock).toHaveAttribute('datetime', /^\d{4}-\d{2}-\d{2}T/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(
      false,
    );
    await expect(page).toHaveScreenshot(`home-${theme}.png`, {
      fullPage: true,
      animations: 'disabled',
      mask: [clock],
    });
  }
  // A real public refresh changes the observed instant, never the mask's geometry.
  const previousRead = await clock.getAttribute('datetime');
  const previousBounds = await clock.boundingBox();
  expect(previousBounds).not.toBeNull();
  const refreshed = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === '/api/v1/overview' &&
      response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: 'Actualizează starea publică', exact: true }).click();
  expect((await refreshed).status()).toBe(200);
  await expect(clock).not.toHaveAttribute('datetime', previousRead!);
  const refreshedBounds = await clock.boundingBox();
  expect(refreshedBounds).not.toBeNull();
  // The button may scroll into view; compare dimensions, not viewport-relative y coordinates.
  expect([refreshedBounds!.width, refreshedBounds!.height]).toEqual([
    previousBounds!.width,
    previousBounds!.height,
  ]);
  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  const nav = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  await expect(nav.getByRole('link')).toHaveCount(5);
  for (const link of await nav.getByRole('link').all()) {
    const bounds = await link.boundingBox();
    expect(bounds?.height).toBeGreaterThanOrEqual(44);
  }
});
