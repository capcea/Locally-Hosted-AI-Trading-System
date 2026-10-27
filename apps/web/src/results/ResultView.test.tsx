import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { EquityChart, exact, ResultSummary } from './ResultView';

describe('stored result presentation', () => {
  it('retains canonical money precision and unavailable metrics', () => {
    expect(exact('25000.12345678')).toBe('25000.12345678');
    expect(exact(null)).toBe('Nu poate fi stabilit');
    expect(exact(0)).toBe('0');
    expect(exact(Infinity)).toBe('Vezi dovezile exacte');
  });
  it('shows evidence, uncertain ratios and separate simulation mode', () => {
    const html = renderToStaticMarkup(
      <ResultSummary
        result={{
          engine: 'EVENT',
          phase: 'VALIDATION',
          trials: [
            {
              metrics: {
                net_profit: '-42.12345678',
                max_drawdown: null,
                trade_count: 2,
                ratios_reason: 'FEWER_THAN_30_DAILY_OBSERVATIONS',
              },
            },
          ],
        }}
        provenance={{
          plan: {
            assumptions: { account_currency: 'USD' },
            datasets: [],
            chronology: { start: 'synthetic-start', end: 'synthetic-end' },
          },
        }}
      />,
    );
    expect(html).toContain('-42.12345678');
    expect(html).toContain('Nu poate fi stabilit');
    expect(html).toContain('prea puține observații');
    expect(html).toContain('Execuție simulată');
    expect(html).toContain('nu demonstrează profit viitor');
  });
  it('screening never appears risk validated and currency is not guessed', () => {
    const html = renderToStaticMarkup(
      <ResultSummary result={{ engine: 'SCREEN', trials: [{ approximate_net: '1.01' }] }} />,
    );
    expect(html).toContain('nu validează execuția și riscul');
    expect(html).toContain('monedă neconfirmată');
  });
  it('labels sampling and offers exact values without connecting missing observations', () => {
    const html = renderToStaticMarkup(
      <EquityChart
        total={1000}
        currency="USD"
        points={[
          { at: '2024-01-02T00:00:00Z', timestamp: 1, equity: '25000.12345678' },
          { at: '2024-01-03T00:00:00Z', timestamp: 86401, equity: '24999.12345678' },
        ]}
      />,
    );
    expect(html).toContain('2 din 1000');
    expect(html).toContain('25000.12345678');
    expect(html).toContain('<table>');
    expect(html).not.toContain('<polyline');
    expect(html).toContain('nu înlocuiește cea mai mare scădere');
  });
});
