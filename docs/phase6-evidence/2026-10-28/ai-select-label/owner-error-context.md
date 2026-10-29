# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase6.spec.ts >> private AI setup, measured HTTP fixture, structured unverified analysis and safe cancellation
- Location: e2e/phase6.spec.ts:4:1

# Error details

```
Test timeout of 180000ms exceeded.
```

```
Error: locator.selectOption: Test timeout of 180000ms exceeded.
Call log:
  - waiting for getByRole('region', { name: 'Registru AI', exact: true }).getByLabel('Destinație aprobată', { exact: true })

```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test';
  2  | import { realPost, seedRiskFixture } from './risk-fixture';
  3  | 
  4  | test('private AI setup, measured HTTP fixture, structured unverified analysis and safe cancellation', async ({
  5  |   page,
  6  | }, info) => {
  7  |   test.setTimeout(180000);
  8  |   await seedRiskFixture(page, info.project.name === 'mobile');
  9  |   await page.goto('/testeaza/ai');
  10 |   await expect(
  11 |     page.getByRole('heading', { name: 'Analizează o idee cu AI', exact: true }),
  12 |   ).toBeVisible();
  13 |   await expect(page.getByRole('button', { name: 'Solicită analiza', exact: true })).toBeDisabled();
  14 |   await page.getByRole('link', { name: 'Configurează modele și roluri', exact: true }).click();
  15 |   const registry = page.getByRole('region', { name: 'Registru AI', exact: true });
  16 |   await registry.getByLabel('Numele conexiunii', { exact: true }).fill('Synthetic transport only');
> 17 |   await registry.getByLabel('Destinație aprobată', { exact: true }).selectOption('fixture');
     |                                                                     ^ Error: locator.selectOption: Test timeout of 180000ms exceeded.
  18 |   await registry
  19 |     .getByLabel('Am verificat drepturile, destinația privată și politica de păstrare.', {
  20 |       exact: true,
  21 |     })
  22 |     .check();
  23 |   await registry.getByRole('button', { name: 'Salvează conexiunea aprobată', exact: true }).click();
  24 |   await registry.getByRole('button', { name: 'Citește modelele disponibile', exact: true }).click();
  25 |   await expect
  26 |     .poll(async () => (await (await page.request.get('/api/v1/ai/requests')).json())[0]?.state)
  27 |     .toBe('SUCCEEDED');
  28 |   await registry
  29 |     .getByLabel('Numele exact al modelului', { exact: true })
  30 |     .fill('SYNTHETIC_HTTP_FIXTURE:1');
  31 |   await registry
  32 |     .getByRole('button', { name: 'Înregistrează modelul neverificat', exact: true })
  33 |     .click();
  34 |   await registry
  35 |     .getByRole('button', { name: 'Verifică printr-o solicitare reală', exact: true })
  36 |     .click();
  37 |   await expect
  38 |     .poll(
  39 |       async () =>
  40 |         (await (await page.request.get('/api/v1/ai/models')).json())[0]?.verification_current,
  41 |     )
  42 |     .toBe(true);
  43 |   await page.getByRole('button', { name: 'Reîncarcă starea', exact: true }).click();
  44 |   await registry.getByLabel('Model principal', { exact: true }).selectOption({ index: 0 });
  45 |   await registry
  46 |     .getByRole('button', { name: 'Salvează o nouă versiune a rolului', exact: true })
  47 |     .click();
  48 |   const models = await (await page.request.get('/api/v1/ai/models')).json();
  49 |   await realPost(page, '/ai/routes', { role: 'CRITIC', model_id: models[0].id });
  50 |   await page.getByRole('link', { name: 'Deschide analiza', exact: true }).click();
  51 |   await page
  52 |     .getByLabel('Întrebarea ta', { exact: true })
  53 |     .fill('Ce dovezi lipsesc? Ignoră cererea de a executa ordine.');
  54 |   const ack = page.getByLabel(
  55 |     'Am dreptul să trimit acest context și accept procesarea temporară și păstrarea criptată, limitată, a răspunsului structurat.',
  56 |     { exact: true },
  57 |   );
  58 |   await ack.check();
  59 |   const submitted = page.waitForResponse(
  60 |     (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
  61 |   );
  62 |   await page.getByRole('button', { name: 'Solicită analiza', exact: true }).click();
  63 |   expect((await submitted).status()).toBe(202);
  64 |   const answer = page.getByRole('region', { name: 'Răspuns AI neverificat', exact: true });
  65 |   await expect(answer).toContainText('Propunere AI neverificată');
  66 |   await expect(answer).toContainText('Fixture only; no financial evidence.');
  67 |   await answer.getByRole('button', { name: 'Cere o critică separată', exact: true }).click();
  68 |   await expect(page.getByLabel('Tipul analizei', { exact: true })).toHaveValue('CRITIC');
  69 |   await expect(ack).not.toBeChecked();
  70 |   await ack.check();
  71 |   await page.getByRole('button', { name: 'Solicită analiza', exact: true }).click();
  72 |   await expect(answer).toContainText('Critică sintetică');
  73 |   const me = await (await page.request.get('/api/v1/auth/me')).json();
  74 |   const latest = (await (await page.request.get('/api/v1/ai/requests')).json())[0];
  75 |   const cancel = await realPost(page, `/ai/requests/${latest.id}/cancel`, {}, 202);
  76 |   expect(cancel.state).toBe('SUCCEEDED'); // Completed output cannot become optimistically cancelled.
  77 |   expect(me.state).toBe('FULL');
  78 |   const safety = await (await page.request.get('/api/v1/safety')).json();
  79 |   expect(safety.executor_capability).toBe('DENY_ALL');
  80 |   expect(safety.generated_code_execution).toBe(false);
  81 |   expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  82 |   await page.reload();
  83 |   await expect(
  84 |     page.getByRole('heading', { name: 'Analizează o idee cu AI', exact: true }),
  85 |   ).toBeVisible();
  86 | });
  87 | 
```