import { useCallback, useEffect, useRef, useState } from 'react';
import { createOverviewReader, initialOverviewState, overviewIsStale } from './overview-state';

export function useOverview() {
  const [state, setState] = useState(() => initialOverviewState(Date.now()));
  const reader = useRef<ReturnType<typeof createOverviewReader> | null>(null);
  useEffect(() => {
    const current = createOverviewReader(setState);
    reader.current = current;
    void current.refresh();
    const poll = setInterval(() => void current.refresh(), 15_000);
    const clock = setInterval(current.tick, 1000);
    return () => {
      clearInterval(poll);
      clearInterval(clock);
      current.stop();
      reader.current = null;
    };
  }, []);
  const refresh = useCallback(() => reader.current?.refresh(), []);
  return { ...state, stale: overviewIsStale(state), refresh };
}
