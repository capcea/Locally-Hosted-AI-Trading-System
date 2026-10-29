import { getOverview, isOverviewStale } from './api';
import type { Overview } from './api';

export type OverviewState = {
  overview: Overview | null;
  error: boolean;
  loading: boolean;
  receivedAt: number | null;
  now: number;
};
export const initialOverviewState = (now: number): OverviewState => ({
  overview: null,
  error: false,
  loading: false,
  receivedAt: null,
  now,
});
export const overviewIsStale = (state: OverviewState) =>
  state.error || isOverviewStale(state.overview, state.receivedAt, state.now);

// One reader per mounted shell. Request identity fences even transports that ignore abort.
export function createOverviewReader(
  changed: (state: OverviewState) => void,
  load: typeof getOverview = getOverview,
  clock: () => number = Date.now,
) {
  let state = initialOverviewState(clock());
  let active = true;
  let pending: { controller: AbortController; timeout: ReturnType<typeof setTimeout> } | null =
    null;
  const publish = (patch: Partial<OverviewState>) => {
    state = { ...state, ...patch };
    if (active) changed(state);
  };
  const abort = () => {
    if (pending) {
      clearTimeout(pending.timeout);
      pending.controller.abort();
      pending = null;
    }
  };
  return {
    tick: () => publish({ now: clock() }),
    async refresh() {
      if (!active) return;
      abort();
      const controller = new AbortController();
      const request = { controller, timeout: setTimeout(() => controller.abort(), 10_000) };
      pending = request;
      publish({ loading: true, now: clock() });
      try {
        const overview = await load(controller.signal);
        if (!active || pending !== request) return;
        if (
          controller.signal.aborted ||
          (state.overview && Date.parse(overview.timestamp) < Date.parse(state.overview.timestamp))
        )
          throw new Error('Unverifiable overview observation');
        const receivedAt = clock();
        // Same instant: comparing a pre-request clock with this completion caused perpetual UNKNOWN.
        publish({ overview, receivedAt, now: receivedAt, error: false, loading: false });
      } catch {
        if (active && pending === request) publish({ error: true, loading: false, now: clock() });
      } finally {
        clearTimeout(request.timeout);
        if (pending === request) pending = null;
      }
    },
    stop() {
      active = false;
      abort();
    },
  };
}
