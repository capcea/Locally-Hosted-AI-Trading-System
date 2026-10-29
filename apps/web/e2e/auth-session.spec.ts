import { execFileSync } from 'node:child_process';
import { createHmac } from 'node:crypto';
import { expect, test } from '@playwright/test';
import type { Locator } from '@playwright/test';

function codeAt(secret: string, at: number) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = [...secret].map((x) => alphabet.indexOf(x).toString(2).padStart(5, '0')).join('');
  const key = Buffer.from((bits.match(/.{8}/g) ?? []).map((x) => parseInt(x, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(at / 30000)));
  const hash = createHmac('sha1', key).update(counter).digest();
  return ((hash.readUInt32BE(hash.at(-1)! & 15) & 0x7fffffff) % 1000000)
    .toString()
    .padStart(6, '0');
}
async function secretFill(locator: Locator, value: string) {
  try {
    await locator.fill(value);
  } catch {
    throw new Error('Sensitive authentication field could not be filled; value omitted.');
  }
}
function age(action: 'stale-mfa' | 'expire', session: string) {
  execFileSync('.venv/bin/python', ['-m', 'testing.mfa_state', action, session], {
    cwd: '../..',
    env: process.env,
    stdio: 'pipe',
  });
}

test('recent MFA, rotation, CSRF renewal and expired-session recovery keep the original route', async ({
  page,
}) => {
  test.setTimeout(180000);
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_OWNER_PASSWORD ||
    !process.env.E2E_AUTH_DATABASE
  )
    throw new Error('Use the disposable auth browser scenario; ambient accounts are prohibited.');
  const password = process.env.E2E_OWNER_PASSWORD;
  await page.goto('/setari/ai#ai-models');
  await page.getByLabel('Nume utilizator', { exact: true }).fill('auth-browser-owner');
  await secretFill(page.getByLabel('Parolă', { exact: true }), password);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar sintetic MFA');
  await secretFill(
    page.getByLabel('Codul privat de configurare', { exact: true }),
    process.env.E2E_SETUP_TOKEN!,
  );
  await page.getByRole('button', { name: 'Creează proprietarul', exact: true }).click();
  await page.getByRole('button', { name: 'Configurează autentificatorul', exact: true }).click();
  const secret = (await page.locator('.enrollment-secret code').textContent())!.trim();
  const replay = codeAt(secret, Date.now());
  await secretFill(page.getByLabel('Cod MFA', { exact: true }), replay);
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  await page.getByRole('button', { name: 'Am salvat codurile', exact: true }).click();
  const before = await (await page.request.get('/api/v1/auth/me')).json();
  age('stale-mfa', before.session_id);
  const region = page.getByRole('region', { name: 'Destinație OpenRouter', exact: true });
  await region.getByText('Înregistrează destinația OpenRouter', { exact: true }).click();
  const form = region.getByRole('form', { name: 'Autorizare OpenRouter', exact: true });
  await form
    .getByLabel('Identificatorul exact al furnizorului din amonte')
    .fill('synthetic-fixture');
  for (const label of [
    'Aprob explicit procesarea în cloud public OpenRouter.',
    'Aprob furnizorul din amonte ales și am verificat drepturile asupra datelor.',
    'Am revizuit tarifele, limitele și eventualele costuri.',
    'Înțeleg limitele garanțiilor ZDR și de confidențialitate declarate.',
  ])
    await form.getByLabel(label, { exact: true }).check();
  let submissions = 0;
  page.on('request', (request) => {
    if (
      request.method() === 'POST' &&
      new URL(request.url()).pathname === '/api/v1/ai/endpoints/openrouter'
    )
      submissions++;
  });
  const refused = page.waitForResponse(
    (r) => r.url().endsWith('/ai/endpoints/openrouter') && r.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Înregistrează autorizarea cloud', exact: true }).click();
  expect((await refused).status()).toBe(403);
  const dialog = page.getByRole('dialog', {
    name: 'Reconfirmă autentificarea în doi pași',
    exact: true,
  });
  await expect(dialog).toBeVisible();
  await secretFill(dialog.getByLabel('Parola curentă', { exact: true }), password);
  await secretFill(dialog.getByLabel('Cod MFA nou', { exact: true }), replay);
  const invalid = page.waitForResponse((r) => r.url().endsWith('/auth/reauthenticate'));
  await dialog.getByRole('button', { name: 'Reconfirmă autentificarea', exact: true }).click();
  expect((await invalid).status()).toBe(401);
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('alert')).toContainText('Parola sau codul MFA');
  await expect(page).toHaveURL(/\/setari\/ai#ai-models$/);
  const usedAt = Date.now() + 30000;
  await secretFill(dialog.getByLabel('Parola curentă', { exact: true }), password);
  await secretFill(dialog.getByLabel('Cod MFA nou', { exact: true }), codeAt(secret, usedAt));
  const authorized = page.waitForResponse((r) => r.url().endsWith('/auth/reauthenticate'));
  await dialog.getByRole('button', { name: 'Reconfirmă autentificarea', exact: true }).click();
  expect((await authorized).status()).toBe(200);
  await expect(dialog).toHaveCount(0);
  expect(submissions).toBe(1); // Authorization does not automatically replay the sensitive action.
  await expect(form.getByLabel('Identificatorul exact al furnizorului din amonte')).toHaveValue(
    'synthetic-fixture',
  );
  const after = await (await page.request.get('/api/v1/auth/me')).json();
  expect(
    Boolean(after.session_id !== before.session_id && after.csrf_token !== before.csrf_token),
  ).toBe(true);
  const saved = page.waitForResponse(
    (r) => r.url().endsWith('/ai/endpoints/openrouter') && r.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Înregistrează autorizarea cloud', exact: true }).click();
  expect((await saved).status()).toBe(201);
  await page.goto('/setari/securitate');
  await page.goBack();
  await expect(page).toHaveURL(/\/setari\/ai#ai-models$/);
  await page.reload();
  await expect(page.getByRole('region', { name: 'Registru AI', exact: true })).toBeVisible();
  age('expire', after.session_id);
  await page.reload();
  await expect(
    page.getByText('Sesiunea a expirat sau a fost revocată. Autentifică-te din nou.', {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('auth-browser-owner');
  await secretFill(page.getByLabel('Parolă', { exact: true }), password);
  await page.getByRole('button', { name: 'Continuă cu parola', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Verifică MFA', exact: true })).toBeVisible();
  // Wait for an actually unused TOTP window; do not reset counters or replay accepted codes.
  await expect
    .poll(() => Math.floor(Date.now() / 30000), { timeout: 35000 })
    .toBeGreaterThanOrEqual(Math.floor(usedAt / 30000));
  await secretFill(page.getByLabel('Cod MFA', { exact: true }), codeAt(secret, Date.now() + 30000));
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Registru AI', exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/setari\/ai#ai-models$/);
});
