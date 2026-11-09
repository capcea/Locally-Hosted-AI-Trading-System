import { afterEach, expect, it, vi } from 'vitest';
import { readWithDeadline } from './read-deadline';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
function stalledFetch() {
  return vi.fn(
    (_path: string, options: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        const abort = () => reject(new DOMException('Read cancelled', 'AbortError'));
        if (options.signal?.aborted) abort();
        else options.signal?.addEventListener('abort', abort, { once: true });
      }),
  );
}
it('bounds an unresponsive read and allows a subsequent real read without replaying requests', async () => {
  vi.useFakeTimers();
  const fetch = stalledFetch();
  vi.stubGlobal('fetch', fetch);
  const outcome = readWithDeadline('/workspace/library', new AbortController().signal).catch(
    (error) => error,
  );
  await vi.advanceTimersByTimeAsync(15000);
  expect(await outcome).toMatchObject({ name: 'AbortError' });
  expect(fetch).toHaveBeenCalledTimes(1);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"items":[]}', { status: 200 })));
  await expect(
    readWithDeadline('/workspace/library', new AbortController().signal),
  ).resolves.toEqual({ items: [] });
  expect(vi.getTimerCount()).toBe(0);
});
it('cancels an obsolete account/owner read immediately and clears its deadline', async () => {
  vi.useFakeTimers();
  const fetch = stalledFetch();
  vi.stubGlobal('fetch', fetch);
  const scope = new AbortController();
  const outcome = readWithDeadline('/risk/accounts/old/status', scope.signal).catch(
    (error) => error,
  );
  scope.abort();
  expect(await outcome).toMatchObject({ name: 'AbortError' });
  expect(vi.getTimerCount()).toBe(0);
});
it('honors a scope already cancelled before starting the read', async () => {
  vi.useFakeTimers();
  vi.stubGlobal('fetch', stalledFetch());
  const scope = new AbortController();
  scope.abort();
  await expect(readWithDeadline('/workspace/library', scope.signal)).rejects.toMatchObject({
    name: 'AbortError',
  });
  expect(vi.getTimerCount()).toBe(0);
});
