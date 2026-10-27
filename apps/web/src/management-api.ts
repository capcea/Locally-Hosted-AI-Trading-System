import { z } from 'zod';
import type { components } from './generated/api';

export type Session = components['schemas']['SessionView'];
export type RecordItem = components['schemas']['RecordView'];
export type RecordBody = RecordItem['data'];
export type RecordPage = components['schemas']['RecordPage'];
export type AuditEvent = components['schemas']['AuditView'];
export type User = components['schemas']['UserView'];

const sessionSchema = z.object({
  user: z.object({
    id: z.uuid(),
    username: z.string(),
    display_name: z.string(),
    role: z.enum(['OWNER', 'OPERATOR', 'VIEWER']),
    active: z.boolean(),
  }),
  state: z.enum(['ENROLLMENT', 'MFA', 'FULL']),
  csrf_token: z.string().regex(/^[a-f0-9]{64}$/),
  expires_at: z.string(),
  session_id: z.uuid(),
});

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; csrf?: string } = {},
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method: options.method ?? 'GET',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: {
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(options.csrf ? { 'X-CSRF-Token': options.csrf } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.ok) {
    const labels: Record<number, string> = {
      401: 'Sesiune expirată sau date de autentificare incorecte.',
      403: 'Acces refuzat. Verifică rolul, sesiunea MFA și protecția cererii.',
      404: 'Înregistrarea nu există sau nu îți aparține.',
      409: 'Conflict: reîncarcă datele și verifică versiunea sau condițiile acțiunii.',
      422: 'Date invalide. Verifică toate câmpurile și folosește valori zecimale exacte.',
      429: 'Prea multe încercări. Reîncearcă după 15 minute.',
      503: 'Serviciul persistent nu este pregătit. Configurarea identității și migrarea sunt necesare.',
    };
    throw new ApiError(
      response.status,
      labels[response.status] ?? 'Cererea nu a putut fi finalizată.',
    );
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function parseSession(value: unknown): Session {
  return sessionSchema.parse(value);
}
