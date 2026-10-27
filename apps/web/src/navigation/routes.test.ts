import { describe, expect, it } from 'vitest';
import { primary, resolveRoute } from './routes';

const id = '11111111-1111-4111-8111-111111111111';
const paths = [
  '/',
  '/autentificare',
  '/configurare-proprietar',
  '/securizare-cont',
  '/testeaza',
  '/testeaza/strategii',
  '/testeaza/nou',
  '/testeaza/activitate',
  `/testeaza/${id}/progres`,
  '/testeaza/date',
  '/testeaza/date/import',
  `/testeaza/date/importuri/${id}`,
  `/testeaza/date/${id}`,
  ...['previzualizare', 'provenienta', 'versiuni'].map((s) => `/testeaza/date/${id}/${s}`),
  '/testeaza/evaluare-finala',
  `/testeaza/evaluare-finala/${id}`,
  '/rezultate',
  '/rezultate/compara',
  `/rezultate/${id}`,
  ...['tranzactii', 'decizii', 'validare', 'provenienta'].map((s) => `/rezultate/${id}/${s}`),
  '/rezultate/simulari',
  `/rezultate/simulari/${id}/jurnal`,
  '/conturi',
  ...[
    '',
    '/siguranta',
    '/inchidere-simulata',
    '/limite',
    '/politici',
    '/ipoteze',
    '/verificare-risc',
    '/alocari-incidente',
    '/conexiuni',
    '/avansat/inregistrari-risc',
    '/avansat/simulator/nou',
    `/avansat/simulator/${id}/date`,
    `/avansat/simulator/${id}/ordine`,
    `/politici/${id}`,
    `/conexiuni/${id}/observatii`,
  ].map((s) => `/conturi/${id}${s}`),
  ...[
    '',
    '/aspect',
    '/securitate',
    '/utilizatori',
    '/istoric',
    '/surse',
    '/catalog',
    '/registru-tehnic',
    '/diagnostic',
    '/despre',
    '/despre/plan',
  ].map((s) => `/setari${s}`),
];
describe('finite task routes', () => {
  it.each(paths)('keeps the mapped destination reachable: %s', (path) => {
    expect(resolveRoute(path).screen).not.toBe('not-found');
    expect(resolveRoute(path).path).toBe(path);
  });
  it.each([
    'https://outside.invalid/',
    '//outside.invalid',
    '/api/v1/orders',
    '/conturi/invalid/siguranta',
    `/conturi/${id}/politici/unreviewed/arbitrary`,
    '/setari/live',
    '/rezultate/compara/extra',
  ])('rejects unknown and external return paths: %s', (path) => {
    expect(resolveRoute(path).screen).toBe('not-found');
  });
  it('resolves static routes before opaque IDs and preserves ownership identifiers', () => {
    expect(primary).toHaveLength(5);
    expect(resolveRoute('/rezultate/compara').section).toBe('compare');
    expect(resolveRoute(`/rezultate/${id}/provenienta`).experimentId).toBe(id);
    expect(resolveRoute(`/conturi/${id}/avansat/simulator/${id}/ordine`).runId).toBe(id);
  });
});
