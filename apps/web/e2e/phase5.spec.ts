import { test, expect } from '@playwright/test';
import { seedRiskFixture, realPost } from './risk-fixture';
import { configureRisk, navigateManagement } from './risk-workflow';

test('Strategy Lab persists real admitted-data experiments, risk-approved trades, replay and cancellation', async ({
  page,
}, info) => {
  test.setTimeout(240000);
  const { account, run } = await seedRiskFixture(page, info.project.name === 'mobile');
  await configureRisk(page, 'Cont risc E2E', 'Scenariu risc E2E',true);
  const provider = await realPost(page, '/market/providers', {
    name: 'Fixture cercetare browser',
    adapter: 'LOCAL',
    rights_reference: 'owner://synthetic-browser-fixture',
    attribution: 'SYNTHETIC_TEST_FIXTURE',
    usage_rights_acknowledged: true,
  });
  const start = Date.parse('2024-01-02T00:00:00Z');
  const at = (seconds: number) => new Date(start + seconds * 1000).toISOString();
  const price = (units: number) =>
    `${Math.floor(units / 10000)}.${String(units % 10000).padStart(4, '0')}`;
  const csv =
    [
      'event_time,observed_at,available_at,bid,ask,sequence',
      ...Array.from(
        { length: 101 },
        (_, i) => `${at(i)},${at(i)},${at(i)},${price(11000 + i)},${price(11002 + i)},${i}`,
      ),
    ].join('\n') + '\n';
  const me = await (await page.request.get('/api/v1/auth/me')).json();
  const imported = await page.request.post('/api/v1/market/imports', {
    headers: { Origin: new URL(page.url()).origin, 'X-CSRF-Token': me.csrf_token },
    multipart: {
      spec_json: JSON.stringify({
        provider_id: provider.id,
        account_id: account.id,
        instrument_id: run.instrument_id,
        source_symbol: run.state.spec.symbol,
        data_type: 'TICK',
        timeframe: 'TICK',
        start: at(0),
        end: at(101),
        format: 'CSV',
        provenance: 'SYNTHETIC_TEST_FIXTURE',
        calendar: run.state.spec.calendar,
        price_increment: '.0001',
      }),
      file: { name: 'synthetic-ticks.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) },
    },
  });
  expect(imported.status()).toBe(202);
  const upload = await imported.json();
  await expect
    .poll(
      async () =>
        (await (await page.request.get(`/api/v1/market/datasets/${upload.dataset_id}`)).json())
          .status,
      { timeout: 60000 },
    )
    .toBe('VALID');
  await navigateManagement(page, 'Laborator de strategii');
  const lab = page.getByRole('region', { name: 'Laborator de strategii', exact: true });
  await lab.getByLabel('Cont sursă verificat', { exact: true }).selectOption(account.id);
  await lab.getByLabel('Set de date principal', { exact: true }).selectOption(upload.dataset_id);
  const form = lab.getByRole('form', { name: 'Configurează backtest', exact: true });
  await form.getByLabel('Șablon simulator și risc', { exact: true }).selectOption(run.id);
  await form
    .getByLabel('Denumire experiment', { exact: true })
    .fill('Experiment cantitativ browser');
  for (const [label, text] of [
    ['Perioadă rapidă', '2'],
    ['Perioadă lentă', '3'],
    ['Fereastră indicator', '2'],
    ['Durată maximă (secunde)', '5'],
    ['Purge (secunde)', '5'],
    ['Embargo (secunde)', '1'],
    ['Limită observații', '200'],
    ['Sfârșit descoperire', at(30)],
    ['Sfârșit calibrare', at(50)],
    ['Sfârșit validare', at(75)],
  ])
    await form.getByLabel(label, { exact: true }).fill(text);
  await form.getByRole('checkbox', { name: /Autorizez copierea politicii/ }).check();
  await form.getByRole('checkbox', { name: /Accept costurile/ }).check();
  const createdPromise = page.waitForResponse(
    (response) =>
      response.url().endsWith('/api/v1/research/experiments') &&
      response.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Înregistrează experimentul', exact: true }).click();
  const createdResponse = await createdPromise;
  expect(createdResponse.status()).toBe(202);
  const created = await createdResponse.json();
  await expect(
    lab.getByRole('heading', { name: 'Experiment cantitativ browser · SUCCEEDED', exact: true }),
  ).toBeVisible({ timeout: 120000 });
  await lab.getByRole('button', { name: `Rezultate ${created.id}`, exact: true }).click();
  const results = lab.getByRole('region', { name: 'Rezultate experiment', exact: true });
  await expect(
    results.getByRole('img', { name: 'Curba capitalului simulat stocat' }),
  ).toBeVisible();
  const stored = await (
    await page.request.get(`/api/v1/research/experiments/${created.id}/results`)
  ).json();
  expect(stored.trials[0].risk_validated).toBe(true);
  expect(stored.trials[0].metrics.trade_count).toBeGreaterThan(0);
  await results.getByLabel('Replay și analiză', { exact: true }).selectOption('replay');
  await results.getByRole('button', { name: 'Încarcă analiza', exact: true }).click();
  await expect(results).toContainText('ALLOW');
  await results
    .getByRole('button', { name: 'Proveniență și număr total de încercări', exact: true })
    .click();
  const provenance = await (
    await page.request.get(`/api/v1/research/experiments/${created.id}/provenance`)
  ).json();
  await expect(results).toContainText(provenance.plan.datasets[0].manifest_sha256);
  await form.getByLabel('Denumire experiment', { exact: true }).fill('Experiment anulat browser');
  await form
    .getByText('Date pentru confirmare multi-timeframe și sweep-uri', { exact: true })
    .click();
  const parameters = provenance.plan.parameters[0];
  await form
    .getByLabel('Parametri pentru sweep (JSON, cel mult 16)', { exact: true })
    .fill(JSON.stringify(Array.from({ length: 16 }, () => parameters)));
  const cancelledPromise = page.waitForResponse(
    (response) =>
      response.url().endsWith('/api/v1/research/experiments') &&
      response.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Înregistrează experimentul', exact: true }).click();
  const queuedResponse = await cancelledPromise;
  expect(queuedResponse.status()).toBe(202);
  const queued = await queuedResponse.json();
  await lab.getByRole('button', { name: `Anulează ${queued.id}`, exact: true }).click();
  await expect(
    lab.getByRole('heading', { name: 'Experiment anulat browser · CANCELLED', exact: true }),
  ).toBeVisible({ timeout: 60000 });
  expect(
    (await page.request.get(`/api/v1/research/experiments/${queued.id}/results`)).status(),
  ).toBe(409);
  expect((await (await page.request.get('/api/v1/audit/verify')).json()).valid).toBe(true);
  for (const path of ['/api/v1/orders', '/api/v1/live/activate'])
    expect((await page.request.post(path, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
    false,
  );
});
