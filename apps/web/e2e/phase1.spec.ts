import { createHmac } from 'node:crypto';
import { expect, test } from '@playwright/test';

// Independent RFC 6238 test client; production verification uses PyOTP and persisted counters.
function totp(secret: string, offsetSeconds = 0): string {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = [...secret]
    .map((letter) => alphabet.indexOf(letter).toString(2).padStart(5, '0'))
    .join('');
  const key = Buffer.from((bits.match(/.{8}/g) ?? []).map((byte) => parseInt(byte, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor((Date.now() / 1000 + offsetSeconds) / 30)));
  const digest = createHmac('sha1', key).update(counter).digest();
  const offset = digest[digest.length - 1] & 15;
  return ((digest.readUInt32BE(offset) & 0x7fffffff) % 1_000_000).toString().padStart(6, '0');
}

test('owner setup, MFA, persistent account/risk/policy management, settings, audit and login', async ({
  page,
}) => {
  test.setTimeout(120_000);
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  ) {
    throw new Error(
      'Phase 1 browser tests require make browser-integration and disposable credentials. No ambient account is used.',
    );
  }
  const password = process.env.E2E_OWNER_PASSWORD;
  const setupToken = process.env.E2E_SETUP_TOKEN;
  await page.goto('/');
  await page.goto('/conturi');
  await page.getByLabel('Nume utilizator', { exact: true }).fill('browser-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(password);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar sintetic E2E');
  await page.getByLabel('Codul privat de configurare', { exact: true }).fill(setupToken);
  await page.getByRole('button', { name: 'Creează proprietarul', exact: true }).click();
  await page.getByRole('button', { name: 'Configurează autentificatorul' }).click();
  await expect(page.locator('.enrollment-secret code')).toBeVisible();
  const secret = (await page.locator('.enrollment-secret code').textContent())?.trim();
  if (!secret) throw new Error('MFA enrollment secret was not supplied');
  await page.getByLabel('Cod MFA', { exact: true }).fill(totp(secret));
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  await expect(page.locator('.recovery-codes code')).toHaveCount(10);
  await page.getByRole('button', { name: 'Am salvat codurile' }).click();

  await page.goto('/conturi/documente');
  const programForm = page.locator('form').filter({ has: page.locator('input[name=phase]') });
  await programForm.getByLabel('Originea înregistrării').selectOption('SYNTHETIC_TEST_FIXTURE');
  await programForm.getByLabel('Denumire', { exact: true }).fill('Program sintetic E2E');
  await programForm.getByLabel('Firmă', { exact: true }).selectOption({ label: 'FTMO' });
  await programForm.getByLabel('Etapă', { exact: true }).fill('SYNTHETIC_TEST_FIXTURE');
  await programForm.getByLabel('Platformă', { exact: true }).fill('Fără broker');
  await programForm.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Program sintetic E2E', exact: true }),
  ).toBeVisible();

  await page.goto('/conturi');
  await page.getByLabel('Originea înregistrării').selectOption('SYNTHETIC_TEST_FIXTURE');
  await page.getByLabel('Denumire', { exact: true }).fill('Cont sintetic E2E');
  await page.getByLabel('Monedă', { exact: true }).fill('USD');
  await page.getByLabel('Capital declarat pentru simulare', { exact: true }).fill('25000.12345678');
  await page.getByLabel('Program', { exact: true }).selectOption({ label: 'Program sintetic E2E' });
  await page.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Cont sintetic E2E', exact: true })).toBeVisible();
  await expect(page.getByText('25000.12345678', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Editează Cont sintetic E2E', exact: true }).click();
  await page.getByLabel('Denumire', { exact: true }).fill('Cont persistent E2E');
  await page.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Cont persistent E2E', exact: true }),
  ).toBeVisible();

  await page.goto('/conturi/avansat/inregistrari-risc');
  await expect(
    page.getByText('Înregistrări descriptive — nu aplică limite.', { exact: true }),
  ).toBeVisible();
  await page.getByLabel('Originea înregistrării').selectOption('SYNTHETIC_TEST_FIXTURE');
  await page.getByLabel('Denumire', { exact: true }).fill('Profil sintetic E2E');
  await page.getByLabel('Cont', { exact: true }).selectOption({ label: 'Cont persistent E2E' });
  for (const [label, value] of [
    ['Risc pe tranzacție (%)', '0.25'],
    ['Pierdere zilnică (%)', '1'],
    ['Pierdere totală (%)', '3'],
    ['Risc agregat (%)', '1'],
  ]) {
    await page.getByLabel(label, { exact: true }).fill(value);
  }
  await page.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Profil sintetic E2E', exact: true }),
  ).toBeVisible();

  await page.goto('/conturi/documente');
  const policyForm = page
    .locator('form')
    .filter({ has: page.locator('input[name=document_digest]') });
  await policyForm.getByLabel('Originea înregistrării').selectOption('SYNTHETIC_TEST_FIXTURE');
  await policyForm.getByLabel('Denumire', { exact: true }).fill('Politică sintetică E2E');
  await policyForm
    .getByLabel('Cont', { exact: true })
    .selectOption({ label: 'Cont persistent E2E' });
  await policyForm
    .getByLabel('Program', { exact: true })
    .selectOption({ label: 'Program sintetic E2E' });
  await policyForm.getByLabel('Versiune', { exact: true }).fill('1');
  await policyForm
    .getByLabel('Adresa documentului sursă', { exact: true })
    .fill('https://example.invalid/synthetic-policy');
  await policyForm
    .getByLabel('Amprenta SHA-256 a documentului', { exact: true })
    .fill('a'.repeat(64));
  await policyForm
    .getByLabel('Începutul valabilității', { exact: true })
    .fill(new Date(Date.now() - 86400000).toISOString().slice(0, 16));
  await policyForm
    .getByLabel('Expirare', { exact: true })
    .fill(new Date(Date.now() + 86400000).toISOString().slice(0, 16));
  await policyForm.getByRole('button', { name: 'Salvează', exact: true }).click();
  const policy = page
    .locator('.management-record')
    .filter({ has: page.getByRole('heading', { name: 'Politică sintetică E2E', exact: true }) });
  await expect(policy).toContainText('UNVERIFIED');
  await policy.getByRole('checkbox').check();
  await policy.getByRole('button', { name: 'Înregistrează verificarea sursei' }).click();
  await expect(policy).toContainText('Stare: VERIFIED');

  await page.goto('/setari/utilizatori');
  await page.getByLabel('Nume utilizator', { exact: true }).fill('browser-viewer');
  await page.getByLabel('Nume afișat', { exact: true }).fill('Cititor sintetic E2E');
  await page
    .getByLabel('Parola inițială a utilizatorului', { exact: true })
    .fill(`${password}-viewer`);
  await page.getByLabel('Rol', { exact: true }).selectOption('VIEWER');
  await page.getByRole('button', { name: 'Creează utilizator', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Cititor sintetic E2E', exact: true }),
  ).toBeVisible();
  await page.goto('/setari/istoric');
  await page.getByRole('button', { name: 'Verifică integritatea', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Lanț verificat');
  await expect(page.locator('.audit-timeline')).toContainText('policy.verification_recorded');

  await page.getByRole('button', { name: 'Deconectare', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('browser-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Continuă cu parola', exact: true }).click();
  await page.getByLabel('Cod MFA', { exact: true }).fill(totp(secret, 30));
  // click() does not await the async handler. A hard navigation can discard the rotated cookie.
  const verified = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === '/api/v1/auth/mfa/verify' &&
      response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  const verifiedResponse = await verified;
  expect(verifiedResponse.status()).toBe(200);
  expect(await verifiedResponse.finished()).toBeNull();
  // Assert individual public fields only; never attach a session object or response headers.
  const verifiedSession = await verifiedResponse.json();
  expect(verifiedSession.state).toBe('FULL');
  expect(verifiedSession.user.role).toBe('OWNER');
  expect(verifiedSession.user.username).toBe('browser-owner');
  await expect(page.getByRole('button', { name: 'Deconectare', exact: true })).toBeVisible();
  const meResponse = await page.request.get('/api/v1/auth/me');
  expect(meResponse.status()).toBe(200);
  const currentSession = await meResponse.json();
  expect(currentSession.state).toBe('FULL');
  expect(currentSession.user.id).toBe(verifiedSession.user.id);
  await page.goto('/conturi');
  await expect(
    page.getByRole('heading', { name: 'Cont persistent E2E', exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.goto('/conturi');
  await expect(
    page.getByRole('heading', { name: 'Cont persistent E2E', exact: true }),
  ).toBeVisible();
  expect(await page.evaluate(() => document.cookie.includes('research_session'))).toBe(false);
  expect(
    await page.evaluate(() => Object.keys(localStorage).every((key) => key === 'research-theme')),
  ).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate']) {
    expect(
      (
        await page.request.post(endpoint, { data: { mode: 'SIMULATED', audit_probe: true } })
      ).status(),
    ).toBe(403);
  }
});
