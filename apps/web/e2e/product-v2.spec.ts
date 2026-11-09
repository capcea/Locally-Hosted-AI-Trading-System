import { expect, test } from '@playwright/test';

test('password-only owner uses the three-destination product without MFA or invented trading', async ({
  page,
}) => {
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  )
    throw new Error('Use the disposable product browser scenario.');
  await page.goto('/');
  await page.getByLabel('Nume utilizator', { exact: true }).fill('product-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(process.env.E2E_OWNER_PASSWORD);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar produs E2E');
  await page
    .getByLabel('Codul privat de configurare', { exact: true })
    .fill(process.env.E2E_SETUP_TOKEN);
  const saved = page.waitForResponse(
    (r) => r.url().endsWith('/auth/bootstrap') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Creează proprietarul', exact: true }).click();
  expect((await saved).status()).toBe(201);
  expect((await (await page.request.get('/api/v1/auth/me')).json()).auth_mode).toBe('PASSWORD');
  await expect(page.getByRole('region', { name: 'Trading Dashboard', exact: true })).toBeVisible();
  const nav = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  await expect(nav.locator('.cockpit-nav-link')).toHaveCount(3);
  await expect(
    page.getByRole('button', { name: 'Configurează autentificatorul', exact: true }),
  ).toHaveCount(0);
  await expect(page.getByLabel('Cod MFA', { exact: true })).toHaveCount(0);
  await nav.getByRole('link', { name: 'Strategy Lab', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'De la o idee la o strategie testată', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('region', { name: 'Asistent AI Strategy Lab', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('navigation', { name: 'Fluxul Strategy Lab', exact: true })
    .getByRole('link', { name: 'Biblioteca validată', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Nicio strategie validată în această pagină', exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/strategy-lab$/);
  await nav.getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Configurează platforma pas cu pas', exact: true }),
  ).toBeVisible();
  await page.goto('/setari/securitate');
  await expect(page.getByText('Nu sunt necesare coduri MFA.', { exact: false })).toBeVisible();
  await expect(page.getByLabel('Cod MFA', { exact: true })).toHaveCount(0);
  await page.reload();
  expect((await (await page.request.get('/api/v1/auth/me')).json()).state).toBe('FULL');
  await page.getByRole('button', { name: 'Deconectare', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('product-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(process.env.E2E_OWNER_PASSWORD);
  await page.getByRole('button', { name: 'Autentificare', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Securitatea contului', exact: true }),
  ).toBeVisible();
  const safety = await (await page.request.get('/api/v1/safety')).json();
  expect(safety.executor_capability).toBe('DENY_ALL');
  expect(safety.generated_code_execution).toBe(false);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});
