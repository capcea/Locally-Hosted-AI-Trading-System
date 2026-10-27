import { createHmac } from 'node:crypto';
import { expect } from '@playwright/test';
import type { Page } from '@playwright/test';

export function totp(secret: string) {
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
export async function realPost(page: Page, path: string, data: unknown, status = 201) {
  const me = await page.request.get('/api/v1/auth/me');
  expect(me.status()).toBe(200);
  const csrf = (await me.json()).csrf_token;
  const response = await page.request.post(`/api/v1${path}`, {
    data,
    headers: {
      Origin: new URL(page.url()).origin,
      'X-CSRF-Token': csrf,
    },
  });
  expect(response.status()).toBe(status);
  return response.json();
}

export async function seedRiskFixture(page: Page, mobile: boolean) {
  if (
    process.env.E2E_PHASE1_ISOLATED !== '1' ||
    !process.env.E2E_SETUP_TOKEN ||
    !process.env.E2E_OWNER_PASSWORD
  )
    throw new Error('Use the disposable risk browser harness.');
  await page.goto('/');
  const primary = page.getByRole('navigation', { name: 'Navigare principală', exact: true });
  await expect(primary.getByRole('link')).toHaveCount(5);
  if (mobile) await expect(primary.getByRole('link', { name: 'Acasă', exact: true })).toBeVisible();
  await primary.getByRole('link', { name: 'Conturi și siguranță', exact: true }).click();
  await page.getByLabel('Nume utilizator', { exact: true }).fill('risk-owner');
  await page.getByLabel('Parolă', { exact: true }).fill(process.env.E2E_OWNER_PASSWORD);
  await page.getByLabel('Nume afișat', { exact: true }).fill('Proprietar risc sintetic');
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
  // Metadata uses actual authenticated services; risk admission below is performed in the UI.
  const account = await realPost(page, '/records/accounts', {
    kind: 'accounts',
    name: 'Cont risc E2E',
    currency: 'USD',
    initial_capital: '25000',
    source: 'SYNTHETIC_TEST_FIXTURE',
  });
  const venue = await realPost(page, '/records/venues', {
    kind: 'venues',
    name: 'Piață sintetică risc',
    venue_type: 'CUSTOM',
  });
  const instrument = await realPost(page, '/records/instruments', {
    kind: 'instruments',
    name: 'EURUSD',
    symbol: 'EURUSD',
    asset_class: 'FOREX',
    venue_id: venue.id,
  });
  const broker = await realPost(page, '/records/brokers', {
    kind: 'brokers',
    name: 'Simulator risc',
    account_id: account.id,
    adapter: 'CUSTOM',
    source: 'SYNTHETIC_TEST_FIXTURE',
  });
  await realPost(page, '/execution/connections', {
    broker_connection_id: broker.id,
    provider: 'SIMULATOR',
    mode: 'SIMULATED',
  });
  const run = await realPost(page, '/execution/simulations', {
    connection_id: broker.id,
    instrument_id: instrument.id,
    name: 'Scenariu risc E2E',
    start_at: '2024-01-02T00:00:00Z',
    spec: {
      symbol: 'EURUSD.test',
      canonical_symbol: 'EURUSD',
      asset_class: 'FOREX',
      tick_size: '.0001',
      digits: 4,
      contract_size: '100000',
      min_volume: '.01',
      max_volume: '100',
      volume_step: '.01',
      stop_distance: '0',
      freeze_distance: '0',
      profit_currency: 'USD',
      order_types: ['MARKET', 'LIMIT', 'STOP'],
      account_mode: 'HEDGING',
      oco_supported: false,
      source: 'Explicit synthetic test specification',
      observed_at: '2024-01-02T00:00:00Z',
      valid_until: '2024-01-12T00:00:00Z',
      calendar: {
        timezone: 'UTC',
        weekdays: [0, 1, 2, 3, 4],
        holidays: [],
        opens: 0,
        closes: 1440,
        verified_until: '2024-01-12T00:00:00Z',
        source: 'Explicit synthetic test calendar',
      },
    },
    assumptions: {
      assumption_source: 'Explicit synthetic assumptions, not real broker data',
      commission_per_unit: '0',
      liquidity_per_tick: '1',
      synthetic_initial_balance: '25000',
      account_currency: 'USD',
    },
  });
  const path = `/execution/simulations/${run.id}/commands`;
  await realPost(
    page,
    path,
    {
      key: 'initial-risk-tick',
      action: 'TICK',
      at: '2024-01-02T00:00:00Z',
      quote: {
        symbol: 'EURUSD.test',
        event_time: '2024-01-02T00:00:00Z',
        available_at: '2024-01-02T00:00:00Z',
        sequence: 0,
        bid: '1.1000',
        ask: '1.1002',
      },
    },
    200,
  );
  const refused = await realPost(
    page,
    path,
    {
      key: 'unconfigured-risk-denied',
      action: 'SUBMIT',
      at: '2024-01-02T00:00:00Z',
      order: {
        side: 'BUY',
        order_type: 'MARKET',
        volume: '.1',
        stop_loss: '1.0990',
        take_profit: '1.1030',
      },
    },
    409,
  );
  expect(refused.risk.decision).not.toBe('ALLOW');
  expect(Object.keys(refused.state.orders)).toHaveLength(0);

  return { account, run, path };
}
