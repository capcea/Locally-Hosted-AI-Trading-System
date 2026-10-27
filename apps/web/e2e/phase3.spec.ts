import { createHmac } from 'node:crypto';
import { test, expect } from '@playwright/test';
import { configureRisk, emergencyAction, navigateManagement } from './risk-workflow';

function totp(secret: string) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = [...secret].map((x) => alphabet.indexOf(x).toString(2).padStart(5, '0')).join('');
  const key = Buffer.from((bits.match(/.{8}/g) ?? []).map((x) => parseInt(x, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const hash = createHmac('sha1', key).update(counter).digest();
  return ((hash.readUInt32BE(hash.at(-1)! & 15) & 0x7fffffff) % 1000000)
    .toString()
    .padStart(6, '0');
}

test('synthetic orders persist, deduplicate, reconcile uncertainty and keep external execution denied', async ({
  page,
}, info) => {
  test.setTimeout(120000);
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  )
    throw new Error('Use the disposable broker browser harness.');
  await page.goto('/');
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Deschide meniul' }).click();
  await page.getByRole('button', { name: 'Cont & administrare', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('broker-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(process.env.E2E_OWNER_PASSWORD);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar sintetic broker');
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
  await page.getByLabel('Originea înregistrării').selectOption('SYNTHETIC_TEST_FIXTURE');
  await page.getByLabel('Denumire', { exact: true }).fill('Cont simulator E2E');
  await page.getByLabel('Monedă', { exact: true }).fill('USD');
  await page.getByLabel('Capital de referință', { exact: true }).fill('25000');
  await page.getByRole('button', { name: 'Salvează', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Cont simulator E2E', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Date de piață', exact: true }).last().click();
  const instrument = page.getByRole('form', { name: 'Înregistrare instrument', exact: true });
  await instrument.getByLabel('Simbol canonic', { exact: true }).fill('EURUSD');
  await instrument.getByLabel('Clasă de active', { exact: true }).selectOption('FOREX');
  await instrument.getByRole('button', { name: 'Salvează instrumentul' }).click();
  await expect(page.getByLabel('Instrument import', { exact: true })).toContainText('EURUSD');
  await page.getByRole('button', { name: 'Broker & simulator', exact: true }).last().click();
  const connection = page.getByRole('form', { name: 'Conexiune broker', exact: true });
  await connection.getByLabel('Denumire conexiune', { exact: true }).fill('Broker sintetic E2E');
  await connection
    .getByLabel('Cont local', { exact: true })
    .selectOption({ label: 'Cont simulator E2E' });
  await connection.getByRole('button', { name: 'Înregistrează conexiunea' }).click();
  await expect(
    page.getByRole('heading', { name: 'Broker sintetic E2E', exact: true }),
  ).toBeVisible();
  const scenario = page.getByRole('form', { name: 'Scenariu sintetic', exact: true });
  await scenario.getByLabel('Denumire scenariu', { exact: true }).fill('Scenariu sintetic E2E');
  await scenario
    .getByLabel('Conexiune simulator', { exact: true })
    .selectOption({ label: 'Broker sintetic E2E' });
  await scenario
    .getByLabel('Instrument scenariu', { exact: true })
    .selectOption({ label: 'EURUSD' });
  await scenario.getByLabel('Mod de poziții', { exact: true }).selectOption('HEDGING');
  await scenario.getByLabel('Confirm explicit ipotezele sintetice', { exact: false }).check();
  await scenario.getByRole('button', { name: 'Creează scenariul sintetic' }).click();
  const selected = page.getByRole('region', { name: 'Scenariu selectat', exact: true });
  await expect(
    selected.getByRole('heading', { name: 'Scenariu sintetic E2E · SIMULATED' }),
  ).toBeVisible();
  await configureRisk(page, 'Cont simulator E2E', 'Scenariu sintetic E2E');
  await navigateManagement(page, 'Broker & simulator');
  await page.getByRole('button', { name: 'Explorează Scenariu sintetic E2E', exact: true }).click();
  const quote = selected.getByRole('form', { name: 'Tick sintetic', exact: true });
  await quote.getByRole('button', { name: 'Aplică tick sintetic' }).click();
  const order = selected.getByRole('form', { name: 'Ordin sintetic', exact: true });
  await order.getByLabel('Cheie idempotentă ordin', { exact: true }).fill('synthetic-order-e2e');
  await order.getByLabel('Sens ordin', { exact: true }).selectOption('BUY');
  await order.getByLabel('Tip ordin simulat', { exact: true }).selectOption('MARKET');
  await order.getByLabel('Stop-loss sintetic obligatoriu', { exact: true }).fill('1.0990');
  await order.getByLabel('Take-profit sintetic obligatoriu', { exact: true }).fill('1.1030');
  await order.getByRole('button', { name: 'Trimite ordin în simulator' }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · ACKNOWLEDGED', exact: true }),
  ).toBeVisible();
  await quote.getByLabel('Moment tick UTC', { exact: true }).fill('2024-01-02T00:00:01Z');
  await quote.getByLabel('Secvență tick', { exact: true }).fill('1');
  await quote.getByRole('button', { name: 'Aplică tick sintetic' }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · FILLED', exact: true }),
  ).toBeVisible();
  const fills = selected.getByLabel('Fill-uri sintetice', { exact: true });
  expect(JSON.parse((await fills.textContent())!)).toHaveLength(1);
  expect(JSON.parse((await fills.textContent())!)[0].price).toMatch(/^1\.1002(?:0*)$/);
  const response = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/commands') && r.request().method() === 'POST',
  );
  await selected.getByRole('button', { name: 'Repetă aceeași comandă idempotentă' }).click();
  expect((await response).status()).toBe(200);
  await expect(
    selected.getByRole('button', { name: 'Repetă aceeași comandă idempotentă' }),
  ).toBeEnabled();
  expect(JSON.parse((await fills.textContent())!)).toHaveLength(1);
  const fault = selected.getByRole('form', { name: 'Fault sintetic', exact: true });
  await fault
    .getByLabel('Defecțiune sintetică următoare', { exact: true })
    .selectOption('AFTER_SUBMIT');
  await fault.getByRole('button', { name: 'Configurează defecțiunea sintetică' }).click();
  await order.getByLabel('Cheie idempotentă ordin', { exact: true }).fill('synthetic-unknown-e2e');
  await order.getByRole('button', { name: 'Trimite ordin în simulator' }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · UNKNOWN', exact: true }),
  ).toBeVisible();
  await selected.getByRole('button', { name: 'Reconciliază adevărul brokerului sintetic' }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · UNKNOWN', exact: true }),
  ).toHaveCount(0);
  const cleared = await emergencyAction(page, 'Cont simulator E2E', 'CLEAR_STOP');
  expect(cleared.completed).toBe(true);
  await navigateManagement(page, 'Broker & simulator');
  await page.getByRole('button', { name: 'Explorează Scenariu sintetic E2E', exact: true }).click();
  await quote.getByLabel('Moment tick UTC', { exact: true }).fill('2024-01-02T00:00:02Z');
  await quote.getByLabel('Secvență tick', { exact: true }).fill('2');
  await quote.getByRole('button', { name: 'Aplică tick sintetic' }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · FILLED', exact: true }),
  ).toHaveCount(2);
  expect(JSON.parse((await fills.textContent())!)).toHaveLength(2);
  await page.reload();
  if (info.project.name === 'mobile')
    await page.getByRole('button', { name: 'Deschide meniul' }).click();
  await page.getByRole('button', { name: 'Broker & simulator', exact: true }).click();
  await page.getByRole('button', { name: 'Explorează Scenariu sintetic E2E', exact: true }).click();
  await expect(page.getByLabel('Evenimente jurnal', { exact: true })).toContainText(
    'STATE_COMMITTED',
  );
  expect(
    JSON.parse((await page.getByLabel('Fill-uri sintetice', { exact: true }).textContent())!),
  ).toHaveLength(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate'])
    expect((await page.request.post(endpoint, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
});
