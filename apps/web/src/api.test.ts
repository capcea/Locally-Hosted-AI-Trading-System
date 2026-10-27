import { afterEach, describe, expect, it, vi } from 'vitest';
import { isStale, readinessSummary } from './api';
import { getOverview } from './api';
import type { Overview, Service } from './api';
import { parseOverview } from './schema';

// Synthetic contract fixture for validation tests only; never a quote or broker response.
function contractFixture(): Overview {
  return {
    application: 'AI Trading Research Platform',
    version: '0.1.0',
    phase: 0,
    timestamp: '2026-10-25T12:00:00Z',
    uptime_seconds: 1,
    trading_data_available: false,
    performance_data_available: false,
    safety: {
      mode: 'SIMULATED',
      live_trading_enabled: false,
      order_submission_enabled: false,
      executor_capability: 'DENY_ALL',
      generated_code_execution: false,
      read_only: true,
      reasons: ['TEST_FIXTURE'],
    },
    services: [
      {
        id: 'api',
        name: 'Test API',
        detail: 'SYNTHETIC_TEST_FIXTURE',
        status: 'HEALTHY',
        latency_ms: null,
      },
    ],
    reference_profile: {
      provenance: 'CONFIGURATION_EXAMPLE',
      currency: 'USD',
      equity: '25000.00',
      risk_per_trade_pct: '0.25',
      daily_loss_pct: '1.00',
      total_drawdown_pct: '3.00',
      open_risk_pct: '1.00',
      enforced: false,
    },
    roadmap: [{ number: 0, title: 'Test', status: 'CURRENT', acceptance: 'Test fixture only' }],
  };
}

afterEach(() => vi.unstubAllGlobals());

describe('untrusted API payloads', () => {
  it('accepts the explicit simulation-only contract', () => {
    expect(parseOverview(contractFixture()).safety.mode).toBe('SIMULATED');
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
});

describe('operational state presentation', () => {
  it('treats unknown or expired observations as stale', () => {
    expect(isStale(null, 100)).toBe(true);
    expect(isStale(1_000, 46_001)).toBe(true);
    expect(isStale(1_000, 46_000)).toBe(false);
    expect(isStale(1_000, 999)).toBe(true);
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
