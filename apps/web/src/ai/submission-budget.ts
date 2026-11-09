import { ApiError } from '../management-api';
import { verified } from './api';
import type { Binding, Model } from './api';

export function verifiedContextWindow(
  models: Model[],
  binding: Binding | undefined,
  fallback: boolean,
  now = Date.now(),
): number | null {
  if (!binding) return null;
  const ids = [binding.model_id, ...(fallback ? binding.fallback_ids : [])];
  const limits: number[] = [];
  for (const id of ids) {
    const model = models.find((item) => item.id === id);
    const observed = model?.verification?.context_tokens;
    if (
      !model ||
      !verified(model, now) ||
      typeof observed !== 'number' ||
      !Number.isSafeInteger(observed) ||
      !Number.isSafeInteger(model.context_ceiling)
    )
      return null;
    limits.push(Math.min(observed, model.context_ceiling, 131072));
  }
  const limit = Math.min(...limits);
  return limit >= 1024 ? limit : null;
}
/** 422 is pre-enqueue validation; network/5xx/other uncertain outcomes keep the exact request. */
export function afterSubmissionFailure<T>(frozen: T, error: unknown): T | null {
  return error instanceof ApiError && error.status === 422 ? null : frozen;
}
