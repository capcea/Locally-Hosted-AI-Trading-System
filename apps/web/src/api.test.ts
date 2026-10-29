import { afterEach, describe, expect, it, vi } from 'vitest';
import { isStale, readinessSummary } from './api';
import { getOverview } from './api';
import type { Service } from './api';
import { contractFixture } from './overview.fixture';
import { parseOverview } from './schema';

afterEach(() => vi.unstubAllGlobals());

describe('untrusted API payloads', () => {
  it('accepts the explicit simulation-only contract', () => {
    expect(parseOverview(contractFixture()).safety.mode).toBe('SIMULATED');
  });
  it('accepts the current Phase6 contract without accepting future phases or live authority', () => {
    expect(parseOverview({ ...contractFixture(), phase: 6 }).phase).toBe(6);
    expect(() => parseOverview({ ...contractFixture(), phase: 7 })).toThrow();
  });
  it.each([
    'mode',
    'live_trading_enabled',
    'order_submission_enabled',
    'generated_code_execution',
    'executor_capability',
  ])('rejects unsafe %s', (field) => {
    const fixture = contractFixture();
    expect(() =>
      parseOverview({
        ...fixture,
        safety: { ...fixture.safety, [field]: field === 'mode' ? 'LIVE' : true },
      }),
    ).toThrow('Contract API invalid');
  });
  it.each([null, {}, { safety: { mode: 'SIMULATED' } }])('rejects incomplete data', (value) => {
    expect(() => parseOverview(value)).toThrow('Contract API invalid');
  });
  it('rejects invalid monetary references and false provenance', () => {
    const fixture = contractFixture();
    for (const equity of ['NaN', '-25000', 'Infinity']) {
      expect(() =>
        parseOverview({ ...fixture, reference_profile: { ...fixture.reference_profile, equity } }),
      ).toThrow();
    }
    expect(() => parseOverview({ ...fixture, performance_data_available: true })).toThrow();
  });
  it('does not treat HTTP 200 with a malformed body as healthy', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ safety: { mode: 'LIVE' } }) }),
    );
    await expect(getOverview()).rejects.toThrow('Contract API invalid');
  });
  it.each(['timestamp', 'services', 'safety'])('rejects a missing %s field', (field) => {
    const fixture = { ...contractFixture() } as Record<string, unknown>;
    delete fixture[field];
    expect(() => parseOverview(fixture)).toThrow('Contract API invalid');
  });
  it.each(['DEGRADED', 'DOWN', 'UNKNOWN', 'healthy', null])(
    'rejects an undocumented service enum %s instead of assuming health',
    (status) => {
      const fixture = contractFixture();
      expect(() =>
        parseOverview({ ...fixture, services: [{ ...fixture.services[0], status }] }),
      ).toThrow('Contract API invalid');
    },
  );
});

describe('operational state presentation', () => {
  it('treats unknown or expired observations as stale', () => {
    expect(isStale(null, 100)).toBe(true);
    expect(isStale(1_000, 46_001)).toBe(true);
    expect(isStale(1_000, 46_000)).toBe(false);
    expect(isStale(1_000, 999)).toBe(true);
    expect(isStale(NaN, 1_000)).toBe(true);
    expect(isStale(1_000, NaN)).toBe(true);
  });
  it('never counts a future broker or disabled executor as a healthy dependency', () => {
    const services: Service[] = [
      { id: 'api', name: 'API', status: 'HEALTHY', detail: '', latency_ms: null },
      { id: 'postgres', name: 'Postgres', status: 'UNAVAILABLE', detail: '', latency_ms: null },
      { id: 'redis', name: 'Redis', status: 'NOT_CONFIGURED', detail: '', latency_ms: null },
      { id: 'storage', name: 'Storage', status: 'HEALTHY', detail: '', latency_ms: null },
      { id: 'mt5', name: 'MT5', status: 'PENDING_IMPLEMENTATION', detail: '', latency_ms: null },
      { id: 'executor', name: 'Executor', status: 'DISABLED', detail: '', latency_ms: null },
    ];
    expect(readinessSummary(services)).toEqual({ healthy: 2, total: 4 });
  });
});
