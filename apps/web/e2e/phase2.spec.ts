import { createHmac } from 'node:crypto';
import { test, expect } from '@playwright/test';
function totp(secret: string) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = [...secret].map((x) => alphabet.indexOf(x).toString(2).padStart(5, '0')).join('');
  const key = Buffer.from((bits.match(/.{8}/g) ?? []).map((x) => parseInt(x, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const hash = createHmac('sha1', key).update(counter).digest();
  const offset = hash.at(-1)! & 15;
  return ((hash.readUInt32BE(offset) & 0x7fffffff) % 1000000).toString().padStart(6, '0');
}
test('market data imports persist, pass quality and display only available stored prices', async ({
  page,
}, info) => {
  test.setTimeout(120000);
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  )
    throw new Error('Use the disposable browser harness.');
  await page.goto('/');
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Deschide meniul' }).click();
  await page.getByRole('button', { name: 'Cont & administrare', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('market-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(process.env.E2E_OWNER_PASSWORD);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar test date');
  await page
    .getByLabel('Codul privat de configurare', { exact: true })
    .fill(process.env.E2E_SETUP_TOKEN);
  await page.getByRole('button', { name: 'Creează proprietarul', exact: true }).click();
  await page.getByRole('button', { name: 'Configurează autentificatorul' }).click();
  const secret = (await page.locator('.enrollment-secret code').textContent())!.trim();
  await page.getByLabel('Cod MFA', { exact: true }).fill(totp(secret));
  await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
  await expect(page.locator('.recovery-codes code')).toHaveCount(10);
  await page.getByRole('button', { name: 'Am salvat codurile' }).click();
  await page.getByLabel('Denumire', { exact: true }).fill('Cont sintetic pentru date');
  await page.getByLabel('Monedă', { exact: true }).fill('USD');
  await page.getByLabel('Capital de referință', { exact: true }).fill('25000');
  await page.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Cont sintetic pentru date' })).toBeVisible();
  await page.getByRole('button', { name: 'Date de piață', exact: true }).last().click();
  const instrument = page.getByRole('form', { name: 'Înregistrare instrument' });
  await instrument.getByLabel('Simbol canonic', { exact: true }).fill('EURUSD');
  await instrument.getByLabel('Clasă de active', { exact: true }).selectOption('FOREX');
  await instrument.getByRole('button', { name: 'Salvează instrumentul' }).click();
  const provider = page.getByRole('form', { name: 'Înregistrare furnizor' });
  await provider.getByLabel('Denumire furnizor', { exact: true }).fill('Fișiere sintetice E2E');
  await provider.getByLabel('Adaptor de date', { exact: true }).selectOption('LOCAL');
  await provider
    .getByLabel('Referință licență / drepturi de utilizare', { exact: true })
    .fill('Synthetic test fixtures authored for acceptance');
  await provider.getByLabel('Atribuire sursă', { exact: true }).fill('SYNTHETIC_TEST_FIXTURE');
  await provider.getByRole('checkbox').check();
  await provider.getByRole('button', { name: 'Înregistrează furnizorul' }).click();
  await expect(page.getByRole('heading', { name: 'Fișiere sintetice E2E' })).toBeVisible();
  const form = page.getByRole('form', { name: 'Import istoric' });
  await form
    .getByLabel('Furnizor import', { exact: true })
    .selectOption({ label: 'Fișiere sintetice E2E' });
  await form
    .getByLabel('Cont pentru date', { exact: true })
    .selectOption({ label: 'Cont sintetic pentru date' });
  await form.getByLabel('Instrument import', { exact: true }).selectOption({ label: 'EURUSD' });
  await form.getByLabel('Simbol exact la sursă', { exact: true }).fill('EURUSD.test');
  await form.getByLabel('Tip de date', { exact: true }).selectOption('BAR');
  await form.getByLabel('Interval de timp', { exact: true }).selectOption('M1');
  await form.getByLabel('Format fișier', { exact: true }).selectOption('CSV');
  await form.getByLabel('Originea datelor', { exact: true }).selectOption('SYNTHETIC_TEST_FIXTURE');
  await form.getByRole('checkbox').check();
  await form
    .getByLabel('Sursa calendarului declarat', { exact: true })
    .fill('Synthetic weekday test calendar');
  const lines = ['event_time,observed_at,available_at,open,high,low,close,sequence'];
  for (let i = 0; i < 5; i++)
    lines.push(
      `2024-01-02T00:0${i}:00Z,2024-01-02T00:0${i + 1}:00Z,2024-01-02T00:0${i + 1}:00Z,1.1,1.2,1.0,1.15,${i}`,
    );
  await form.getByLabel('Fișier istoric', { exact: true }).setInputFiles({
    name: 'synthetic.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(lines.join('\n')),
  });
  await form.getByRole('button', { name: 'Pornește importul' }).click();
  await expect(page.getByRole('button', { name: 'Explorează EURUSD v1' })).toBeVisible();
  await expect(
    page
      .locator('.management-record')
      .filter({ has: page.getByRole('heading', { name: 'EURUSD · v1', exact: true }) }),
  ).toContainText('SYNTHETIC_TEST_FIXTURE · VALID · BAR/M1', { timeout: 30000 });
  await page.getByRole('button', { name: 'Explorează EURUSD v1' }).click();
  await page.getByRole('button', { name: 'Încarcă eșantionul' }).click();
  await expect(page.getByRole('img', { name: 'Prețuri din setul de date importat' })).toBeVisible();
  await expect(page.getByText('SYNTHETIC_TEST_FIXTURE', { exact: false }).first()).toBeVisible();
  const explorer = page.getByRole('region', { name: 'Explorator set de date', exact: true });
  const manifestResponse = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname.endsWith('/provenance') &&
      response.request().method() === 'GET',
  );
  await explorer.getByRole('button', { name: 'Verifică manifestul și proveniența' }).click();
  const response = await manifestResponse;
  expect(response.status()).toBe(200);
  const manifest = await response.json();
  expect(manifest.schema_version).toBe(1);
  const result = explorer.getByRole('region', {
    name: 'Detalii de proveniență',
    exact: true,
  });
  await expect(result).toBeVisible();
  await expect(result.locator('pre')).toHaveText(JSON.stringify(manifest, null, 2));
  await page
    .getByLabel('Informații disponibile la UTC', { exact: true })
    .fill('2024-01-02T00:00:00Z');
  const earlierSampleResponse = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname.endsWith('/sample') && response.request().method() === 'GET',
  );
  await explorer.getByRole('button', { name: 'Încarcă eșantionul' }).click();
  const earlierSample = await earlierSampleResponse;
  expect(earlierSample.status()).toBe(200);
  expect((await earlierSample.json()).items).toEqual([]);
  await expect(explorer.getByText('0 observații; limită 500', { exact: false })).toBeVisible();
  await expect(page.getByRole('img', { name: 'Prețuri din setul de date importat' })).toHaveCount(
    0,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
});
