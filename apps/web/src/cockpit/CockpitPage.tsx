import './cockpit-shell.css';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { components } from '../generated/api';
import type { Overview } from '../api';
import { readinessSummary } from '../api';
import { api } from '../management-api';
import { allRecords } from '../records';
import { useAuth } from '../auth/AuthProvider';
import { navigate } from '../navigation/history';
import type { JobSummary } from '../home/HomePage';
import { safetyLabel } from '../RiskBanner';

type AccountStatus = components['schemas']['AccountStatus'];
type RiskState = 'UNKNOWN' | 'CHECKING' | 'ATTENTION' | 'VERIFIED';
type JobView = {
  id: string;
  name: string;
  phase: string;
  state: string;
  progress: number;
  createdAt: string | null;
};
type Snapshot = {
  type: 'local-ai:snapshot';
  jobsVerified: boolean;
  jobs: JobView[];
  partial: boolean;
  overviewVerified: boolean;
  serviceHealth: string;
  riskState: RiskState;
  userName: string;
};
const destinations = new Set([
  '/', '/testeaza', '/testeaza/nou', '/testeaza/activitate',
  '/rezultate', '/conturi/siguranta', '/setari',
]);

export default function CockpitPage({
  overview,
  stale,
}: {
  overview: Overview | null;
  stale: boolean;
}) {
  const { session } = useAuth();
  const frame = useRef<HTMLIFrameElement>(null);
  const [frameReady, setFrameReady] = useState(false);
  const [jobs, setJobs] = useState<JobView[]>([]);
  const [jobsVerified, setJobsVerified] = useState(false);
  const [riskState, setRiskState] = useState<RiskState>('CHECKING');

  useEffect(() => {
    if (session?.state !== 'FULL') return;
    let mounted = true;
    let running = false;
    const update = async () => {
      if (running) return;
      running = true;
      try {
        // These are actual saved research jobs, not inferred AI decisions or profits.
        const fetched = await api<JobSummary[]>('/research/experiments?limit=100');
        if (mounted) {
          setJobs(fetched.map((job) => ({
            id: job.id,
            name: job.name,
            phase: job.phase,
            state: job.job.state,
            progress: job.job.progress,
            createdAt: job.created_at ?? null,
          })));
          setJobsVerified(true);
        }
      } catch {
        if (mounted) {
          setJobsVerified(false);
          setJobs([]);
        }
      }
      try {
        const accounts = await allRecords('accounts');
        const statuses = await Promise.all(accounts.map((account) =>
          api<AccountStatus>(`/risk/accounts/${account.id}/status`),
        ));
        if (mounted) {
          const now = Date.now();
          setRiskState(
            statuses.length === 0
              ? 'UNKNOWN'
              : statuses.every((status) =>
                  safetyLabel(status, now) === 'Verificare obligatorie la fiecare ordin simulat',
                )
                ? 'VERIFIED'
                : 'ATTENTION',
          );
        }
      } catch {
        if (mounted) setRiskState('UNKNOWN');
      } finally {
        running = false;
      }
    };
    void update();
    const interval = window.setInterval(() => void update(), 10000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [session?.state, session?.user.id]);

  const readiness = overview ? readinessSummary(overview.services) : null;
  const serviceHealth =
    stale || !readiness || readiness.total === 0
      ? 'UNKNOWN'
      : readiness.healthy === readiness.total
        ? 'HEALTHY'
        : 'ATTENTION';

  const snapshot = useMemo<Snapshot>(() => ({
    type: 'local-ai:snapshot',
    jobsVerified,
    jobs,
    partial: jobs.length >= 100,
    overviewVerified: !stale && Boolean(overview),
    serviceHealth,
    riskState,
    userName: session?.state === 'FULL' ? session.user.display_name : '',
  }), [jobs, jobsVerified, overview, riskState, serviceHealth, session, stale]);

  const sendSnapshot = useCallback(() => {
    frame.current?.contentWindow?.postMessage(snapshot, '*');
  }, [snapshot]);

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.source !== frame.current?.contentWindow || !event.data || typeof event.data !== 'object')
        return;
      if (event.data.type === 'local-ai:ready') {
        setFrameReady(true);
        frame.current?.contentWindow?.postMessage(snapshot, '*');
      }
      if (event.data.type === 'local-ai:navigate' && typeof event.data.path === 'string') {
        const path = event.data.path;
        // Allow only known routes; result links require a UUID owned by the current user.
        if (destinations.has(path) ||
            /^\/rezultate\/[0-9a-f-]{36}$/i.test(path)) navigate(path);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [snapshot]);

  useEffect(() => {
    if (frameReady) sendSnapshot();
  }, [frameReady, sendSnapshot]);

  return (
    <iframe
      ref={frame}
      title="Local AI — AI Cockpit"
      src="/cockpit.html"
      sandbox="allow-scripts"
      onLoad={sendSnapshot}
      style={{
        width: '100%',
        height: '100dvh',
        border: 0,
        display: 'block',
        background: '#090d14',
      }}
    />
  );
}
