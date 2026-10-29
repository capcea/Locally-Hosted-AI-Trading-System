import { describe, expect, it } from 'vitest';
import type { components } from './generated/api';
import { safetyLabel, safetyOverview } from './RiskBanner';

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

describe('plain-language account coverage preserves uncertainty', () => {
  it('does not present a failed empty read as no configured accounts', () => {
    expect(safetyOverview({ failed: true, checked: now, count: 0, issues: 0 })).toContain(
      'UNAVAILABLE',
    );
  });
  it('does not report zero accounts before the first completed read', () => {
    expect(safetyOverview({ failed: false, checked: null, count: 0, issues: 0 })).toContain(
      'UNKNOWN',
    );
  });
  it('describes an empty completed read without claiming safety', () => {
    expect(safetyOverview({ failed: false, checked: now, count: 0, issues: 0 })).toBe(
      'Niciun cont în lista citită',
    );
  });
  it('keeps mandatory per-order checks visible even with no current issues', () => {
    expect(safetyOverview({ failed: false, checked: now, count: 1, issues: 0 })).toBe(
      '1 cont citit · verificare la fiecare ordin simulat',
    );
  });
  it('retains both the attention count and the read scope', () => {
    expect(safetyOverview({ failed: false, checked: now, count: 3, issues: 1 })).toBe(
      'Un cont necesită verificare · 3 conturi citite',
    );
  });
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
