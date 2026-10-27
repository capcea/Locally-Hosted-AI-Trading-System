import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, parseSession } from './management-api';

afterEach(() => vi.unstubAllGlobals());
describe('identity client boundary', () => {
  it('rejects fabricated role and MFA session states', () => {
    const session = {
      user: {
        id: '11111111-1111-4111-8111-111111111111',
        username: 'fixture',
        display_name: 'Fixture',
        role: 'OWNER',
        active: true,
      },
      state: 'FULL',
      csrf_token: 'a'.repeat(64),
      expires_at: '2026-10-26T12:00:00Z',
      session_id: '22222222-2222-4222-8222-222222222222',
    };
    expect(parseSession(session).state).toBe('FULL');
    expect(() => parseSession({ ...session, state: 'LIVE_APPROVED' })).toThrow();
    expect(() => parseSession({ ...session, user: { ...session.user, role: 'ROOT' } })).toThrow();
  });
  it('uses same-origin cookies and explicitly sends CSRF on mutations', async () => {
    const request = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', request);
    await api('/auth/logout', { method: 'POST', body: {}, csrf: 'fixture-csrf' });
    expect(request).toHaveBeenCalledWith(
      '/api/v1/auth/logout',
      expect.objectContaining({
        credentials: 'same-origin',
        cache: 'no-store',
        headers: expect.objectContaining({ 'X-CSRF-Token': 'fixture-csrf' }),
      }),
    );
  });
  it('does not expose server error bodies that could contain sensitive details', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('sensitive fixture detail', { status: 503 })),
    );
    await expect(api('/auth/me')).rejects.toBeInstanceOf(ApiError);
    await expect(api('/auth/me')).rejects.not.toThrow('sensitive fixture detail');
  });
});
