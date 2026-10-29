import { expect, test } from '@playwright/test';
import { realPost, seedRiskFixture, totp } from './risk-fixture';
import { configureRisk } from './risk-workflow';

test('independent safety, reviewed setup, guarded routes, keyboard review and viewer isolation', async ({
  page,
}, info) => {
  test.setTimeout(180000);
  const { account } = await seedRiskFixture(page, info.project.name === 'mobile');
  const me = await (await page.request.get('/api/v1/auth/me')).json();
  expect(me.state).toBe('FULL');
  await page.route('**/api/v1/overview', (route) => route.abort());
  // Outage diagnostics remain visible on the public diagnostic route (not the isolated home iframe).
  await page.goto('/setari/diagnostic');
  await expect(page.getByRole('alert').first()).toContainText(
    'Conexiunea cu API-ul nu este disponibilă',
  );
  await expect(
    page.getByRole('complementary', { name: 'Siguranță risc globală', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('navigation', { name: 'Navigare principală', exact: true })
    .getByRole('link', { name: 'Siguranță', exact: true })
    .click();
  const center = page.getByRole('region', { name: 'Centru de risc', exact: true });
  await center
    .getByLabel('Cont pentru controlul riscului', { exact: true })
    .selectOption(account.id);
  await expect(
    center.getByRole('button', { name: 'Oprește intrările noi simulate', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Aplică acțiunea de siguranță', exact: true }),
  ).toHaveCount(0);
  const stop = center.getByRole('button', { name: 'Oprește intrările noi simulate', exact: true });
  await stop.focus();
  await expect(stop).toBeFocused();
  await page.keyboard.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Oprește intrările noi simulate', exact: true });
  await expect(dialog).toContainText('Pozițiile existente nu se închid automat');
  await expect(dialog).toContainText(account.id);
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(stop).toBeFocused();
  await page.route(`**/api/v1/risk/accounts/${account.id}/status`, (route) => route.abort());
  await page.goto(`/conturi/${account.id}/siguranta`);
  await expect(center).toContainText('UNAVAILABLE');
  await center.getByRole('button', { name: 'Oprește intrările noi simulate', exact: true }).click();
  await expect(
    page
      .getByRole('dialog')
      .getByRole('button', { name: 'Confirmă oprește intrările noi simulate', exact: true }),
  ).toBeDisabled();
  await page.keyboard.press('Escape');
  await page.unroute(`**/api/v1/risk/accounts/${account.id}/status`);
  await page.unroute('**/api/v1/overview');
  await page.goto('/testeaza/nou');
  const wizard = page.getByRole('form', { name: 'Configurează testul istoric', exact: true });
  await wizard.getByLabel('Contul testului', { exact: true }).selectOption(account.id);
  await expect(wizard.getByRole('button', { name: 'Continuă', exact: true })).toBeDisabled();
  await expect(
    wizard.getByRole('link', { name: 'Verifică ori importă date istorice', exact: true }),
  ).toBeVisible();
  await wizard
    .getByRole('link', { name: 'Verifică ori importă date istorice', exact: true })
    .click();
  await expect(page).toHaveURL(/\/testeaza\/date\/import$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/testeaza\/nou$/);
  await expect(wizard.getByLabel('Contul testului', { exact: true })).toHaveValue(account.id);
  await page.reload();
  await expect(wizard).toBeVisible(); // auth survives; memory drafts do not claim durable storage
  await page.goto('/testeaza');
  await expect(wizard).toHaveCount(1);
  await expect(wizard).toBeVisible();
  // Advanced routes remain navigable via the collapsible section navigator.
  await page.locator('.cockpit-page-tools summary').click();
  await expect(
    page
      .getByRole('navigation', { name: 'În această secțiune', exact: true })
      .getByRole('link', { name: 'Test nou', exact: true }),
  ).toHaveAttribute('aria-current', 'page');
  await configureRisk(page, 'Cont risc E2E', 'Scenariu risc E2E');
  const before = await (
    await page.request.get(`/api/v1/risk/accounts/${account.id}/profiles`)
  ).json();
  await realPost(page, '/records/risk-profiles', {
    kind: 'risk-profiles',
    name: 'Doar metadate',
    account_id: account.id,
    per_trade_pct: '.1',
    daily_loss_pct: '1',
    total_loss_pct: '3',
    aggregate_risk_pct: '1',
    source: 'SYNTHETIC_TEST_FIXTURE',
  });
  await page.goto('/conturi/avansat/inregistrari-risc');
  await expect(
    page.getByText('Înregistrări descriptive — nu aplică limite.', { exact: true }),
  ).toBeVisible();
  expect(
    await (await page.request.get(`/api/v1/risk/accounts/${account.id}/profiles`)).json(),
  ).toEqual(before);
  await page.goto('/testeaza/evaluare-finala');
  await expect(
    page.getByRole('region', { name: 'Evaluare finală protejată', exact: true }),
  ).toContainText('Expunerea anterioară este necunoscută');
  await expect(
    page.getByRole('button', { name: 'Autorizează evaluarea finală unică', exact: true }),
  ).toHaveCount(0);
  const viewerPassword = process.env.E2E_OWNER_PASSWORD! + '-viewer';
  await realPost(page, '/auth/users', {
    username: 'ux-viewer',
    display_name: 'Cititor UX sintetic',
    password: viewerPassword,
    role: 'VIEWER',
  });
  await page.getByRole('button', { name: 'Deconectare', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('ux-viewer');
  await page.getByLabel('Parolă', { exact: true }).fill(viewerPassword);
  await page.getByRole('button', { name: 'Continuă cu parola', exact: true }).click();
  await page.getByRole('button', { name: 'Configurează autentificatorul', exact: true }).click();
  const secret = (await page.locator('.enrollment-secret code').textContent())!.trim();
  await page.getByLabel('Cod MFA', { exact: true }).fill(totp(secret));
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  await page.getByRole('button', { name: 'Am salvat codurile', exact: true }).click();
  await expect(
    page.getByText('Doar proprietarul cu MFA recent poate autoriza evaluarea finală.', {
      exact: false,
    }),
  ).toBeVisible();
  await page.goto('/conturi');
  await expect(
    page.getByText(
      'Rolul Doar citire permite inspectarea înregistrărilor, nu salvarea sau schimbarea lor.',
      { exact: true },
    ),
  ).toBeVisible();
  expect((await page.request.get(`/api/v1/records/accounts/${account.id}`)).status()).toBe(404);
  await page.goto('/setari/utilizatori');
  await expect(
    page.getByText('Doar proprietarul poate administra identități și roluri.', { exact: false }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'Toate setările', exact: true }).click();
  await expect(page).toHaveURL(/\/setari$/);
  for (const label of ['Cont și acces', 'Date și cercetare', 'Platformă'])
    await expect(page.getByRole('region', { name: label, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Utilizatori și roluri', exact: false }).click();
  await expect(page).toHaveURL(/\/setari\/utilizatori$/);
  await expect(
    page.getByText('Doar proprietarul poate administra identități și roluri.', { exact: false }),
  ).toBeVisible();
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate'])
    expect((await page.request.post(endpoint, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});
