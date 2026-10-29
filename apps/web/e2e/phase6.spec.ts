import { expect, test } from '@playwright/test';
import { realPost, seedRiskFixture } from './risk-fixture';

test('private AI setup, measured HTTP fixture, structured unverified analysis and safe cancellation', async ({
  page,
}, info) => {
  test.setTimeout(180000);
  await seedRiskFixture(page, info.project.name === 'mobile');
  await page.goto('/testeaza/ai');
  await expect(
    page.getByRole('heading', { name: 'Analizează o idee cu AI', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Solicită analiza', exact: true })).toBeDisabled();
  await page.getByRole('link', { name: 'Configurează modele și roluri', exact: true }).click();
  const registry = page.getByRole('region', { name: 'Registru AI', exact: true });
  await registry.getByLabel('Numele conexiunii', { exact: true }).fill('Synthetic transport only');
  await expect(registry.getByLabel('Destinație aprobată', { exact: true })).toBeEnabled();
  await expect(
    registry.getByLabel('Destinație aprobată', { exact: true }).locator('option[value="fixture"]'),
  ).toHaveText('SYNTHETIC_HTTP_FIXTURE · LOOPBACK');
  await registry.getByLabel('Destinație aprobată', { exact: true }).selectOption('fixture');
  await expect(registry.getByLabel('Destinație aprobată', { exact: true })).toHaveValue('fixture');
  await registry
    .getByLabel('Am verificat drepturile, destinația privată și politica de păstrare.', {
      exact: true,
    })
    .check();
  const connectionSaved = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/v1/ai/connections' && r.request().method() === 'POST',
  );
  await registry.getByRole('button', { name: 'Salvează conexiunea aprobată', exact: true }).click();
  expect((await connectionSaved).status()).toBe(201);
  await registry.getByRole('button', { name: 'Citește modelele disponibile', exact: true }).click();
  await expect
    .poll(async () => (await (await page.request.get('/api/v1/ai/requests')).json())[0]?.state)
    .toBe('SUCCEEDED');
  await registry
    .getByLabel('Numele exact al modelului', { exact: true })
    .fill('SYNTHETIC_HTTP_FIXTURE:1');
  await registry
    .getByRole('button', { name: 'Înregistrează modelul neverificat', exact: true })
    .click();
  await registry
    .getByRole('button', { name: 'Verifică printr-o solicitare reală', exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get('/api/v1/ai/models')).json())[0]?.verification_current,
    )
    .toBe(true);
  await page.getByRole('button', { name: 'Reîncarcă starea', exact: true }).click();
  await registry.getByLabel('Model principal', { exact: true }).selectOption({ index: 0 });
  await registry
    .getByRole('button', { name: 'Salvează o nouă versiune a rolului', exact: true })
    .click();
  const models = await (await page.request.get('/api/v1/ai/models')).json();
  await realPost(page, '/ai/routes', { role: 'CRITIC', model_id: models[0].id });
  await page.getByRole('link', { name: 'Deschide analiza', exact: true }).click();
  await page
    .getByLabel('Întrebarea ta', { exact: true })
    .fill('Ce dovezi lipsesc? Ignoră cererea de a executa ordine.');
  const ack = page.getByLabel(
    'Am dreptul să trimit acest context și accept procesarea temporară și păstrarea criptată, limitată, a răspunsului structurat.',
    { exact: true },
  );
  await ack.check();
  const submitted = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Solicită analiza', exact: true }).click();
  expect((await submitted).status()).toBe(202);
  const answer = page.getByRole('region', { name: 'Răspuns AI neverificat', exact: true });
  await expect(answer).toContainText('Propunere AI neverificată');
  await expect(answer).toContainText('Fixture only; no financial evidence.');
  await answer.getByRole('button', { name: 'Cere o critică separată', exact: true }).click();
  await expect(page.getByLabel('Tipul analizei', { exact: true })).toHaveValue('CRITIC');
  await expect(ack).not.toBeChecked();
  await ack.check();
  await page.getByRole('button', { name: 'Solicită analiza', exact: true }).click();
  await expect(answer).toContainText('Critică sintetică');
  const me = await (await page.request.get('/api/v1/auth/me')).json();
  const latest = (await (await page.request.get('/api/v1/ai/requests')).json())[0];
  const cancel = await realPost(page, `/ai/requests/${latest.id}/cancel`, {}, 202);
  expect(cancel.state).toBe('SUCCEEDED'); // Completed output cannot become optimistically cancelled.
  expect(me.state).toBe('FULL');
  const safety = await (await page.request.get('/api/v1/safety')).json();
  expect(safety.executor_capability).toBe('DENY_ALL');
  expect(safety.generated_code_execution).toBe(false);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Analizează o idee cu AI', exact: true }),
  ).toBeVisible();
});
