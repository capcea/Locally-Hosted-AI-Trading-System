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
async function marketStep(title: string, body: () => Promise<void>) {
  // Fixed stage names only: no passwords, MFA/session payloads or source files in output.
  console.info(`[phase2] ${title}`);
  await test.step(title, body);
}
test('market data imports persist, pass quality and display only available stored prices', async ({
  page,
}) => {
  test.setTimeout(120000);
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  )
    throw new Error('Use the disposable browser harness.');
  const ownerPassword = process.env.E2E_OWNER_PASSWORD;
  const setupToken = process.env.E2E_SETUP_TOKEN;
  const form = page.getByRole('form', { name: 'Import istoric' });
  const explorer = page.getByRole('region', { name: 'Explorator set de date', exact: true });
  await marketStep('Owner MFA and persistent simulation account', async () => {
    await page.goto('/');
    await page.goto('/conturi');
    await page.getByLabel('Nume utilizator', { exact: true }).fill('market-owner');
    await page.getByLabel('Parolă', { exact: true }).fill(ownerPassword);
    await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar test date');
    await page.getByLabel('Codul privat de configurare', { exact: true }).fill(setupToken);
    await page.getByRole('button', { name: 'Creează proprietarul', exact: true }).click();
    await page.getByRole('button', { name: 'Configurează autentificatorul' }).click();
    const secret = (await page.locator('.enrollment-secret code').textContent())!.trim();
    await page.getByLabel('Cod MFA', { exact: true }).fill(totp(secret));
    await page.getByRole('button', { name: 'Verifică MFA', exact: true }).click();
    await expect(page.locator('.recovery-codes code')).toHaveCount(10);
    await page.getByRole('button', { name: 'Am salvat codurile' }).click();
    await page.getByLabel('Denumire', { exact: true }).fill('Cont sintetic pentru date');
    await page.getByLabel('Monedă', { exact: true }).fill('USD');
    await page.getByLabel('Capital declarat pentru simulare', { exact: true }).fill('25000');
    await page.getByRole('button', { name: 'Salvează', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Cont sintetic pentru date' })).toBeVisible();
  });
  await marketStep('Persist instrument before leaving its editor', async () => {
    await page.goto('/setari/catalog');
    const instrument = page.getByRole('form', { name: 'Înregistrare instrument' });
    await instrument.getByLabel('Simbol canonic', { exact: true }).fill('EURUSD');
    await instrument.getByLabel('Clasă de active', { exact: true }).selectOption('FOREX');
    const instrumentSaved = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === '/api/v1/records/instruments' &&
        response.request().method() === 'POST',
    );
    await instrument.getByRole('button', { name: 'Salvează instrumentul' }).click();
    const savedInstrument = await instrumentSaved;
    expect(savedInstrument.status()).toBe(201);
    expect(await savedInstrument.finished()).toBeNull();
    await expect(page.getByRole('heading', { name: 'EURUSD', exact: true })).toBeVisible();
  });
  await marketStep('Register the permitted local source', async () => {
    await page.goto('/setari/surse');
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
  });
  await marketStep('Choose source, account and imported instrument', async () => {
    await page.goto('/testeaza/date/import');
    await form
      .getByLabel('Furnizor import', { exact: true })
      .selectOption({ label: 'Fișiere sintetice E2E' });
    await form.getByRole('button', { name: 'Continuă', exact: true }).click();
    await form
      .getByLabel('Cont pentru date', { exact: true })
      .selectOption({ label: 'Cont sintetic pentru date' });
    await form.getByLabel('Instrument import', { exact: true }).selectOption({ label: 'EURUSD' });
    await form.getByLabel('Simbol exact la sursă', { exact: true }).fill('EURUSD.test');
    await form.getByLabel('Tip de date', { exact: true }).selectOption('BAR');
    await form.getByLabel('Interval de timp', { exact: true }).selectOption('M1');
    await form.getByRole('button', { name: 'Continuă', exact: true }).click();
  });
  await marketStep('Attach historical file and explicit UTC times', async () => {
    await form.getByLabel('Început import UTC', { exact: true }).fill('2024-01-02T00:00:00Z');
    await form.getByLabel('Sfârșit import UTC', { exact: true }).fill('2024-01-02T00:05:00Z');
    await form.getByLabel('Format fișier', { exact: true }).selectOption('CSV');
    await form
      .getByLabel('Originea datelor', { exact: true })
      .selectOption('SYNTHETIC_TEST_FIXTURE');
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
    await form.getByRole('button', { name: 'Continuă', exact: true }).click();
  });
  await marketStep('Review calendar and source rights', async () => {
    await form.getByRole('checkbox', { name: /Declar explicit calendarul/ }).check();
    await form
      .getByLabel('Sursa calendarului declarat', { exact: true })
      .fill('Synthetic weekday test calendar');
    await form.getByRole('checkbox', { name: /Am verificat drepturile sursei/ }).check();
    await form.getByRole('button', { name: 'Continuă', exact: true }).click();
  });
  await marketStep('Accept import, observe redirect and finish real worker job', async () => {
    const importAccepted = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === '/api/v1/market/imports' &&
        response.request().method() === 'POST',
    );
    await form.getByRole('button', { name: 'Pornește importul' }).click();
    const accepted = await importAccepted;
    expect(accepted.status()).toBe(202);
    expect(await accepted.finished()).toBeNull();
    const job = await accepted.json();
    expect(job.id).toMatch(/^[0-9a-f-]{36}$/);
    expect(job.dataset_id).toMatch(/^[0-9a-f-]{36}$/);
    // The submit handler redirects only after parsing the response. Do not race it back to catalog.
    await expect(page).toHaveURL(new RegExp(`/testeaza/date/importuri/${job.id}$`));
    await expect
      .poll(
        async () => {
          const response = await page.request.get(`/api/v1/market/jobs/${job.id}`);
          expect(response.status()).toBe(200);
          return (await response.json()).state;
        },
        { message: 'The real market worker must complete the accepted import', timeout: 30000 },
      )
      .toBe('SUCCEEDED');
    await page.getByRole('link', { name: 'Seturi de date', exact: true }).click();
  });
  await marketStep('Read admitted stored prices and their quality', async () => {
    await expect(page.getByRole('button', { name: 'Explorează EURUSD v1' })).toBeVisible();
    await expect(
      page
        .locator('.management-record')
        .filter({ has: page.getByRole('heading', { name: 'EURUSD · v1', exact: true }) }),
    ).toContainText('SYNTHETIC_TEST_FIXTURE · VALID · BAR/M1', { timeout: 30000 });
    await page.getByRole('button', { name: 'Explorează EURUSD v1' }).click();
    await page.getByRole('button', { name: 'Încarcă eșantionul' }).click();
    await expect(
      page.getByRole('img', { name: 'Prețuri din setul de date importat' }),
    ).toBeVisible();
    await expect(page.getByText('SYNTHETIC_TEST_FIXTURE', { exact: false }).first()).toBeVisible();
  });
  await marketStep('Verify the exact persisted provenance manifest', async () => {
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
  });
  await marketStep('Refuse observations unavailable at the decision time', async () => {
    await page
      .getByLabel('Informații disponibile la UTC', { exact: true })
      .fill('2024-01-02T00:00:00Z');
    const earlierSampleResponse = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname.endsWith('/sample') &&
        response.request().method() === 'GET',
    );
    await explorer.getByRole('button', { name: 'Încarcă eșantionul' }).click();
    const earlierSample = await earlierSampleResponse;
    expect(earlierSample.status()).toBe(200);
    expect((await earlierSample.json()).items).toEqual([]);
    await expect(explorer.getByText('0 observații; limită 500', { exact: false })).toBeVisible();
    await expect(page.getByRole('img', { name: 'Prețuri din setul de date importat' })).toHaveCount(
      0,
    );
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth),
    ).toBe(false);
  });
});
