import { z } from 'zod';
import type { Overview } from './api';

const amount = z
  .string()
  .max(32)
  .regex(/^\d+(\.\d+)?$/);
const text = z.string().max(2000);
export const overviewSchema = z.strictObject({
  application: z.literal('AI Trading Research Platform'),
  version: z.literal('0.1.0'),
  phase: z.union([
    z.literal(0),
    z.literal(1),
    z.literal(2),
    z.literal(3),
    z.literal(4),
    z.literal(5),
    z.literal(6),
  ]),
  timestamp: z.iso.datetime({ offset: true }),
  uptime_seconds: z.number().int().nonnegative(),
  trading_data_available: z.literal(false),
  performance_data_available: z.literal(false),
  safety: z.strictObject({
    mode: z.literal('SIMULATED'),
    live_trading_enabled: z.literal(false),
    order_submission_enabled: z.literal(false),
    executor_capability: z.literal('DENY_ALL'),
    generated_code_execution: z.literal(false),
    read_only: z.literal(true),
    reasons: z.array(text).min(1).max(30),
  }),
  services: z
    .array(
      z.strictObject({
        id: text,
        name: text,
        detail: text,
        status: z.enum([
          'HEALTHY',
          'UNAVAILABLE',
          'NOT_CONFIGURED',
          'DISABLED',
          'PENDING_IMPLEMENTATION',
        ]),
        latency_ms: z.number().int().nonnegative().nullable(),
      }),
    )
    .min(1)
    .max(40),
  reference_profile: z.strictObject({
    provenance: z.literal('CONFIGURATION_EXAMPLE'),
    currency: z.literal('USD'),
    equity: amount,
    risk_per_trade_pct: amount,
    daily_loss_pct: amount,
    total_drawdown_pct: amount,
    open_risk_pct: amount,
    enforced: z.literal(false),
  }),
  roadmap: z
    .array(
      z.strictObject({
        number: z.number().int().nonnegative(),
        title: text,
        status: z.enum(['CURRENT', 'PLANNED']),
        acceptance: text,
      }),
    )
    .min(1)
    .max(30),
}) satisfies z.ZodType<Overview>;

export function parseOverview(value: unknown): Overview {
  const parsed = overviewSchema.safeParse(value);
  if (!parsed.success)
    throw new Error('Contract API invalid; starea sistemului nu este verificată.');
  return parsed.data;
}
