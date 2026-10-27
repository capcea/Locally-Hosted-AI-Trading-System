import type { components } from './generated/api';
import { parseOverview } from './schema';

export type Overview = components['schemas']['Overview'];
export type Service = components['schemas']['ServiceHealth'];

export async function getOverview(signal?: AbortSignal): Promise<Overview> {
  const response = await fetch('/api/v1/overview', { signal, cache: 'no-store' });
  if (!response.ok) throw new Error(`API indisponibil (${response.status}).`);
  return parseOverview(await response.json());
}

export function isStale(lastSuccess: number | null, now: number): boolean {
  return lastSuccess === null || now < lastSuccess || now - lastSuccess > 45_000;
}

export function readinessSummary(services: Service[]): { healthy: number; total: number } {
  const dependencies = services.filter((service) =>
    ['api', 'postgres', 'redis', 'storage'].includes(service.id),
  );
  return {
    healthy: dependencies.filter((service) => service.status === 'HEALTHY').length,
    total: dependencies.length,
  };
}
