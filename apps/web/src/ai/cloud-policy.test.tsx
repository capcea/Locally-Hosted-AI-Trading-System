import { expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { cloudDraft, cloudSaveConfirmed, cloudStatusSchema, cloudSubmission } from './cloud-policy';
import type { CloudStatus } from './cloud-policy';
import { CloudAuthorizationForm } from './CloudAuthorizationForm';
import { CloudPolicySummary } from './CloudSetup';

const id = '11111111-1111-4111-8111-111111111111';
function snapshot(provider = 'azure'): CloudStatus {
  return cloudStatusSchema.parse({
    operator_enabled: true,
    provider: 'OPENROUTER',
    base_url: 'https://openrouter.ai/api/v1',
    policy_version: 'openrouter-public-v1',
    disclosure: 'SYNTHETIC_TEST_FIXTURE',
    authorization: {
      id,
      policy: {
        version: 'openrouter-public-v1',
        upstream_provider: provider,
        input_usd_per_million: '0.750000',
        output_usd_per_million: '2.500000',
        request_usd: '0.008000',
        daily_usd: '0.250000',
        acknowledged_public_cloud: true,
        acknowledged_upstream_processing: true,
        acknowledged_cost: true,
        acknowledged_provider_policy_limits: true,
      },
    },
    billing_reservations: [],
  });
}
function formData(provider = 'azure') {
  const data = new FormData();
  for (const [name, value] of Object.entries({
    upstream: provider,
    input_price: '0.750000',
    output_price: '2.500000',
    request_budget: '0.008000',
    daily_budget: '0.250000',
    cloud: 'on',
    upstream_ack: 'on',
    cost: 'on',
    limits: 'on',
  }))
    data.set(name, value);
  return data;
}

it.each(['openai', 'azure', 'azure/swedencentral'])(
  'prefills the exact saved %s provider and billing caps without auto-consent',
  (provider) => {
    const state = snapshot(provider);
    const save = vi.fn();
    const policy = state.authorization!.policy;
    const markup = renderToStaticMarkup(
      <CloudAuthorizationForm policy={policy} busy={false} save={save} />,
    );
    for (const value of Object.values(cloudDraft(policy)))
      expect(markup).toContain(`value="${value}"`);
    expect(markup.match(/type="checkbox"/g)).toHaveLength(4);
    expect(markup).not.toContain('checked=""');
    expect(markup).toContain('Reconfirmarea MFA nu salvează automat');
    expect(save).not.toHaveBeenCalled();
  },
);

it('shows the server-approved provider without requiring technical JSON', () => {
  expect(renderToStaticMarkup(<CloudPolicySummary state={snapshot('openai')} />)).toContain(
    'Furnizor aprobat pe server:',
  );
  expect(renderToStaticMarkup(<CloudPolicySummary state={snapshot('openai')} />)).toContain(
    '<strong>openai</strong>',
  );
  expect(renderToStaticMarkup(<CloudPolicySummary state={snapshot('azure')} />)).toContain(
    '<strong>azure</strong>',
  );
});

it('never calls a typed draft a saved authorization or invents a provider for first setup', () => {
  const state = { ...snapshot(), authorization: null };
  expect(cloudDraft(null).upstream_provider).toBe('');
  const markup = renderToStaticMarkup(<CloudPolicySummary state={state} />);
  expect(markup).toContain('Nicio autorizare cloud salvată');
  expect(markup).not.toContain('<strong>azure</strong>');
});

it('confirms only the exact returned authorization ID and reread submitted values', () => {
  const submitted = cloudSubmission(formData());
  const result = { id: 'openrouter', authorization_id: id };
  expect(cloudSaveConfirmed(result, snapshot(), submitted)).toBe(true);
  expect(cloudSaveConfirmed(undefined, snapshot(), submitted)).toBe(false); // Includes rejected MFA; no optimistic success.
  expect(
    cloudSaveConfirmed(
      { ...result, authorization_id: '22222222-2222-4222-8222-222222222222' },
      snapshot(),
      submitted,
    ),
  ).toBe(false);
  expect(cloudSaveConfirmed(result, snapshot('openai'), submitted)).toBe(false);
  const changed = snapshot();
  changed.authorization!.policy.daily_usd = '0.500000';
  expect(cloudSaveConfirmed(result, changed, submitted)).toBe(false);
});

it('builds approval only from freshly checked controls and never treats saved consents as new approval', () => {
  const data = formData();
  data.delete('cloud');
  data.delete('cost');
  const submitted = cloudSubmission(data);
  expect(submitted.acknowledged_public_cloud).toBe(false);
  expect(submitted.acknowledged_cost).toBe(false);
  expect(submitted.acknowledged_upstream_processing).toBe(true);
  expect(
    cloudSaveConfirmed({ id: 'openrouter', authorization_id: id }, snapshot(), submitted),
  ).toBe(false);
});

it('does not replace an incomplete saved policy with default financial values', () => {
  const state = snapshot();
  const partial = { ...state.authorization!.policy } as Record<string, unknown>;
  delete partial.request_usd;
  expect(() =>
    cloudStatusSchema.parse({ ...state, authorization: { id, policy: partial } }),
  ).toThrow();
});
