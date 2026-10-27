import { test, expect } from '@playwright/test';
import { realPost, seedRiskFixture } from './risk-fixture';
import { configureRisk, emergencyAction, navigateManagement } from './risk-workflow';

test('risk profiles, what-if, reservations and durable owner emergency controls use real APIs', async ({
  page,
}, info) => {
  test.setTimeout(180000);
  const { account, run, path } = await seedRiskFixture(page, info.project.name === 'mobile');
  await configureRisk(page, 'Cont risc E2E', 'Scenariu risc E2E');
  const center = page.getByRole('region', { name: 'Centru de risc', exact: true });
  await center
    .getByLabel('Scenariu pentru evaluarea riscului', { exact: true })
    .selectOption({ label: 'Scenariu risc E2E' });
  const calculator = center.getByRole('form', { name: 'Calculator risc ipotetic', exact: true });
  await calculator.getByLabel('Stop-loss pentru calculator', { exact: true }).fill('1.0990');
  await calculator.getByLabel('Take-profit pentru calculator', { exact: true }).fill('1.1030');
  await calculator.getByRole('button', { name: 'Calculează riscul ipotetic', exact: true }).click();
  const calculated = center.getByRole('region', { name: 'Rezultat calculator risc', exact: true });
  await expect(
    calculated.getByRole('heading', { name: 'ALLOW · SIMULATED', exact: true }),
  ).toBeVisible();
  expect(
    await (await page.request.get(`/api/v1/risk/accounts/${account.id}/reservations`)).json(),
  ).toHaveLength(0);
  await navigateManagement(page, 'Broker & simulator');
  await page.getByRole('button', { name: 'Explorează Scenariu risc E2E', exact: true }).click();
  const selected = page.getByRole('region', { name: 'Scenariu selectat', exact: true });
  const order = selected.getByRole('form', { name: 'Ordin sintetic', exact: true });
  await order.getByLabel('Cheie idempotentă ordin', { exact: true }).fill('approved-risk-e2e');
  await order.getByLabel('Sens ordin', { exact: true }).selectOption('BUY');
  await order.getByLabel('Tip ordin simulat', { exact: true }).selectOption('MARKET');
  await order.getByLabel('Stop-loss sintetic obligatoriu', { exact: true }).fill('1.0990');
  await order.getByLabel('Take-profit sintetic obligatoriu', { exact: true }).fill('1.1030');
  await order.getByRole('button', { name: 'Trimite ordin în simulator', exact: true }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · ACKNOWLEDGED', exact: true }),
  ).toBeVisible();
  const tick = selected.getByRole('form', { name: 'Tick sintetic', exact: true });
  await tick.getByLabel('Moment tick UTC', { exact: true }).fill('2024-01-02T00:00:01Z');
  await tick.getByLabel('Secvență tick', { exact: true }).fill('1');
  await tick.getByRole('button', { name: 'Aplică tick sintetic', exact: true }).click();
  await expect(
    selected.getByRole('heading', { name: 'BUY MARKET · FILLED', exact: true }),
  ).toBeVisible();
  const active = await (
    await page.request.get(`/api/v1/risk/accounts/${account.id}/reservations`)
  ).json();
  expect(active).toHaveLength(1);
  expect(active[0].state).toBe('OPEN');
  const stopped = await emergencyAction(page, 'Cont risc E2E', 'STOP_NEW_ENTRIES');
  expect(stopped.manual_stop).toBe(true);
  const denied = await realPost(
    page,
    path,
    {
      key: 'owner-stop-refuses-entry',
      action: 'SUBMIT',
      at: '2024-01-02T00:00:01Z',
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
  expect(denied.risk.reasons).toContain('STOP_NEW_ENTRIES');
  await page.reload();
  await page.goto('/conturi/siguranta');
  await center
    .getByLabel('Cont pentru controlul riscului', { exact: true })
    .selectOption({ label: 'Cont risc E2E' });
  await expect(center.getByRole('region', { name: 'Stare risc cont', exact: true })).toContainText(
    'INTRĂRI BLOCATE',
  );
  const flattened = await emergencyAction(page, 'Cont risc E2E', 'FLATTEN');
  expect(flattened.completed).toBe(true);
  expect(flattened.remaining_positions).toBe(0);
  expect(flattened.external_positions_closed).toBe(false);
  const final = await (await page.request.get(`/api/v1/execution/simulations/${run.id}`)).json();
  expect(
    Object.values(final.state.positions).every((p) =>
      (p as { volume: string }).volume.match(/^0(?:\.0+)?$/),
    ),
  ).toBe(true);
  const audit = await (await page.request.get('/api/v1/audit/verify')).json();
  expect(audit.valid).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
  for (const endpoint of ['/api/v1/orders', '/api/v1/live/activate'])
    expect((await page.request.post(endpoint, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
});
