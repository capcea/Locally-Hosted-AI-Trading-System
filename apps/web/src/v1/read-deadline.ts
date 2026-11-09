import { api } from '../management-api';

/** Bounded, cancellable reads only. A timed-out mutation must never be retried by this helper. */
export async function readWithDeadline<T>(path: string, scope: AbortSignal): Promise<T> {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  scope.addEventListener('abort', cancel, { once: true });
  if (scope.aborted) cancel();
  const timer = setTimeout(cancel, 15000);
  try {
    return await api<T>(path, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
    scope.removeEventListener('abort', cancel);
  }
}
