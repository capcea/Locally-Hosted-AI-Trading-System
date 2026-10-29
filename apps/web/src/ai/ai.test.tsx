import { expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import AICenter, { Registry } from './AICenter';
import { active, jobLabel, stateLabels } from './api';
import type { Job, Model } from './api';
import type { Session } from '../management-api';
import { resolveRoute, primary } from '../navigation/routes';
import { activeSection } from '../navigation/sections';

const registryLabels = [
  'Destinație aprobată',
  'Protocol',
  'Conexiune',
  'Rol',
  'Model principal',
  'Alternativă explicită · opțional',
];

it.each(['empty', 'loaded', 'revised'] as const)(
  'keeps AI registry select names independent of %s option content',
  (state) => {
    const populated = state !== 'empty';
    const model: Model = {
      id: '11111111-1111-4111-8111-111111111111',
      connection_id: '22222222-2222-4222-8222-222222222222',
      name: state === 'revised' ? 'Different model' : 'SYNTHETIC_HTTP_FIXTURE:1',
      context_ceiling: 4096,
      verification_current: true,
      verification: null,
      verified_until: '9999-01-01T00:00:00Z',
    };
    const markup = renderToStaticMarkup(
      <Registry
        models={
          populated ? [model, { ...model, id: 'unverified', verification_current: false }] : []
        }
        endpoints={
          populated
            ? [{ id: 'fixture', label: 'SYNTHETIC_HTTP_FIXTURE', transport: 'LOOPBACK' }]
            : []
        }
        connections={
          populated ? [{ id: model.connection_id, name: model.name, enabled: true }] : []
        }
        bindings={[]}
        busy={false}
        mutate={async () => undefined}
      />,
    );
    const selects = [...markup.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/g)];
    expect(selects).toHaveLength(registryLabels.length);
    expect(selects.map(([, attributes]) => /aria-label="([^"]+)"/.exec(attributes)?.[1])).toEqual(
      registryLabels,
    );
    if (populated) {
      expect(selects[0][2]).toContain('value="fixture"');
      expect(selects[0][2]).toContain('SYNTHETIC_HTTP_FIXTURE · LOOPBACK');
      expect(selects[4][2]).toContain(model.name);
      expect(selects[4][2]).not.toContain('value="unverified"');
    } else {
      expect(selects[0][2]).toContain('Configurează mai întâi destinația');
      expect(selects[2][2]).toContain('Creează mai întâi o conexiune activă');
      expect(selects[4][2]).toContain('Verifică mai întâi un model');
      expect(markup).toContain('Nicio destinație aprobată.');
      expect(markup).toContain('disabled=""');
    }
  },
);

it('keeps analysis and context selectors explicitly named before models are available', () => {
  vi.stubGlobal('window', { location: { pathname: '/testeaza/ai' } });
  try {
    const markup = renderToStaticMarkup(
      <AICenter session={{ user: { role: 'OWNER' }, csrf_token: '' } as Session} />,
    );
    const selects = [...markup.matchAll(/<select\b([^>]*)>/g)];
    expect(selects.map(([, attributes]) => /aria-label="([^"]+)"/.exec(attributes)?.[1])).toEqual([
      'Tipul analizei',
      'Tip de referință',
    ]);
  } finally {
    vi.unstubAllGlobals();
  }
});

it('preserves five destinations, guarded AI setup and reloadable job routes', () => {
  const id = '11111111-1111-4111-8111-111111111111';
  expect(primary).toHaveLength(5);
  const route = resolveRoute(`/testeaza/ai/${id}`);
  expect(route).toMatchObject({ screen: 'ai', area: 'research', jobId: id });
  expect(activeSection(route)).toBe('/testeaza/ai');
  expect(resolveRoute('/setari/ai')).toMatchObject({ area: 'settings', screen: 'ai' });
});

it('renders an honest unknown state and does not offer executable code or fabricated activity', () => {
  const session = { user: { role: 'OWNER' }, csrf_token: '' } as Session;
  vi.stubGlobal('window', { location: { pathname: '/testeaza/ai' } });
  let markup: string;
  try {
    markup = renderToStaticMarkup(<AICenter session={session} />);
  } finally {
    vi.unstubAllGlobals();
  }
  expect(markup).toContain('Niciun model confirmat disponibil');
  expect(markup).toContain('GPU: necunoscut');
  expect(markup).toContain('Niciun agent nu lucrează automat');
  expect(markup).toContain('SIMULATED / DENY_ALL');
  expect(markup).toContain('disabled=""');
  expect(markup).not.toContain('dangerouslySetInnerHTML');
});

it('keeps requested cancellation pending until a terminal worker acknowledgement', () => {
  expect(active({ state: 'RUNNING', cancel_requested: true } as Job)).toBe(true);
  expect(active({ state: 'CANCELLED', cancel_requested: true } as Job)).toBe(false);
  expect(stateLabels.UNKNOWN).toContain('nu poate fi confirmat');
  expect(stateLabels.CANCELLED).toContain('local');
  expect(jobLabel({ kind: 'PROBE', role: 'LIGHTWEIGHT' } as Job)).toBe('Verifică modelul');
  expect(jobLabel({ kind: 'DISCOVER', role: 'LIGHTWEIGHT' } as Job)).toBe(
    'Citește modelele disponibile',
  );
});

it('uses explicit OpenRouter protocol and cloud consent without exposing credential inputs by default', () => {
  const markup = renderToStaticMarkup(
    <Registry
      models={[]}
      bindings={[]}
      busy={false}
      mutate={async () => undefined}
      endpoints={[{ id: 'openrouter', label: 'OpenRouter', transport: 'OPENROUTER_PUBLIC' }]}
      connections={[
        {
          id: 'connection',
          name: 'Cloud public',
          enabled: true,
          provider: 'OPENROUTER',
          credential_configured: false,
        },
      ]}
    />,
  );
  expect(markup).toContain('OPENROUTER · OpenAI compatibil');
  expect(markup).toContain('Aprob politica cloud public separat de aprobarea privată.');
  expect(markup).toContain('Lipsește cheia');
  expect(markup).toContain('Configurează cheia OpenRouter');
  expect(markup).not.toContain('type="password"');
  expect(markup).toContain('Verifică mai întâi un model');
});
