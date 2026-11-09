import { expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import AIChat from './AIChat';
import { inferenceUnavailable } from './readiness';
import type { ReadinessObservation } from './readiness';
import type { Session } from '../management-api';
import { standingAction } from './StandingAuthorization';
import { ModelProbe } from './ModelProbe';

const now = Date.parse('2026-10-29T12:00:00Z');
function observed(): ReadinessObservation {
  return {
    role: 'RESEARCH',
    category: 'documentation',
    received: now,
    value: {
      ready: true,
      reason: null,
      observed_at: new Date(now).toISOString(),
      gateway_configured: true,
      worker_state: 'OBSERVED_RECENTLY',
      worker_expires_at: new Date(now + 20000).toISOString(),
      model_verified: true,
      standing_active: true,
      standing_authorization_id: 'synthetic-standing-id',
      budget: { available: true },
    },
  };
}
it('requires all actual readiness gates even if ready is incorrectly true', () => {
  expect(inferenceUnavailable(observed(), 'RESEARCH', 'documentation', now)).toBe('');
  for (const delta of [
    { gateway_configured: false },
    { standing_active: false },
    { model_verified: false },
    { standing_authorization_id: null },
    { worker_state: 'UNKNOWN' },
    { worker_expires_at: new Date(now - 1).toISOString() },
    { budget: { available: false } },
  ]) {
    const row = observed();
    Object.assign(row.value, delta);
    expect(inferenceUnavailable(row, 'RESEARCH', 'documentation', now)).not.toBe('');
  }
});
it('never reuses a stale observation or the previous role/data category', () => {
  for (const time of [now - 1, now + 20000])
    expect(inferenceUnavailable(observed(), 'RESEARCH', 'documentation', time)).not.toBe('');
  expect(inferenceUnavailable(observed(), 'CRITIC', 'documentation', now)).not.toBe('');
  expect(inferenceUnavailable(observed(), 'RESEARCH', 'dataset', now)).not.toBe('');
  const row = observed();
  row.value.observed_at = 'invalid';
  expect(inferenceUnavailable(row, 'RESEARCH', 'documentation', now)).not.toBe('');
  expect(inferenceUnavailable(null, 'RESEARCH', 'documentation', now)).not.toBe('');
});
it.each([
  'AI_STANDING_AUTHORIZATION_REQUIRED',
  'AI_CLOUD_BUDGET_EXCEEDED',
  'AI_WORKER_UNAVAILABLE',
  'AI_MODEL_REQUIRES_VERIFICATION',
])(
  'explains server refusal %s and permits recovery only from a fresh ready observation',
  (reason) => {
    const row = observed();
    row.value.ready = false;
    row.value.reason = reason;
    expect(inferenceUnavailable(row, 'RESEARCH', 'documentation', now)).not.toBe('');
    expect(inferenceUnavailable(observed(), 'RESEARCH', 'documentation', now)).toBe('');
  },
);
it('removes repeated rights, remote and cost controls from the actual chat composer', () => {
  vi.stubGlobal('window', { location: { pathname: '/testeaza/ai' } });
  try {
    const markup = renderToStaticMarkup(
      <AIChat session={{ user: { id: 'owner', role: 'OWNER' }, csrf_token: '' } as Session} />,
    );
    expect(markup).not.toContain('Am dreptul să trimit acest context');
    expect(markup).not.toContain('Permit procesarea pe infrastructura la distanță');
    expect(markup).not.toContain('Aprob costul unei solicitări');
    expect(markup).toContain('Autorizarea permanentă și limitele sunt verificate de server');
    expect(markup).toContain('SIMULATED / DENY_ALL');
  } finally {
    vi.unstubAllGlobals();
  }
});
it('keeps a standing-funded probe explicit without a repetitive cost checkbox', () => {
  const submit = vi.fn();
  const markup = renderToStaticMarkup(
    <ModelProbe
      modelName="SYNTHETIC_FIXTURE"
      busy={false}
      connection={{
        id: 'connection',
        name: 'fixture',
        enabled: true,
        provider: 'OPENROUTER',
        credential_configured: true,
      }}
      costApproved={false}
      standingAuthorized
      setCostApproved={() => undefined}
      submit={submit}
    />,
  );
  expect(markup).not.toContain('type="checkbox"');
  expect(markup).not.toContain('disabled=""');
  expect(markup).toContain('autorizarea permanentă');
  expect(submit).not.toHaveBeenCalled();
});
it('does not use an unrelated, revoked or narrower standing grant for technical operations', () => {
  const state = {
    authorization: {
      id: 'id',
      revision: 1,
      active: true,
      policy: {
        connection_ids: ['c'],
        roles: ['LIGHTWEIGHT'],
        operations: ['PROBE'],
        data_categories: ['documentation'],
        request_usd: '0.01',
        daily_usd: '0.50',
        monthly_usd: '5',
        grants: [],
      },
    },
  };
  expect(standingAction(state, 'PROBE', 'c')).toBe('id');
  expect(standingAction(state, 'DISCOVER', 'c')).toBeUndefined();
  expect(standingAction(state, 'PROBE', 'other')).toBeUndefined();
  state.authorization.active = false;
  expect(standingAction(state, 'PROBE', 'c')).toBeUndefined();
});
