# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-visual.spec.ts >> non-secret public Home has reviewed light/dark visual baselines and reflows
- Location: e2e/ux-visual.spec.ts:3:1

# Error details

```
Error: expect(page).toHaveScreenshot(expected) failed

  Expected an image 1280px by 1047px, received 1280px by 1684px. 237080 pixels (ratio 0.11 of all image pixels) are different.

  Snapshot: home-light.png

Call log:
  - Expect "toHaveScreenshot(home-light.png)" with timeout 5000ms
    - verifying given screenshot expectation
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - Expected an image 1280px by 1047px, received 1280px by 1684px. 237080 pixels (ratio 0.11 of all image pixels) are different.
  - waiting 100ms before taking screenshot
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - captured a stable screenshot
  - Expected an image 1280px by 1047px, received 1280px by 1684px. 237080 pixels (ratio 0.11 of all image pixels) are different.

```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test';
  2  | 
  3  | test('non-secret public Home has reviewed light/dark visual baselines and reflows', async ({
  4  |   page,
  5  | }) => {
  6  |   // Capture ONLY the signed-out public page. Auth/recovery capture remains globally disabled.
  7  |   const clock = page.locator('time[data-visual-clock]');
  8  |   await page.goto('/');
  9  |   await expect(page.getByRole('heading', { name: 'Acasă', exact: true })).toBeVisible();
  10 |   await expect(clock).toBeVisible();
  11 |   await expect(page.locator('input[type=password],.enrollment-secret,.recovery-codes')).toHaveCount(
  12 |     0,
  13 |   );
  14 |   for (const theme of ['light', 'dark']) {
  15 |     await page.evaluate((value) => {
  16 |       localStorage.setItem('research-theme', value);
  17 |     }, theme);
  18 |     await page.reload();
  19 |     await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
  20 |     await expect(clock).toBeVisible();
  21 |     await expect(clock).toHaveText(/^[0-9]{2}:[0-9]{2}:[0-9]{2}$/);
  22 |     await expect(clock).toHaveAttribute('datetime', /^\d{4}-\d{2}-\d{2}T/);
  23 |     expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(
  24 |       false,
  25 |     );
> 26 |     await expect(page).toHaveScreenshot(`home-${theme}.png`, {
     |                        ^ Error: expect(page).toHaveScreenshot(expected) failed
  27 |       fullPage: true,
  28 |       animations: 'disabled',
  29 |       mask: [clock],
  30 |     });
  31 |   }
  32 |   // A real public refresh changes the observed instant, never the mask's geometry.
  33 |   const previousRead = await clock.getAttribute('datetime');
  34 |   const previousBounds = await clock.boundingBox();
  35 |   expect(previousBounds).not.toBeNull();
  36 |   const refreshed = page.waitForResponse(
  37 |     (response) =>
  38 |       new URL(response.url()).pathname === '/api/v1/overview' &&
  39 |       response.request().method() === 'GET',
  40 |   );
  41 |   await page.getByRole('button', { name: 'Actualizează starea publică', exact: true }).click();
  42 |   expect((await refreshed).status()).toBe(200);
  43 |   await expect(clock).not.toHaveAttribute('datetime', previousRead!);
  44 |   const refreshedBounds = await clock.boundingBox();
  45 |   expect(refreshedBounds).not.toBeNull();
  46 |   // The button may scroll into view; compare dimensions, not viewport-relative y coordinates.
  47 |   expect([refreshedBounds!.width, refreshedBounds!.height]).toEqual([
  48 |     previousBounds!.width,
  49 |     previousBounds!.height,
  50 |   ]);
  51 |   await page.setViewportSize({ width: 320, height: 800 });
  52 |   expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  53 |   const nav = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  54 |   await expect(nav.getByRole('link')).toHaveCount(5);
  55 |   for (const link of await nav.getByRole('link').all()) {
  56 |     const bounds = await link.boundingBox();
  57 |     expect(bounds?.height).toBeGreaterThanOrEqual(44);
  58 |   }
  59 | });
  60 | 
```