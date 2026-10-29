import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, parseSession } from './management-api';

afterEach(() => vi.unstubAllGlobals());
describe('identity client boundary', () => {
  it('keeps a valid session after an invalid MFA code', async () => {
    const surface = new EventTarget();
    const expired = vi.fn();
    surface.addEventListener('research-session-expired', expired);
    vi.stubGlobal('window', surface);
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Invalid, expired or already used MFA code' }), {
          status: 401,
        }),
      ),
    );
    await expect(api('/auth/reauthenticate', { method: 'POST' })).rejects.toBeInstanceOf(ApiError);
    expect(expired).not.toHaveBeenCalled();
  });
  it('does not let an old session failure invalidate a completed login', async () => {
    const surface = new EventTarget();
    const expired = vi.fn();
    surface.addEventListener('research-session-expired', expired);
    vi.stubGlobal('window', surface);
    let finish!: (response: Response) => void;
    const oldResponse = new Promise<Response>((resolve) => {
      finish = resolve;
    });
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockImplementation((path: string) =>
          path.endsWith('/me') ? oldResponse : Promise.resolve(new Response('{}', { status: 200 })),
        ),
    );
    const old = api('/auth/me').catch(() => undefined);
    await api('/auth/login', { method: 'POST' });
    finish(new Response(JSON.stringify({ detail: 'Session expired or revoked' }), { status: 401 }));
    await old;
    expect(expired).not.toHaveBeenCalled();
  });
  it.each([
    [403, 'Recent MFA verification required', 'research-mfa-required', 'MFA_RECENT_REQUIRED'],
    [403, 'CSRF validation failed', 'research-session-refresh', 'CSRF_FAILED'],
    [401, 'Session expired or revoked', 'research-session-expired', 'SESSION_EXPIRED'],
  ])('classifies %s/%s without retrying an action', async (status, detail, event, code) => {
    const surface = new EventTarget();
    const notified = vi.fn();
    surface.addEventListener(String(event), notified);
    vi.stubGlobal('window', surface);
    const request = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail }), { status: Number(status) }));
    vi.stubGlobal('fetch', request);
    await expect(api('/ai/endpoints/openrouter', { method: 'POST' })).rejects.toMatchObject({
      code,
    });
    expect(notified).toHaveBeenCalledTimes(1);
    expect(request).toHaveBeenCalledTimes(1);
  });
  it('distinguishes invalid credentials from expiration and keeps permission refusal separate', async () => {
    const surface = new EventTarget();
    const event = vi.fn();
    surface.addEventListener('research-session-expired', event);
    surface.addEventListener('research-mfa-required', event);
    vi.stubGlobal('window', surface);
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: 'Invalid credentials' }), { status: 401 }),
        ),
    );
    await expect(api('/auth/login', { method: 'POST' })).rejects.toMatchObject({
      code: 'LOGIN_INVALID',
    });
    await expect(api('/auth/login', { method: 'POST' })).rejects.not.toThrow('expirat');
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: 'Owner role required' }), { status: 403 }),
        ),
    );
    await expect(api('/ai/endpoints/openrouter', { method: 'POST' })).rejects.toMatchObject({
      code: 'ROLE_REQUIRED',
    });
    expect(event).not.toHaveBeenCalled();
  });
  it('does not publish old successful session data after a newer authorization response', async () => {
    let finish!: (response: Response) => void;
    const earlier = new Promise<Response>((resolve) => {
      finish = resolve;
    });
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockImplementation((path: string) =>
          path.endsWith('/me') ? earlier : Promise.resolve(new Response('{}', { status: 200 })),
        ),
    );
    const old = api('/auth/me').catch((error: unknown) => error);
    await api('/auth/reauthenticate', { method: 'POST' });
    finish(
      new Response(JSON.stringify({ state: 'FULL', session_id: 'obsolete' }), { status: 200 }),
    );
    expect(await old).toMatchObject({ code: 'AUTH_STATE_CHANGED', status: 409 });
  });
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
  it('does not echo an arbitrary uppercase error body as a trusted research code', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: 'PRIVATE_UPPERCASE_VALUE' }), { status: 409 }),
        ),
    );
    await expect(api('/research/experiments')).rejects.not.toThrow('PRIVATE_UPPERCASE_VALUE');
  });
  it('does not prescribe a fabricated retry timer or retry an uncertain write automatically', async () => {
    const request = vi.fn().mockResolvedValue(new Response(null, { status: 429 }));
    vi.stubGlobal('fetch', request);
    await expect(api('/auth/login')).rejects.not.toThrow('15 minute');
    expect(request).toHaveBeenCalledTimes(1);
  });
});
