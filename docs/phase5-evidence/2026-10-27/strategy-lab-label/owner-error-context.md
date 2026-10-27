# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase5.spec.ts >> Strategy Lab persists real admitted-data experiments, risk-approved trades, replay and cancellation
- Location: e2e/phase5.spec.ts:5:1

# Error details

```
Test timeout of 240000ms exceeded.
```

```
Error: locator.selectOption: Test timeout of 240000ms exceeded.
Call log:
  - waiting for getByRole('region', { name: 'Laborator de strategii', exact: true }).getByLabel('Cont sursă verificat', { exact: true })

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import { seedRiskFixture, realPost } from './risk-fixture';
  3   | import { configureRisk, navigateManagement } from './risk-workflow';
  4   | 
  5   | test('Strategy Lab persists real admitted-data experiments, risk-approved trades, replay and cancellation', async ({
  6   |   page,
  7   | }, info) => {
  8   |   test.setTimeout(240000);
  9   |   const { account, run } = await seedRiskFixture(page, info.project.name === 'mobile');
  10  |   await configureRisk(page, 'Cont risc E2E', 'Scenariu risc E2E', true);
  11  |   const provider = await realPost(page, '/market/providers', {
  12  |     name: 'Fixture cercetare browser',
  13  |     adapter: 'LOCAL',
  14  |     rights_reference: 'owner://synthetic-browser-fixture',
  15  |     attribution: 'SYNTHETIC_TEST_FIXTURE',
  16  |     usage_rights_acknowledged: true,
  17  |   });
  18  |   const start = Date.parse('2024-01-02T00:00:00Z');
  19  |   const at = (seconds: number) => new Date(start + seconds * 1000).toISOString();
  20  |   const price = (units: number) =>
  21  |     `${Math.floor(units / 10000)}.${String(units % 10000).padStart(4, '0')}`;
  22  |   const csv =
  23  |     [
  24  |       'event_time,observed_at,available_at,bid,ask,sequence',
  25  |       ...Array.from(
  26  |         { length: 101 },
  27  |         (_, i) => `${at(i)},${at(i)},${at(i)},${price(11000 + i)},${price(11002 + i)},${i}`,
  28  |       ),
  29  |     ].join('\n') + '\n';
  30  |   const me = await (await page.request.get('/api/v1/auth/me')).json();
  31  |   const imported = await page.request.post('/api/v1/market/imports', {
  32  |     headers: { Origin: new URL(page.url()).origin, 'X-CSRF-Token': me.csrf_token },
  33  |     multipart: {
  34  |       spec_json: JSON.stringify({
  35  |         provider_id: provider.id,
  36  |         account_id: account.id,
  37  |         instrument_id: run.instrument_id,
  38  |         source_symbol: run.state.spec.symbol,
  39  |         data_type: 'TICK',
  40  |         timeframe: 'TICK',
  41  |         start: at(0),
  42  |         end: at(101),
  43  |         format: 'CSV',
  44  |         provenance: 'SYNTHETIC_TEST_FIXTURE',
  45  |         calendar: run.state.spec.calendar,
  46  |         price_increment: '.0001',
  47  |       }),
  48  |       file: { name: 'synthetic-ticks.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) },
  49  |     },
  50  |   });
  51  |   expect(imported.status()).toBe(202);
  52  |   const upload = await imported.json();
  53  |   await expect
  54  |     .poll(
  55  |       async () =>
  56  |         (await (await page.request.get(`/api/v1/market/datasets/${upload.dataset_id}`)).json())
  57  |           .status,
  58  |       { timeout: 60000 },
  59  |     )
  60  |     .toBe('VALID');
  61  |   await navigateManagement(page, 'Laborator de strategii');
  62  |   const lab = page.getByRole('region', { name: 'Laborator de strategii', exact: true });
> 63  |   await lab.getByLabel('Cont sursă verificat', { exact: true }).selectOption(account.id);
      |                                                                 ^ Error: locator.selectOption: Test timeout of 240000ms exceeded.
  64  |   await lab.getByLabel('Set de date principal', { exact: true }).selectOption(upload.dataset_id);
  65  |   const form = lab.getByRole('form', { name: 'Configurează backtest', exact: true });
  66  |   await form.getByLabel('Șablon simulator și risc', { exact: true }).selectOption(run.id);
  67  |   await form
  68  |     .getByLabel('Denumire experiment', { exact: true })
  69  |     .fill('Experiment cantitativ browser');
  70  |   for (const [label, text] of [
  71  |     ['Perioadă rapidă', '2'],
  72  |     ['Perioadă lentă', '3'],
  73  |     ['Fereastră indicator', '2'],
  74  |     ['Durată maximă (secunde)', '5'],
  75  |     ['Purge (secunde)', '5'],
  76  |     ['Embargo (secunde)', '1'],
  77  |     ['Limită observații', '200'],
  78  |     ['Sfârșit descoperire', at(30)],
  79  |     ['Sfârșit calibrare', at(50)],
  80  |     ['Sfârșit validare', at(75)],
  81  |   ])
  82  |     await form.getByLabel(label, { exact: true }).fill(text);
  83  |   await form.getByRole('checkbox', { name: /Autorizez copierea politicii/ }).check();
  84  |   await form.getByRole('checkbox', { name: /Accept costurile/ }).check();
  85  |   const createdPromise = page.waitForResponse(
  86  |     (response) =>
  87  |       response.url().endsWith('/api/v1/research/experiments') &&
  88  |       response.request().method() === 'POST',
  89  |   );
  90  |   await form.getByRole('button', { name: 'Înregistrează experimentul', exact: true }).click();
  91  |   const createdResponse = await createdPromise;
  92  |   expect(createdResponse.status()).toBe(202);
  93  |   const created = await createdResponse.json();
  94  |   await expect(
  95  |     lab.getByRole('heading', { name: 'Experiment cantitativ browser · SUCCEEDED', exact: true }),
  96  |   ).toBeVisible({ timeout: 120000 });
  97  |   await lab.getByRole('button', { name: `Rezultate ${created.id}`, exact: true }).click();
  98  |   const results = lab.getByRole('region', { name: 'Rezultate experiment', exact: true });
  99  |   await expect(
  100 |     results.getByRole('img', { name: 'Curba capitalului simulat stocat' }),
  101 |   ).toBeVisible();
  102 |   const stored = await (
  103 |     await page.request.get(`/api/v1/research/experiments/${created.id}/results`)
  104 |   ).json();
  105 |   expect(stored.trials[0].risk_validated).toBe(true);
  106 |   expect(stored.trials[0].metrics.trade_count).toBeGreaterThan(0);
  107 |   await results.getByLabel('Replay și analiză', { exact: true }).selectOption('replay');
  108 |   await results.getByRole('button', { name: 'Încarcă analiza', exact: true }).click();
  109 |   await expect(results).toContainText('ALLOW');
  110 |   await results
  111 |     .getByRole('button', { name: 'Proveniență și număr total de încercări', exact: true })
  112 |     .click();
  113 |   const provenance = await (
  114 |     await page.request.get(`/api/v1/research/experiments/${created.id}/provenance`)
  115 |   ).json();
  116 |   await expect(results).toContainText(provenance.plan.datasets[0].manifest_sha256);
  117 |   await form.getByLabel('Denumire experiment', { exact: true }).fill('Experiment anulat browser');
  118 |   await form
  119 |     .getByText('Date pentru confirmare multi-timeframe și sweep-uri', { exact: true })
  120 |     .click();
  121 |   const parameters = provenance.plan.parameters[0];
  122 |   await form
  123 |     .getByLabel('Parametri pentru sweep (JSON, cel mult 16)', { exact: true })
  124 |     .fill(JSON.stringify(Array.from({ length: 16 }, () => parameters)));
  125 |   const cancelledPromise = page.waitForResponse(
  126 |     (response) =>
  127 |       response.url().endsWith('/api/v1/research/experiments') &&
  128 |       response.request().method() === 'POST',
  129 |   );
  130 |   await form.getByRole('button', { name: 'Înregistrează experimentul', exact: true }).click();
  131 |   const queuedResponse = await cancelledPromise;
  132 |   expect(queuedResponse.status()).toBe(202);
  133 |   const queued = await queuedResponse.json();
  134 |   await lab.getByRole('button', { name: `Anulează ${queued.id}`, exact: true }).click();
  135 |   await expect(
  136 |     lab.getByRole('heading', { name: 'Experiment anulat browser · CANCELLED', exact: true }),
  137 |   ).toBeVisible({ timeout: 60000 });
  138 |   expect(
  139 |     (await page.request.get(`/api/v1/research/experiments/${queued.id}/results`)).status(),
  140 |   ).toBe(409);
  141 |   expect((await (await page.request.get('/api/v1/audit/verify')).json()).valid).toBe(true);
  142 |   for (const path of ['/api/v1/orders', '/api/v1/live/activate'])
  143 |     expect((await page.request.post(path, { data: { mode: 'SIMULATED' } })).status()).toBe(403);
  144 |   expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(
  145 |     false,
  146 |   );
  147 | });
  148 | 
```