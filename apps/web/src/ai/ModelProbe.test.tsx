import { expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ModelProbe, probeDisabledReason } from './ModelProbe';
import type { Connection } from './api';
import { Registry } from './AICenter';

const cloud: Connection = {
  id: 'synthetic-cloud',
  name: 'SYNTHETIC_TEST_FIXTURE',
  provider: 'OPENROUTER',
  enabled: true,
  credential_configured: true,
};

it.each([
  [true, cloud, true, 'operațiunii în curs'],
  [false, undefined, true, 'nu poate fi confirmată'],
  [false, { ...cloud, enabled: false }, true, 'Activează conexiunea'],
  [false, { ...cloud, credential_configured: false }, true, 'Configurează cheia'],
  [false, cloud, false, 'Bifează aprobarea costului'],
] as const)(
  'explains the actual probe blocker (busy=%s, connection=%s, approval=%s)',
  (busy, connection, approval, expected) => {
    expect(probeDisabledReason(busy, connection, approval)).toContain(expected);
  },
);

it.each([false, true])(
  'keeps the OpenRouter cost confirmation next to its own button; approved=%s',
  (approved) => {
    const submit = vi.fn();
    const change = vi.fn();
    const markup = renderToStaticMarkup(
      <ModelProbe
        modelName="SYNTHETIC_TEST_FIXTURE"
        connection={cloud}
        busy={false}
        costApproved={approved}
        setCostApproved={change}
        submit={submit}
      />,
    );
    expect(markup).toContain('role="group"');
    expect(markup).toContain('cu posibile costuri');
    const button = /<button\b([^>]*)>Verifică printr-o solicitare reală<\/button>/.exec(markup);
    expect(button).not.toBeNull();
    expect(button![1].includes('disabled=""')).toBe(!approved);
    const description = /aria-describedby="([^"]+)"/.exec(button![1])![1];
    expect(markup).toContain(`id="${description}"`);
    expect(markup).toContain(approved ? 'numai când apeși butonul' : 'Bifează aprobarea costului');
    expect(submit).not.toHaveBeenCalled();
    expect(change).not.toHaveBeenCalled();
  },
);

it('keeps private provider verification independent of cloud-cost approval', () => {
  const privateConnection = { ...cloud, provider: 'OLLAMA_NATIVE', credential_configured: false };
  expect(probeDisabledReason(false, privateConnection, false)).toBe('');
  const markup = renderToStaticMarkup(
    <ModelProbe
      modelName="SYNTHETIC_PRIVATE_FIXTURE"
      connection={privateConnection}
      busy={false}
      costApproved={false}
      setCostApproved={() => undefined}
      submit={() => undefined}
    />,
  );
  expect(markup).not.toContain('type="checkbox"');
  expect(markup).not.toContain('disabled=""');
  expect(markup).toContain('conexiunea privată aprobată');
});

it('renders one unchecked cloud approval inside each model action, not as a reordered grid item', () => {
  const mutate = vi.fn();
  const markup = renderToStaticMarkup(
    <Registry
      models={['one', 'two'].map((id) => ({
        id,
        name: `SYNTHETIC_MODEL_${id}`,
        connection_id: cloud.id,
        context_ceiling: 4096,
        verification_current: false,
        verification: null,
        verified_until: null,
      }))}
      endpoints={[]}
      connections={[cloud]}
      bindings={[]}
      busy={false}
      mutate={mutate}
    />,
  );
  const actions = [
    ...markup.matchAll(
      /<div role="group" aria-label="Verificare model ([^"]+)">([\s\S]*?)<\/div>/g,
    ),
  ];
  expect(actions).toHaveLength(2);
  for (const [, , group] of actions) {
    expect(group).toContain('type="checkbox"');
    expect(group).not.toContain('checked=""');
    expect(group).toContain('Bifează aprobarea costului');
    expect(group).toContain('Verifică printr-o solicitare reală');
    expect(group).toContain('disabled=""');
  }
  expect(mutate).not.toHaveBeenCalled();
});
