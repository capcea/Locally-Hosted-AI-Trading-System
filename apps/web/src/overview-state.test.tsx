import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { Overview, Service } from './api';
import { getOverview } from './api';
import { contractFixture } from './overview.fixture';
import { createOverviewReader, initialOverviewState, overviewIsStale } from './overview-state';
import type { OverviewState } from './overview-state';
import { infrastructureHealth } from './infrastructure-health';
import { SidebarStatus } from './v1/ShellTools';

const start = Date.parse('2026-10-29T08:00:00Z');
function snapshot(at = start): Overview {
  return {
    ...contractFixture(),
    timestamp: new Date(at).toISOString(),
    services: ['storage', 'api', 'ollama', 'redis', 'postgres'].map((id) => ({
      id,
      name: id,
      status: id === 'ollama' ? 'NOT_CONFIGURED' : 'HEALTHY',
      detail: 'SYNTHETIC_TEST_FIXTURE',
      latency_ms: null,
    })),
  };
}
function observation(statuses: Service['status'][]) {
  const data = snapshot();
  data.services = data.services
    .filter((service) => service.id !== 'ollama')
    .map((service, i) => ({ ...service, status: statuses[i] }));
  return data;
}
function harness(load: typeof getOverview = getOverview) {
  let now = start;
  let state = initialOverviewState(now);
  const reader = createOverviewReader(
    (next) => (state = next),
    load,
    () => now,
  );
  return {
    reader,
    state: () => state,
    advance: (ms: number) => {
      now += ms;
      reader.tick();
    },
  };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((ok, no) => {
    resolve = ok;
    reject = no;
  });
  return { promise, resolve, reject };
}
const html = (state: OverviewState) =>
  renderToStaticMarkup(
    <SidebarStatus
      overview={state.overview}
      stale={overviewIsStale(state)}
      now={state.now}
      error={state.error}
      loading={state.loading}
      refresh={() => undefined}
    />,
  );

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('four infrastructure observations, independent of AI/broker/execution status', () => {
  it('maps shuffled actual stable IDs and retains the V1 display', () => {
    const result = infrastructureHealth(snapshot(), false, start + 100);
    expect(result.status).toBe('HEALTHY');
    expect(result.rows.map((r) => [r.id, r.status])).toEqual(
      ['api', 'postgres', 'redis', 'storage'].map((id) => [id, 'HEALTHY']),
    );
    const markup = renderToStaticMarkup(
      <SidebarStatus overview={snapshot()} stale={false} now={start + 100} />,
    );
    expect(markup.match(/>Disponibil<\/strong>/g)).toHaveLength(4);
    expect(markup).toContain('nu autorizează tranzacții');
    expect(markup).not.toContain('ollama');
  });
  it.each([
    ['HEALTHY', ['HEALTHY', 'HEALTHY', 'HEALTHY', 'HEALTHY']],
    ['DEGRADED', ['HEALTHY', 'UNAVAILABLE', 'HEALTHY', 'HEALTHY']],
    ['DOWN', ['UNAVAILABLE', 'UNAVAILABLE', 'UNAVAILABLE', 'UNAVAILABLE']],
    ['UNKNOWN', ['HEALTHY', 'HEALTHY', 'NOT_CONFIGURED', 'HEALTHY']],
  ] as const)(
    'represents aggregate %s from explicit per-service observations',
    (status, values) => {
      expect(infrastructureHealth(observation([...values]), false, start).status).toBe(status);
    },
  );
  it('does not turn incomplete or ambiguous service coverage into HEALTHY', () => {
    const data = snapshot();
    data.services = data.services.filter((s) => s.id !== 'postgres');
    expect(infrastructureHealth(data, false, start).rows[1]).toMatchObject({
      id: 'postgres',
      status: 'UNKNOWN',
      text: 'UNKNOWN',
    });
    data.services.push(snapshot().services.find((s) => s.id === 'api')!);
    expect(infrastructureHealth(data, false, start).rows[0].status).toBe('UNKNOWN');
  });
  it.each([start + 45_001, start - 1, NaN])(
    'does not trust stale/future/invalid observation clocks at %s',
    (now) => {
      expect(
        infrastructureHealth(snapshot(), false, now).rows.every((r) => r.text === 'UNKNOWN'),
      ).toBe(true);
    },
  );
  it('never trusts an invalid timestamp even when passed a false stale flag', () => {
    const data = { ...snapshot(), timestamp: 'invalid' };
    expect(infrastructureHealth(data, false, start).status).toBe('UNKNOWN');
  });
});

describe('overview reader used by the shell', () => {
  it('remains fresh after nonzero request latency and across repeated poll completions', async () => {
    const first = deferred<Overview>();
    const next = deferred<Overview>();
    const load = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(next.promise);
    const h = harness(load);
    const read = h.reader.refresh();
    h.advance(100);
    first.resolve(snapshot());
    await read;
    expect(h.state().receivedAt).toBe(h.state().now);
    expect(overviewIsStale(h.state())).toBe(false);
    expect(html(h.state()).match(/>Disponibil<\/strong>/g)).toHaveLength(4);
    h.advance(15_000);
    const second = h.reader.refresh();
    h.advance(100);
    next.resolve(snapshot(start + 15_000));
    await second;
    expect(overviewIsStale(h.state())).toBe(false);
    h.advance(45_001);
    expect(html(h.state())).not.toContain('>Disponibil</strong>');
    expect(html(h.state())).toContain('Verifică din nou');
    h.reader.stop();
  });
  it('does not renew backend observation age when stale HTTP200 is received now', async () => {
    const h = harness(async () => snapshot(start - 45_001));
    await h.reader.refresh();
    expect(h.state().receivedAt).toBe(start);
    expect(overviewIsStale(h.state())).toBe(true);
    expect(html(h.state())).not.toContain('>Disponibil</strong>');
    h.reader.stop();
  });
  it.each([503, 200])(
    'recovers after an unavailable or malformed HTTP%s without cached success',
    async (status) => {
      const fetcher = vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(snapshot())))
        .mockResolvedValueOnce(new Response(JSON.stringify({ services: [] }), { status }))
        .mockResolvedValueOnce(new Response(JSON.stringify(snapshot())));
      vi.stubGlobal('fetch', fetcher);
      const h = harness();
      await h.reader.refresh();
      expect(overviewIsStale(h.state())).toBe(false);
      await h.reader.refresh();
      expect(h.state().error).toBe(true);
      expect(html(h.state())).toContain('date indisponibile sau invalide');
      expect(html(h.state())).not.toContain('>Disponibil</strong>');
      await h.reader.refresh();
      expect(h.state().error).toBe(false);
      expect(overviewIsStale(h.state())).toBe(false);
      expect(fetcher).toHaveBeenCalledWith(
        '/api/v1/overview',
        expect.objectContaining({ cache: 'no-store' }),
      );
      h.reader.stop();
    },
  );
  it.each(['success', 'error'])(
    'ignores an out-of-order %s after a newer request completes',
    async (outcome) => {
      const old = deferred<Overview>();
      const load = vi
        .fn()
        .mockReturnValueOnce(old.promise)
        .mockResolvedValueOnce(snapshot(start + 1));
      const h = harness(load);
      const first = h.reader.refresh();
      h.advance(1);
      await h.reader.refresh();
      const accepted = h.state();
      if (outcome === 'success')
        old.resolve(observation(['UNAVAILABLE', 'UNAVAILABLE', 'UNAVAILABLE', 'UNAVAILABLE']));
      else old.reject(new Error('old request failed'));
      await first;
      expect(h.state()).toBe(accepted);
      expect(overviewIsStale(h.state())).toBe(false);
      h.reader.stop();
    },
  );
  it('rejects a regressed server timestamp and recovers from an offline transport', async () => {
    const load = vi
      .fn()
      .mockResolvedValueOnce(snapshot())
      .mockResolvedValueOnce(snapshot(start - 1))
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockResolvedValueOnce(snapshot(start + 1));
    const h = harness(load);
    await h.reader.refresh();
    await h.reader.refresh();
    expect(h.state().overview?.timestamp).toBe(snapshot().timestamp);
    expect(overviewIsStale(h.state())).toBe(true);
    await h.reader.refresh();
    expect(h.state().error).toBe(true);
    h.advance(1);
    await h.reader.refresh();
    expect(overviewIsStale(h.state())).toBe(false);
    h.reader.stop();
  });
  it('cannot publish a late completion after timeout or unmount', async () => {
    vi.useFakeTimers();
    const late = deferred<Overview>();
    const h = harness(() => late.promise);
    const first = h.reader.refresh();
    await vi.advanceTimersByTimeAsync(10_000);
    late.resolve(snapshot());
    await first;
    expect(h.state().error).toBe(true);
    const unmounted = deferred<Overview>();
    const stopped = harness(() => unmounted.promise);
    const second = stopped.reader.refresh();
    const before = stopped.state();
    stopped.reader.stop();
    unmounted.resolve(snapshot());
    await second;
    expect(stopped.state()).toBe(before);
    h.reader.stop();
  });
});
