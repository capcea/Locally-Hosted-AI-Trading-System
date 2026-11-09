import { afterEach, expect, it, vi } from 'vitest';
import * as reads from '../v1/data';
afterEach(() => vi.restoreAllMocks());
import { renderToStaticMarkup } from 'react-dom/server';
import { AuthProvider } from '../auth/AuthProvider';
import { primary, primaryArea, resolveRoute } from '../navigation/routes';
import { LabOverview, TradingDashboard, ValidatedLibrary } from './Workspace';
import type { Session } from '../management-api';

it('has exactly three primary destinations and preserves legacy deep-link ownership context', () => {
  expect(primary.map((item) => item.label)).toEqual([
    'Trading Dashboard',
    'Strategy Lab',
    'Settings',
  ]);
  expect(resolveRoute('/strategy-lab').screen).toBe('lab');
  expect(resolveRoute('/strategy-lab/biblioteca').screen).toBe('library');
  expect(resolveRoute('/strategy-lab/testeaza').canonicalPath).toBe('/testeaza/nou');
  expect(primaryArea(resolveRoute('/rezultate'))).toBe('research');
  expect(primaryArea(resolveRoute('/conturi/siguranta'))).toBe('settings');
});
it('keeps the entire existing flow reachable from a focused Strategy Lab', () => {
  const html = renderToStaticMarkup(
    <AuthProvider>
      <LabOverview />
    </AuthProvider>,
  );
  for (const path of [
    '/strategy-lab/idei',
    '/strategy-lab/testeaza',
    '/strategy-lab/biblioteca',
    '/testeaza/date/import',
    '/testeaza/campanii',
    '/testeaza/evaluare-finala',
  ]) {
    expect(html).toContain(`href="${path}"`);
    expect(resolveRoute(path).screen).not.toBe('not-found');
  }
  expect(html).toContain(
    'Antrenarea și validarea unui model specializat nu sunt încă implementate',
  );
  expect(html).not.toContain('profit garantat');
});
it('shows honest account/PnL/activity states without invented trading or model specialization', () => {
  const session = {
    user: { id: 'fixture-owner', role: 'OWNER' },
    state: 'FULL',
    auth_mode: 'PASSWORD',
    csrf_token: '',
  } as Session;
  const html = renderToStaticMarkup(
    <AuthProvider>
      <TradingDashboard
        session={session}
        accounts={[]}
        accountId=""
        accountsReady
        accountsFailed={false}
        choose={() => undefined}
      />
    </AuthProvider>,
  );
  expect(html).toContain('Adaugă primul cont');
  expect(html).toContain('PnL realizat');
  expect(html).toContain('Date curente neconfirmate');
  expect(html).toContain('traderul continuu conectat la broker nu este implementat');
  expect(html).toContain('SIMULATED / DENY_ALL');
  expect(html).toContain('disabled=""');
  expect(html).not.toContain('<iframe');
});
it('does not turn synthetic fixtures or a missing library into execution eligibility', () => {
  const html = renderToStaticMarkup(
    <AuthProvider>
      <ValidatedLibrary />
    </AuthProvider>,
  );
  expect(html).toContain('Randamentul pozitiv singur nu este suficient');
  expect(html).not.toContain('Pornește trading real');
});

it('keeps the Lab and account safety reachable when a persisted experiment has no job record', () => {
  const uncertain = [
    { id: 'incomplete-run', name: 'Test fără job', strategy: 'EMA_TREND', job: null },
  ];
  vi.spyOn(reads, 'useOwnedRead').mockImplementation(<T,>(path: string | null) => ({
    data: (path?.startsWith('/research/experiments') ? uncertain : null) as T | null,
    lastKnown: null,
    failed: false,
    loading: false,
  }));
  const lab = renderToStaticMarkup(
    <AuthProvider>
      <LabOverview />
    </AuthProvider>,
  );
  expect(lab).toContain('Test fără job');
  expect(lab).toContain('Rezultat necunoscut');
  const session = {
    user: { id: 'fixture-owner', role: 'OWNER' },
    state: 'FULL',
    auth_mode: 'PASSWORD',
    csrf_token: '',
  } as Session;
  const dashboard = renderToStaticMarkup(
    <AuthProvider>
      <TradingDashboard
        session={session}
        accounts={[]}
        accountId=""
        accountsReady
        accountsFailed={false}
        choose={() => undefined}
      />
    </AuthProvider>,
  );
  expect(dashboard).toContain('Unele teste nu au o stare de procesare confirmată');
  expect(dashboard).toContain('SIMULATED / DENY_ALL');
});

it('makes later account candidate pages reachable instead of limiting selection to the first fifty', () => {
  vi.spyOn(reads, 'useOwnedRead').mockImplementation(<T,>(path: string | null) => ({
    data: (path?.startsWith('/workspace/library')
      ? { items: [], has_more: true, unavailable_count: 50 }
      : null) as T | null,
    lastKnown: null,
    failed: false,
    loading: false,
  }));
  const session = {
    user: { id: 'fixture-owner', role: 'OWNER' },
    state: 'FULL',
    auth_mode: 'PASSWORD',
    csrf_token: '',
  } as Session;
  const html = renderToStaticMarkup(
    <AuthProvider>
      <TradingDashboard
        session={session}
        accounts={[]}
        accountId="account-fixture"
        accountsReady
        accountsFailed={false}
        choose={() => undefined}
      />
    </AuthProvider>,
  );
  expect(html).toContain('Paginile strategiilor contului');
  expect(html).toContain('Strategii următoare');
  expect(html).toContain('Unele dovezi nu pot fi revalidate');
  expect(reads.useOwnedRead).toHaveBeenCalledWith(
    '/workspace/library?limit=50&offset=0&account_id=account-fixture',
    15000,
  );
});

it('treats missing jobs as UNKNOWN in history filters and results summaries', async () => {
  const { ExperimentStats, ResultsOverview } = await import('../v1/ResearchViews');
  const missing = {
    id: 'missing-job',
    name: 'Job neconfirmat',
    strategy: 'EMA_TREND',
    phase: 'DISCOVERY',
    engine: 'EVENT',
    job: null,
    result: null,
  } as reads.ResearchJob;
  expect(reads.filterExperiments([missing], '', 'UNKNOWN', '')).toEqual([missing]);
  expect(reads.filterExperiments([missing], '', 'SUCCEEDED', '')).toEqual([]);
  expect(() => renderToStaticMarkup(<ExperimentStats jobs={[missing]} available />)).not.toThrow();
  const html = renderToStaticMarkup(<ResultsOverview jobs={[missing]} failed={false} />);
  expect(html).toContain('Niciun rezultat finalizat');
  expect(html).not.toContain('<svg role="img"');
});

it('opens Strategy Lab directly on the real AI composer while keeping technical tools advanced', () => {
  vi.stubGlobal('window', { location: { pathname: '/strategy-lab' } });
  try {
    const session = {
      user: { id: 'fixture-owner', role: 'OWNER' },
      state: 'FULL',
      auth_mode: 'PASSWORD',
      csrf_token: '',
    } as Session;
    const html = renderToStaticMarkup(
      <AuthProvider>
        <LabOverview session={session} />
      </AuthProvider>,
    );
    expect(html).toContain('Asistent AI Strategy Lab');
    expect(html).toContain('Ce strategie vrei să cercetăm?');
    expect(html).toContain('Întrebarea ta');
    expect(html).toContain('Configurare manuală și instrumente avansate');
    expect(html).toContain('Niciun model confirmat disponibil');
    expect(html).not.toContain('AI online');
  } finally {
    vi.unstubAllGlobals();
  }
});
