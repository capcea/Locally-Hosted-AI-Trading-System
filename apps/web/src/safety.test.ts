import { describe, expect, it } from 'vitest';
import type { components } from './generated/api';
import { safetyLabel } from './RiskBanner';

type Status = components['schemas']['AccountStatus'];
const now = Date.parse('2026-10-27T12:00:00Z');
const status = (patch: Partial<Status> = {}): Status => ({
  account_id: 'fixture',
  currency: 'USD',
  configured: true,
  ledger_verified: true,
  data_verified: true,
  manual_stop: false,
  automatic_stop: false,
  reasons: [],
  revision: 1,
  monitor_at: '2026-10-27T11:59:59Z',
  clock: null,
  values: null,
  daily_headroom: null,
  total_headroom: null,
  ledger_sequence: 0,
  ledger_digest: 'fixture',
  source: 'SIMULATED',
  external_execution_authorized: false,
  ...patch,
});
describe('safety does not infer authorization from missing or stale data', () => {
  it('keeps unknown separate from failure', () => {
    expect(safetyLabel(null, now)).toContain('UNKNOWN');
    expect(safetyLabel(status(), now, true)).toContain('UNAVAILABLE');
  });
  it.each([null, 'invalid', '2026-10-27T11:59:00Z', '2026-10-27T12:00:05Z'])(
    'refuses to describe monitor %s as current',
    (monitor_at) => {
      expect(safetyLabel(status({ monitor_at }), now)).toContain('STALE');
    },
  );
  it('never hides a persistent stop behind a stale label', () => {
    expect(safetyLabel(status({ manual_stop: true, monitor_at: null }), now)).toContain(
      'Intrări simulate oprite',
    );
    expect(safetyLabel(status({ automatic_stop: true }), now)).toContain('Intrări simulate oprite');
  });
  it('a fresh observed state still requires per-order risk checks', () => {
    expect(safetyLabel(status(), now)).toContain('Verificare obligatorie la fiecare ordin simulat');
  });
});
