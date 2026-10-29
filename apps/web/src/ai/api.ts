import { api } from '../management-api';
import type { components } from '../generated/api';

export type Job = components['schemas']['AIJobView'];
export type Submission = components['schemas']['RequestInput'];
export type Role = Submission['role'];
export type Model = {
  id: string;
  name: string;
  connection_id: string;
  context_ceiling: number;
  verification_current: boolean;
  verification: Record<string, unknown> | null;
  verified_until: string | null;
};
export type Status = {
  configured: boolean;
  model_count: number;
  worker_state: string;
  gpu_availability: string;
  external_execution: 'DENY_ALL';
  generated_code_execution: false;
  limits: { hourly_owner: number; hourly_role: number; global_concurrency: number };
};
export type Binding = { role: Role; model_id: string; revision: number; fallback_ids: string[] };
export type Endpoint = { id: string; label: string; transport: string };
export type Connection = {
  id: string;
  enabled: boolean;
  name: string;
  provider?: string;
  credential_configured?: boolean;
};
export const roles: Role[] = ['RESEARCH', 'CODING', 'CRITIC', 'LIGHTWEIGHT'];
export const roleLabels: Record<Role, string> = {
  RESEARCH: 'Propune o ipoteză',
  CODING: 'Propune cod · numai text',
  CRITIC: 'Caută puncte slabe',
  LIGHTWEIGHT: 'Rezumă dovezile',
};
export const stateLabels: Record<Job['state'], string> = {
  QUEUED: 'Solicitată',
  RUNNING: 'În curs de analiză',
  RETRY: 'Reîncercare sigură programată',
  SUCCEEDED: 'Analiză salvată · neverificată',
  FAILED: 'Analiză refuzată sau eșuată',
  CANCELLED: 'Anulare confirmată local',
  UNKNOWN: 'Rezultatul furnizorului nu poate fi confirmat',
};
export const active = (job: Job) => ['QUEUED', 'RUNNING', 'RETRY'].includes(job.state);
export const jobLabel = (job: Job) =>
  job.kind === 'DISCOVER'
    ? 'Citește modelele disponibile'
    : job.kind === 'PROBE'
      ? 'Verifică modelul'
      : (roleLabels[job.role as Role] ?? 'Analiză AI');
export const ai = <T>(path: string) => api<T>(`/ai${path}`);
export const verified = (model: Model, now = Date.now()) =>
  model.verification_current &&
  model.verified_until !== null &&
  Date.parse(model.verified_until) > now;
