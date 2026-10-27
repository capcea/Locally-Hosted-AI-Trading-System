import { expect } from '@playwright/test';
import type { Page } from '@playwright/test';

export async function navigateManagement(page: Page, name: string) {
  await page
    .getByRole('navigation', { name: 'Administrare', exact: true })
    .getByRole('button', { name, exact: true })
    .click();
}
export async function emergencyAction(page: Page, account: string, action: string) {
  await navigateManagement(page, 'Centru de risc');
  const center = page.getByRole('region', { name: 'Centru de risc', exact: true });
  await center
    .getByLabel('Cont pentru controlul riscului', { exact: true })
    .selectOption({ label: account });
  const form = center.getByRole('form', { name: 'Urgență risc', exact: true });
  await form.getByLabel('Acțiune de siguranță', { exact: true }).selectOption(action);
  await form.getByRole('checkbox').check();
  const result = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/emergency') && r.request().method() === 'POST',
  );
  await form.getByRole('button', { name: 'Aplică acțiunea de siguranță', exact: true }).click();
  const response = await result;
  expect(response.status()).toBe(200);
  return response.json();
}
export async function configureRisk(page: Page, account: string, scenario: string, automated=false) {
  await navigateManagement(page, 'Centru de risc');
  const center = page.getByRole('region', { name: 'Centru de risc', exact: true });
  await center
    .getByLabel('Cont pentru controlul riscului', { exact: true })
    .selectOption({ label: account });
  const profile = center.getByRole('form', { name: 'Profil risc independent', exact: true });
  await profile
    .getByRole('checkbox', {
      name: 'Confirm limite interne pentru simulare; nu reprezintă permisiuni de tranzacționare.',
    })
    .check();
  const savedProfile = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/profiles') && r.request().method() === 'POST',
  );
  await profile.getByRole('button', { name: 'Salvează versiunea profilului', exact: true }).click();
  expect((await savedProfile).status()).toBe(201);
  const policy = center.getByRole('form', { name: 'Politică risc verificabilă', exact: true });
  await policy
    .getByRole('checkbox', {
      name: 'Confirm regulile și perioada declarate. Politica internă nu este o regulă oficială de firmă.',
    })
    .check();
  if(automated) await policy.getByLabel('Automatizare permisă explicit de politică',{exact:true}).check();
  const savedPolicy = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/policies') && r.request().method() === 'POST',
  );
  await policy.getByRole('button', { name: 'Salvează politica neverificată', exact: true }).click();
  expect((await savedPolicy).status()).toBe(201);
  await expect(
    center.getByRole('heading', { name: 'Politică v1 · UNVERIFIED', exact: true }),
  ).toBeVisible();
  const attest = center.getByRole('form', { name: 'Confirmare politică v1', exact: true });
  await attest.getByRole('checkbox').check();
  const attested = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/attest') && r.request().method() === 'POST',
  );
  await attest
    .getByRole('button', { name: 'Înregistrează atestarea politicii v1', exact: true })
    .click();
  expect((await attested).status()).toBe(200);
  await expect(
    center.getByRole('heading', { name: 'Politică v1 · VERIFIED', exact: true }),
  ).toBeVisible();
  await center
    .getByLabel('Scenariu pentru evaluarea riscului', { exact: true })
    .selectOption({ label: scenario });
  const context = center.getByRole('form', { name: 'Context monetar simulat', exact: true });
  await context
    .getByLabel('Valoare tick în moneda profitului pe unitate', { exact: true })
    .fill('10');
  await context
    .getByLabel('Marjă sintetică pe unitate în moneda contului', { exact: true })
    .fill('1000');
  await context
    .getByRole('checkbox', { name: 'Confirm explicit ipotezele sintetice și proveniența lor.' })
    .check();
  const savedContext = page.waitForResponse(
    (r) => new URL(r.url()).pathname.endsWith('/contexts') && r.request().method() === 'POST',
  );
  await context.getByRole('button', { name: 'Salvează contextul monetar', exact: true }).click();
  expect((await savedContext).status()).toBe(201);
  const result = await emergencyAction(page, account, 'CLEAR_STOP');
  expect(result.completed).toBe(true);
  await expect(center.getByRole('region', { name: 'Stare risc cont', exact: true })).toContainText(
    'Verificare obligatorie',
  );
}
