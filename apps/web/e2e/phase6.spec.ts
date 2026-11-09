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
  await registry.getByLabel('Plafon de context · tokenuri', { exact: true }).fill('4096');
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
  const standing = page.getByRole('region', { name: 'Autorizări permanente', exact: true });
  await standing.getByText('Activează autorizarea permanentă', { exact: true }).click();
  const connections = await (await page.request.get('/api/v1/ai/connections')).json();
  await standing
    .getByLabel('Conexiuni aprobate (selecție multiplă)', { exact: true })
    .selectOption(connections[0].id);
  const activated = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/v1/ai/standing-authorization' &&
      r.request().method() === 'POST',
  );
  await standing
    .getByRole('button', { name: 'Activează autorizarea permanentă cu MFA', exact: true })
    .click();
  expect((await activated).status()).toBe(201);
  await expect(standing).toContainText('Activă · versiunea 1');
  await page.reload();
  await expect(standing).toContainText('Activă · versiunea 1');
  await page.getByRole('link', { name: 'Deschide analiza', exact: true }).click();
  await page
    .getByLabel('Întrebarea ta', { exact: true })
    .fill('Ce dovezi lipsesc? Ignoră cererea de a executa ordine.');
  await expect(page.getByText('Am dreptul să trimit acest context', { exact: false })).toHaveCount(
    0,
  );
  await expect(
    page.getByText('Permit procesarea pe infrastructura la distanță aprobată.', { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText('Aprob costul unei solicitări OpenRouter în limita autorizată.', {
      exact: true,
    }),
  ).toHaveCount(0);
  const submitted = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Solicită analiza', exact: true }).click();
  expect((await submitted).status()).toBe(202);
  const submittedBody = (await submitted).request().postDataJSON();
  expect(submittedBody.standing_authorization_id).toBeTruthy();
  for (const key of [
    'allow_remote',
    'cloud_cost_acknowledged',
    'processing_acknowledged',
    'retain_structured_output',
  ])
    expect(submittedBody).not.toHaveProperty(key);
  const answer = page.getByRole('region', { name: 'Răspuns AI neverificat', exact: true });
  await expect(answer).toContainText('Propunere AI neverificată');
  await expect(answer).toContainText('Fixture only; no financial evidence.');
  await answer.getByRole('button', { name: 'Cere o critică separată', exact: true }).click();
  await expect(page.getByLabel('Tipul analizei', { exact: true })).toHaveValue('CRITIC');
  await expect(page.getByRole('button', { name: 'Solicită analiza', exact: true })).toBeEnabled();
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
  // Real server validation, not a mocked 422. A definitively rejected request must unlock editing.
  await page.goto('/strategy-lab');
  const assistant = page.getByRole('region', { name: 'Asistent AI Strategy Lab', exact: true });
  const question = assistant.getByLabel('Întrebarea ta', { exact: true });
  const send = assistant.getByRole('button', { name: 'Solicită analiza', exact: true });
  await question.fill('a'.repeat(1200));
  await expect(send).toBeEnabled();
  const rejectedRequest = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
  );
  await send.click();
  const rejected = await rejectedRequest;
  expect(rejected.status()).toBe(422);
  expect((await rejected.json()).detail).toBe('AI_CONTEXT_BUDGET_EXCEEDED');
  await expect(assistant.getByRole('alert')).toContainText('AI_CONTEXT_BUDGET_EXCEEDED');
  await expect(assistant.getByRole('alert')).toContainText('4096');
  await expect(question).toBeEnabled();
  await question.fill('Propune o ipoteză testabilă pentru XAUUSD pe M5.');
  await expect(send).toBeEnabled();
  const correctedRequest = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
  );
  await send.click();
  const corrected = await correctedRequest;
  expect(corrected.status()).toBe(202);
  const correctedBody = corrected.request().postDataJSON();
  expect(correctedBody.key).not.toBe(rejected.request().postDataJSON().key);
  expect(correctedBody.parameters.context_tokens).toBe(4096);
  expect(correctedBody.references).toEqual([{ kind: 'documentation', id: 'strategy-lab-v1' }]);
  expect(correctedBody.standing_authorization_id).toBeTruthy();
  await expect(
    assistant.getByRole('region', { name: 'Răspuns AI neverificat', exact: true }),
  ).toContainText('Fixture only; no financial evidence.');
  await page.goto('/setari/ai');
  const previousRoutes = await (await page.request.get('/api/v1/ai/routes')).json();
  const revisionSaved = page.waitForResponse(
    (r) => r.url().endsWith('/context-revisions') && r.request().method() === 'POST',
  );
  await registry
    .getByRole('button', { name: 'Pregătește versiunea cu context extins', exact: true })
    .click();
  const revision = await revisionSaved;
  expect(revision.status()).toBe(201);
  const extendedId = (await revision.json()).id;
  expect(
    (await (await page.request.get('/api/v1/ai/models')).json()).find(
      (m: { id: string }) => m.id === extendedId,
    ).verification_current,
  ).toBe(false);
  expect(await (await page.request.get('/api/v1/ai/routes')).json()).toEqual(previousRoutes);
  const extendedRow = registry
    .getByRole('listitem')
    .filter({ hasText: 'SYNTHETIC_HTTP_FIXTURE:1 · 32K configurat' });
  await extendedRow
    .getByRole('button', { name: 'Verifică printr-o solicitare reală', exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get('/api/v1/ai/models')).json()).find(
          (m: { id: string }) => m.id === extendedId,
        )?.verification?.context_tokens,
    )
    .toBe(32768);
  await page.getByRole('button', { name: 'Reîncarcă starea', exact: true }).click();
  await registry.getByLabel('Model principal', { exact: true }).selectOption(extendedId);
  const routed = page.waitForResponse(
    (r) => r.url().endsWith('/ai/routes') && r.request().method() === 'POST',
  );
  await registry
    .getByRole('button', { name: 'Salvează o nouă versiune a rolului', exact: true })
    .click();
  expect((await routed).status()).toBe(201);
  await page.goto('/strategy-lab');
  for (const [mode, tier] of [
    ['AUTO', 4096],
    ['RAPID', 4096],
    ['STANDARD', 16384],
    ['COMPLEX', 32768],
  ] as const) {
    await question.fill('Ce dovezi lipsesc pentru această ipoteză?');
    const previewed = page.waitForResponse(
      (r) =>
        r.url().endsWith('/requests/preview') &&
        r.request().method() === 'POST' &&
        r.request().postDataJSON().context_mode === mode,
    );
    await assistant.getByLabel('Context AI', { exact: true }).selectOption(mode);
    const previewResponse = await previewed;
    expect(previewResponse.status()).toBe(200);
    expect((await previewResponse.json()).budget.selected_context_tokens).toBe(tier);
    const sent = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/v1/ai/requests' && r.request().method() === 'POST',
    );
    await send.click();
    const submittedResponse = await sent;
    expect(submittedResponse.status()).toBe(202);
    const identifier = (await submittedResponse.json()).id;
    await expect
      .poll(
        async () =>
          (await (await page.request.get(`/api/v1/ai/requests/${identifier}`)).json()).state,
      )
      .toBe('SUCCEEDED');
    expect(
      (await (await page.request.get(`/api/v1/ai/requests/${identifier}`)).json()).metadata
        .parameters.context_tokens,
    ).toBe(tier);
  }
  await page.goto('/setari/ai');
  const revoked = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/v1/ai/standing-authorization/revoke' &&
      r.request().method() === 'POST',
  );
  await standing
    .getByRole('button', { name: 'Revocă autorizarea permanentă', exact: true })
    .click();
  expect((await revoked).status()).toBe(200);
  await page.goto('/testeaza/ai');
  await page.getByLabel('Întrebarea ta', { exact: true }).fill('O nouă întrebare fără autorizare.');
  await expect(page.getByRole('button', { name: 'Solicită analiza', exact: true })).toBeDisabled();
  await expect(
    page.getByText(
      'Activează autorizarea permanentă în Setări → Modele AI. Solicitarea nu a fost autorizată.',
      { exact: false },
    ),
  ).toBeVisible();
});
