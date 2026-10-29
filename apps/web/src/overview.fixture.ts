import type { Overview } from './api';

// Synthetic contract fixture for validation tests only; never a quote or broker response.
export function contractFixture(): Overview {
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
