import { isStale } from './api';
import type { Overview, Service } from './api';
import { ro } from './locale';

export const infrastructureServices = [
  { id: 'api', label: 'API' },
  { id: 'postgres', label: 'Bază de date' },
  { id: 'redis', label: 'Redis' },
  { id: 'storage', label: 'Stocare (MinIO)' },
] as const;
export type InfrastructureStatus = 'HEALTHY' | 'DEGRADED' | 'DOWN' | 'UNKNOWN';

export function infrastructureHealth(overview: Overview | null, stale: boolean, now: number) {
  const unverified = stale || !overview || isStale(Date.parse(overview.timestamp), now);
  const rows = infrastructureServices.map(({ id, label }) => {
    const matches = overview?.services.filter((service) => service.id === id) ?? [];
    const service: Service | undefined = matches.length === 1 ? matches[0] : undefined;
    let status: InfrastructureStatus = 'UNKNOWN';
    if (!unverified && service?.status === 'HEALTHY') status = 'HEALTHY';
    if (!unverified && ['UNAVAILABLE', 'DISABLED'].includes(service?.status ?? '')) status = 'DOWN';
    return {
      id,
      label,
      status,
      text: unverified || !service ? 'UNKNOWN' : (ro.statuses[service.status] ?? 'UNKNOWN'),
      detail: service?.detail,
    };
  });
  const status: InfrastructureStatus = rows.some((row) => row.status === 'UNKNOWN')
    ? 'UNKNOWN'
    : rows.every((row) => row.status === 'HEALTHY')
      ? 'HEALTHY'
      : rows.every((row) => row.status === 'DOWN')
        ? 'DOWN'
        : 'DEGRADED';
  return { status, rows };
}
