import { expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { PublicReadTime } from './PublicReadTime';

it.each([
  '2024-01-02T00:00:00Z',
  '2024-01-02T01:01:01Z',
  '2024-01-02T08:08:08Z',
  '2024-01-02T23:59:59Z',
])('retains the exact observation and an eight-character Romanian clock: %s', (iso) => {
  const html = renderToStaticMarkup(<PublicReadTime at={Date.parse(iso)} />);
  expect(html).toContain(`dateTime="${new Date(iso).toISOString()}"`);
  expect(html).toMatch(/>[0-9]{2}:[0-9]{2}:[0-9]{2}<\/time>/);
  expect(html).toContain('data-visual-clock="true"');
});
