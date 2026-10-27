import { afterEach, expect, it, vi } from 'vitest';
import { allRecords } from './records';
afterEach(() => vi.unstubAllGlobals());
const page = (items: unknown[], total: number) =>
  new Response(JSON.stringify({ items, total }), {
    headers: { 'Content-Type': 'application/json' },
  });
it('reads every declared account page instead of assuming the first 100 is complete', async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(
      page(
        Array.from({ length: 100 }, (_, i) => ({ id: String(i) })),
        101,
      ),
    )
    .mockResolvedValueOnce(page([{ id: 'last' }], 101));
  vi.stubGlobal('fetch', fetch);
  const records = await allRecords('accounts');
  expect(records).toHaveLength(101);
  expect(records.at(-1)?.id).toBe('last');
  expect(fetch.mock.calls[1][0]).toContain('offset=100');
});
it('does not certify an incomplete or changing catalog', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(page([{ id: 'first' }], 101))
      .mockResolvedValueOnce(page([], 101)),
  );
  await expect(allRecords('accounts')).rejects.toThrow('nu a putut fi citit complet');
});
it('refuses mixed pagination snapshots and duplicate account coverage', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(page([{ id: 'first' }], 101))
      .mockResolvedValueOnce(page([{ id: 'first' }], 101)),
  );
  await expect(allRecords('accounts')).rejects.toThrow('nu a putut fi citit complet');
});
