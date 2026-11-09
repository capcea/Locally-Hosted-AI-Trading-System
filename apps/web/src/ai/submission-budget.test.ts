import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from '../management-api';
import type { Model, Binding } from './api';
import { afterSubmissionFailure, verifiedContextWindow } from './submission-budget';
import { parseBudgetDiagnostics } from './budget-diagnostics';

const now = Date.parse('2026-10-30T12:00:00Z');
const model: Model = {
  id: 'verified',
  name: 'fixture',
  connection_id: 'fixture',
  context_ceiling: 4096,
  verification_current: true,
  verified_until: '2026-10-30T13:00:00Z',
  verification: { context_tokens: 4096 },
};
const binding: Binding = { role: 'RESEARCH', model_id: model.id, revision: 1, fallback_ids: [] };
const budget = {
  message_content_bytes: 2000,
  schema_bytes: 1053,
  input_upper_bound: 3053,
  framing_tokens: 512,
  output_tokens: 768,
  requested_context_tokens: 4096,
  registered_context_tokens: 4096,
  verified_context_tokens: 4096,
  effective_context_tokens: 4096,
  required_context_upper_bound: 4333,
};
afterEach(() => vi.unstubAllGlobals());
describe('AI capacity and deterministic submission recovery', () => {
  it('uses actual verification and the smaller approved fallback ceiling', () => {
    expect(verifiedContextWindow([model], binding, false, now)).toBe(4096);
    const fallback = { ...model, id: 'fallback', context_ceiling: 2048 };
    const route = { ...binding, fallback_ids: ['fallback'] };
    expect(verifiedContextWindow([model, fallback], route, true, now)).toBe(2048);
    expect(verifiedContextWindow([model, fallback], route, false, now)).toBe(4096);
  });
  it.each([null, {}, { context_tokens: '4096' }, { context_tokens: true }])(
    'refuses missing or invalid capacity metadata: %s',
    (verification) => {
      expect(verifiedContextWindow([{ ...model, verification }], binding, false, now)).toBeNull();
    },
  );
  it('refuses expired or missing models rather than assuming the default', () => {
    expect(verifiedContextWindow([model], binding, false, now + 3600000)).toBeNull();
    expect(verifiedContextWindow([], binding, false, now)).toBeNull();
    expect(verifiedContextWindow([model], undefined, false, now)).toBeNull();
  });
  it('unfreezes a definitive 422 but preserves the exact request on uncertainty', () => {
    const frozen = { key: 'keep-exact-key', question: 'fixture' };
    expect(afterSubmissionFailure(frozen, new ApiError(422, 'budget'))).toBeNull();
    for (const error of [
      new TypeError('network'),
      new ApiError(503, 'unavailable'),
      new ApiError(409, 'unknown'),
    ]) {
      expect(afterSubmissionFailure(frozen, error)).toBe(frozen);
    }
  });
  it('parses allowlisted integer sizes only; never displays arbitrary diagnostic data', () => {
    expect(parseBudgetDiagnostics(JSON.stringify({ ...budget, secret: 'do-not-reflect' }))).toEqual(
      budget,
    );
    expect(
      parseBudgetDiagnostics(JSON.stringify({ ...budget, schema_bytes: 'sensitive' })),
    ).toBeUndefined();
    expect(
      parseBudgetDiagnostics(JSON.stringify({ ...budget, output_tokens: -1 })),
    ).toBeUndefined();
    expect(parseBudgetDiagnostics('invalid')).toBeUndefined();
  });
  it('shows the specific context error and limits, without retrying the rejected request', async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'AI_CONTEXT_BUDGET_EXCEEDED' }), {
        status: 422,
        headers: { 'X-AI-Context-Budget': JSON.stringify({ ...budget, secret: 'do-not-reflect' }) },
      }),
    );
    vi.stubGlobal('fetch', fetcher);
    const failure = await api('/ai/requests', { method: 'POST', body: {} }).catch(
      (error: unknown) => error,
    );
    expect(failure).toBeInstanceOf(ApiError);
    expect(failure).toMatchObject({ status: 422, code: 'AI_CONTEXT_BUDGET_EXCEEDED', budget });
    expect((failure as Error).message).toContain('4096');
    expect((failure as Error).message).toContain('4333');
    expect((failure as Error).message).not.toContain('do-not-reflect');
    expect((failure as Error).message).not.toContain('Date invalide.');
    expect((failure as Error).message).toContain('Poți edita întrebarea');
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
