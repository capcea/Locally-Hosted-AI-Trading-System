import { expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ProviderError } from './ProviderError';

it.each([
  [404, 'MODEL_METADATA', 'Citirea detaliilor modelului'],
  [400, 'COMPLETION', 'Solicitarea de generare'],
  [503, 'MODEL_CATALOG', 'Citirea catalogului de modele'],
] as const)(
  'displays the actual observed HTTP%s and allowlisted %s stage',
  (status, operation, label) => {
    const markup = renderToStaticMarkup(
      <ProviderError
        error="AI_PROVIDER_REQUEST_REFUSED"
        metadata={{ provider_diagnostic: { http_status: status, operation } }}
      />,
    );
    expect(markup).toContain(`<dd>${status}</dd>`);
    expect(markup).toContain(label);
    expect(markup).toContain('Nu retrimitem automat');
    expect(markup).toContain('Cod diagnostic:');
    if (operation === 'MODEL_METADATA')
      expect(markup).toContain('identificatorul exact autor/model');
  },
);

it('does not invent a status for a historical failure with no diagnostic data', () => {
  const markup = renderToStaticMarkup(
    <ProviderError error="AI_PROVIDER_REQUEST_REFUSED" metadata={null} />,
  );
  expect(markup).toContain('nu au fost păstrate');
  expect(markup).not.toContain('Status HTTP primit');
  expect(markup).not.toContain('<dd>400</dd>');
});

it('explains an approved provider ZDR conflict without proposing a privacy bypass or invented HTTP', () => {
  const markup = renderToStaticMarkup(
    <ProviderError error="AI_APPROVED_UPSTREAM_NOT_ZDR" metadata={null} />,
  );
  expect(markup).toContain('furnizorul aprobat nu apare în catalogul ZDR');
  expect(markup).toContain('nu dezactivăm ZDR');
  expect(markup).toContain('Nu a fost trimisă generarea');
  expect(markup).not.toContain('Status HTTP primit');
});

it.each([
  { http_status: '404', operation: 'MODEL_METADATA' },
  { http_status: 404, operation: 'PRIVATE_PROVIDER_TEXT' },
  { http_status: 404, operation: 'MODEL_METADATA', body: 'PRIVATE_PROVIDER_TEXT' },
  { http_status: 999, operation: 'COMPLETION' },
])('rejects malformed or extra provider data without echoing its fields', (value) => {
  const markup = renderToStaticMarkup(
    <ProviderError error="AI_PROVIDER_REQUEST_REFUSED" metadata={{ provider_diagnostic: value }} />,
  );
  expect(markup).not.toContain('Status HTTP primit');
  expect(markup).not.toContain('PRIVATE_PROVIDER_TEXT');
});
