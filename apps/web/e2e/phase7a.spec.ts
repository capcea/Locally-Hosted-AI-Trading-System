import { test, expect } from '@playwright/test';
import { seedRiskFixture, realPost } from './risk-fixture';
import { configureRisk } from './risk-workflow';

test('bounded synthetic campaign requires owner review and retains canonical experiment lineage', async ({
  page,
}, info) => {
  test.setTimeout(240000);
  const { account, run } = await seedRiskFixture(page, info.project.name === 'mobile');
  await configureRisk(page, 'Cont risc E2E', 'Scenariu risc E2E', true);
  const provider = await realPost(page, '/market/providers', {
    name: 'SYNTHETIC_FIXTURE campaign data',
    adapter: 'LOCAL',
    rights_reference: 'owner://synthetic-campaign-test',
    attribution: 'SYNTHETIC_TEST_FIXTURE',
    usage_rights_acknowledged: true,
  });
  const at = (n: number) => new Date(Date.parse('2024-01-02T00:00:00Z') + n * 1000).toISOString();
  const price = (n: number) => `${Math.floor(n / 10000)}.${String(n % 10000).padStart(4, '0')}`;
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
      file: {
        name: 'synthetic-campaign-ticks.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csv),
      },
    },
  });
  expect(imported.status()).toBe(202);
  const dataset = (await imported.json()).dataset_id;
  await expect
    .poll(
      async () =>
        (await (await page.request.get(`/api/v1/market/datasets/${dataset}`)).json()).status,
      { timeout: 60000 },
    )
    .toBe('VALID');
  const data = await (await page.request.get(`/api/v1/market/datasets/${dataset}`)).json();
  const context = (await (await page.request.get(`/api/v1/risk/runs/${run.id}/contexts`)).json())[0]
    .context;
  context.financial.automated = true;
  context.financial.execution_style = 'INTRADAY_BENCHMARK';
  const registry = await (await page.request.get('/api/v1/research/strategies')).json();
  const original = await realPost(
    page,
    '/research/experiments',
    {
      key: 'campaign-template-' + crypto.randomUUID().replaceAll('-', ''),
      name: 'Configurație sintetică pentru campanie',
      source_account_id: account.id,
      strategy: 'EMA_TREND',
      strategy_digest: registry.find((s: { id: string }) => s.id === 'EMA_TREND').digest,
      datasets: [
        {
          dataset_id: dataset,
          manifest_sha256: data.manifest_sha256,
          symbol: run.state.spec,
          context,
        },
      ],
      parameters: [
        { fast: 2, slow: 3, lookback: 2, stop_ticks: 20, max_hold_seconds: 5, volume: '.01' },
      ],
      chronology: {
        start: at(0),
        discovery_end: at(30),
        calibration_end: at(50),
        validation_end: at(75),
        end: at(101),
        purge_seconds: 5,
        embargo_seconds: 1,
      },
      phase: 'DISCOVERY',
      engine: 'EVENT',
      assumptions: run.state.model,
      seed: 7,
      max_rows: 200,
      max_seconds: 120,
      bootstrap_samples: 100,
      acknowledged_clone_policy_to_isolated_accounts: true,
      acknowledged_research_only: true,
      acknowledged_cost_and_bar_assumptions: true,
    },
    202,
  );
  await expect
    .poll(
      async () =>
        (await (await page.request.get(`/api/v1/research/experiments/${original.id}`)).json()).job
          .state,
      { timeout: 120000 },
    )
    .toBe('SUCCEEDED');
  await page.goto('/testeaza/campanii');
  const form = page.getByRole('form', { name: 'Campanie nouă', exact: true });
  await form.getByLabel('Scopul cercetării', { exact: true }).fill('Campanie sintetică browser');
  await form
    .getByLabel('Ce vrei să verifici?', { exact: true })
    .fill('Verifică infrastructura cu strategia revizuită și date sintetice.');
  await form
    .getByLabel('Configurație dintr-un test existent', { exact: true })
    .selectOption(original.id);
  await form.getByRole('checkbox', { name: /Accept doar cercetare limitată/ }).check();
  const created = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/v1/campaigns' && r.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Creează ciorna campaniei', exact: true }).click();
  const response = await created;
  expect(response.status()).toBe(201);
  const campaign = await response.json();
  await expect(page).toHaveURL(new RegExp(`/testeaza/campanii/${campaign.id}$`));
  const progress = page.getByRole('region', { name: 'Progresul campaniei', exact: true });
  await progress.getByRole('button', { name: 'Revizuiește autorizarea', exact: true }).click();
  await progress.getByRole('checkbox', { name: /Autorizez exact aceste limite/ }).check();
  await progress
    .getByRole('button', { name: 'Autorizează campania limitată', exact: true })
    .click();
  const send = progress.getByRole('button', { name: 'Trimite testul revizuit', exact: true });
  await expect(send).toBeVisible({ timeout: 30000 });
  await expect(send).toBeDisabled();
  await progress.getByRole('checkbox', { name: /Am revizuit exact planul/ }).check();
  const submitted = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/submit-plan') && r.request().method() === 'POST',
  );
  await send.click();
  expect((await submitted).status()).toBe(202);
  await expect(progress).toContainText('Cercetare oprită', { timeout: 120000 });
  await expect(progress).toContainText('SYNTHETIC_FIXTURE');
  await expect(
    page.getByRole('region', { name: 'Istoricul cercetării', exact: true }),
  ).toContainText('Dovezi insuficiente');
  const entries = await (await page.request.get(`/api/v1/campaigns/${campaign.id}/lineage`)).json();
  expect(entries.some((e: { kind: string }) => e.kind === 'EVIDENCE')).toBe(true);
  expect(
    entries.every(
      (e: { source: string; paper_eligible: boolean }) =>
        e.source === 'SYNTHETIC_FIXTURE' && !e.paper_eligible,
    ),
  ).toBe(true);
  await page.reload();
  await expect(progress).toContainText('Cercetare oprită');
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  expect(
    (await page.request.post('/api/v1/orders', { data: { mode: 'SIMULATED' } })).status(),
  ).toBe(403);
});
