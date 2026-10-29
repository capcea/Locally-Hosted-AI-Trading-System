import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { AuthProvider } from '../auth/AuthProvider';
import type { RecordItem, Session } from '../management-api';
import { resolveRoute } from '../navigation/routes';
import { activeSection } from '../navigation/sections';
import HomePage from '../home/HomePage';
import AICenter from '../ai/AICenter';
import { offerAIQuestion, takeAIQuestion, clearAIQuestion } from '../ai/draft';
import { AIRoles } from './AIWidgets';
import { AccountsOverview } from './AccountsOverview';
import { BacktestReview, ResultsOverview, StrategyLibrary } from './ResearchViews';
import { filterExperiments, strategyFamily } from './data';
import type { ResearchJob, ReviewedStrategy } from './data';
import { ResultTiles } from './ExperimentPreview';
import { SidebarStatus, searchPages } from './ShellTools';
import { pageTitles } from './navigation';

const session = { user: { id: 'owner-fixture', role: 'OWNER' }, csrf_token: '' } as Session;
const strategy: ReviewedStrategy = {
  id: 'EMA_TREND',
  version: 'fixture-1',
  digest: 'fixture',
  entry: 'SYNTHETIC_TEST_FIXTURE',
  exit: 'fixture',
  assumptions: 'fixture only',
  parameters: {},
};
describe('approved V1 routes and independent safety', () => {
  it.each([
    ['/', 'Acasă'],
    ['/testeaza/strategii', 'Strategii'],
    ['/testeaza/nou', 'Backtesting'],
    ['/testeaza/activitate', 'Experimente'],
    ['/testeaza/ai', 'AI Center'],
    ['/rezultate', 'Rezultate'],
    ['/conturi', 'Conturi și siguranță'],
    ['/setari/ai', 'Setări · Modele AI'],
    ['/setari', 'Setări · Platformă'],
  ])('keeps the approved composition reachable at %s', (path, title) => {
    expect(resolveRoute(path).screen).not.toBe('not-found');
    expect(pageTitles(resolveRoute(path))).toBe(title);
  });
  it.each([
    ['/testeaza/backtesting', 'nou'],
    ['/testeaza/experimente', 'activitate'],
    ['/setari/platforma', ''],
    ['/setari/modele-ai', 'ai'],
  ])('maps finite alias %s without losing the actual path', (path, section) => {
    expect(resolveRoute(path).section ?? '').toBe(section);
    expect(resolveRoute(path).path).toBe(path);
    expect(activeSection(resolveRoute(path))).toBe(
      activeSection(resolveRoute(resolveRoute(path).canonicalPath!)),
    );
  });
  it('never presents missing public health as operational or grants trading authority', () => {
    const html = renderToStaticMarkup(<SidebarStatus overview={null} stale />);
    expect(html).toContain('UNKNOWN');
    expect(html).not.toContain('Disponibil</strong>');
    expect(html).toContain('nu autorizează');
  });
  it('indexes actual finite destinations rather than promising private full-text search', () => {
    for (const p of searchPages) expect(resolveRoute(p.href).screen).not.toBe('not-found');
    expect(searchPages.some((p) => p.href === '/setari/securitate')).toBe(true);
  });
});
describe('real data or explicit empty compositions', () => {
  it('retains all Home cards without fictional screenshot metrics', () => {
    const html = renderToStaticMarkup(
      <AuthProvider>
        <HomePage overview={null} stale refresh={() => undefined} />
      </AuthProvider>,
    );
    for (const title of [
      'Experimente citite',
      'Strategii de bază',
      'Teste finalizate',
      'Performanța experimentului selectat',
      'Asistent AI',
      'Experimente recente',
      'Siguranță și limite',
      'Următoarele acțiuni',
      'Fluxul de cercetare',
    ])
      expect(html).toContain(title);
    expect(html).toContain('Nu afișăm rezultate sau solduri presupuse.');
    expect(html).not.toContain('56,2%');
    expect(html).not.toContain('Ollama online');
    expect(html).toContain('disabled=""');
  });
  it('shows only API-returned library definitions, actual categories and exact version evidence', () => {
    const html = renderToStaticMarkup(
      <StrategyLibrary strategies={[strategy]} loaded blocked={false} choose={() => undefined} />,
    );
    expect(html).toContain('fixture-1');
    expect(html).toContain('EMA_TREND');
    expect(html).toContain('Trend (1)');
    expect(html).not.toContain('Strategii active');
    expect(strategyFamily('RSI')).toBe('Mean Reversion');
  });
  it('explains missing prerequisites and preserves safe configuration links', () => {
    const html = renderToStaticMarkup(
      <BacktestReview
        items={[
          {
            title: 'Politică verificată',
            ready: false,
            detail: 'Nu este disponibilă',
            href: '/conturi/siguranta',
            action: 'Revizuiește siguranța',
          },
        ]}
      />,
    );
    expect(html).toContain('Necesită verificare');
    expect(html).toContain('/conturi/siguranta');
    expect(html).not.toContain('<svg role="img"');
  });
  it('filters history by all criteria together and never changes cancellation acknowledgement', () => {
    const jobs = [
      {
        id: 'a',
        name: 'Cercetare A',
        strategy: 'EMA_TREND',
        phase: 'VALIDATION',
        job: { state: 'RUNNING', cancel_requested: true },
      },
      { id: 'b', name: 'Test B', strategy: 'RSI', phase: 'DISCOVERY', job: { state: 'SUCCEEDED' } },
    ] as ResearchJob[];
    expect(filterExperiments(jobs, ' EMA_ ', 'RUNNING', 'VALIDATION')).toEqual([jobs[0]]);
    expect(filterExperiments(jobs, '', 'CANCELLED', '')).toEqual([]);
    expect(jobs[0].job.state).toBe('RUNNING');
  });
  it('results without a stored experiment have no fabricated metric or graph', () => {
    const html = renderToStaticMarkup(<ResultsOverview jobs={[]} failed={false} />);
    expect(html).toContain('Niciun rezultat finalizat');
    expect(html).not.toContain('<svg role="img"');
  });
  it('only displays stored metrics from one selected trial and never manufactures missing ratios', () => {
    const html = renderToStaticMarkup(
      <ResultTiles
        result={{
          trials: [
            {
              metrics: {
                net_profit: '-42.12345678',
                max_drawdown: '80',
                profit_factor: null,
                win_rate: null,
              },
            },
          ],
        }}
        currency="USD"
      />,
    );
    expect(html).toContain('-42.12345678');
    expect(html).toContain('Indisponibil');
    expect(html).not.toContain('0%');
  });
  it('separates declared account metadata from applied limits and broker balances', () => {
    const account = {
      id: 'fixture',
      data: {
        kind: 'accounts',
        name: 'Synthetic account',
        initial_capital: '123.45678',
        currency: 'USD',
        source: 'SYNTHETIC_TEST_FIXTURE',
      },
    } as RecordItem;
    const html = renderToStaticMarkup(
      <AccountsOverview
        accounts={[account]}
        ready
        failed={false}
        selected="fixture"
        choose={() => undefined}
      />,
    );
    expect(html).toContain('123.45678');
    expect(html).toContain('Nu confirmă un sold de broker');
    expect(html).toContain('/conturi/fixture/siguranta');
  });
  it('leaves all four AI roles explicitly unverified with no models', () => {
    const html = renderToStaticMarkup(<AIRoles models={[]} bindings={[]} status={null} />);
    expect(html.match(/Niciun model atribuit/g)).toHaveLength(4);
    expect(html).not.toContain('Online');
    expect(html).toContain('UNKNOWN');
  });
  it.each([false, true])(
    'retains actual AI forms and no fabricated activity, advanced=%s',
    (advanced) => {
      vi.stubGlobal('window', { location: { pathname: advanced ? '/setari/ai' : '/testeaza/ai' } });
      try {
        const html = renderToStaticMarkup(<AICenter session={session} advanced={advanced} />);
        expect(html).toContain('SIMULATED / DENY_ALL');
        expect(html).toContain('Niciun agent nu lucrează automat');
        expect(html).toContain(advanced ? 'Registru AI' : 'Tipul analizei');
        if (advanced) expect(html).toContain('Înregistrează modelul neverificat');
      } finally {
        vi.unstubAllGlobals();
      }
    },
  );
});
describe('question handoff is memory-only, owner-bound and one-use', () => {
  it('requires a fresh explicit submission in AI Center', () => {
    offerAIQuestion('owner', '  Test question  ');
    expect(takeAIQuestion('owner')).toBe('Test question');
    expect(takeAIQuestion('owner')).toBe('');
  });
  it('cannot leak a question to another identity or survive logout clearing', () => {
    offerAIQuestion('a', 'private');
    expect(takeAIQuestion('b')).toBe('');
    offerAIQuestion('a', 'private');
    clearAIQuestion();
    expect(takeAIQuestion('a')).toBe('');
  });
});
