import { expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ContextBudgetControl } from './ContextBudget';
import type { ContextMode } from './ContextBudget';

it.each(['AUTO', 'RAPID', 'STANDARD', 'COMPLEX'] as ContextMode[])(
  'keeps %s accessible without repeated consent',
  (mode) => {
    const markup = renderToStaticMarkup(
      <ContextBudgetControl
        mode={mode}
        onChange={() => undefined}
        disabled={false}
        ceiling={32768}
        preview={null}
      />,
    );
    expect(markup).toContain('aria-label="Context AI"');
    expect(markup).toContain(`value="${mode}" selected=""`);
    expect(markup).toContain('Plafon verificat disponibil');
    expect(markup).toContain('Nivelul și consumul se calculează pe server');
    expect(markup).not.toContain('checkbox');
  },
);
it('never fabricates remaining capacity when verification or preview is unavailable', () => {
  const markup = renderToStaticMarkup(
    <ContextBudgetControl
      mode="AUTO"
      onChange={() => undefined}
      disabled
      ceiling={null}
      preview={null}
    />,
  );
  expect(markup).toContain('necunoscut');
  expect(markup).not.toContain('Marjă context:');
});
