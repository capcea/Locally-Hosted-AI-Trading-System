import { z } from 'zod';
import { researchErrors } from './copy/ro';
import { aiErrors } from './ai/copy';
import { parseBudgetDiagnostics, budgetExplanation } from './ai/budget-diagnostics';
import type { BudgetDiagnostics } from './ai/budget-diagnostics';
import { campaignErrors } from './campaigns/copy';
import type { components } from './generated/api';
import {
  authRevision,
  advanceAuthRevision,
  authCode,
  authMessages,
  rotatesSession,
} from './auth/lifecycle';

export type Session = components['schemas']['SessionView'];
export type RecordItem = components['schemas']['RecordView'];
export type RecordBody = RecordItem['data'];
export type RecordPage = components['schemas']['RecordPage'];
export type AuditEvent = components['schemas']['AuditView'];
export type User = components['schemas']['UserView'];

const sessionSchema = z.object({
  auth_mode: z.enum(['PASSWORD', 'TOTP']).default('TOTP'),
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
    public code = '',
    public budget?: BudgetDiagnostics,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; csrf?: string; signal?: AbortSignal } = {},
): Promise<T> {
  let revision = authRevision();
  const obsolete = () => new ApiError(409, authMessages.AUTH_STATE_CHANGED, 'AUTH_STATE_CHANGED');
  const response = await fetch(`/api/v1${path}`, {
    method: options.method ?? 'GET',
    credentials: 'same-origin',
    cache: 'no-store',
    ...(options.signal ? { signal: options.signal } : {}),
    headers: {
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(options.csrf ? { 'X-CSRF-Token': options.csrf } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (revision !== authRevision()) throw obsolete();
  if (!response.ok) {
    const labels: Record<number, string> = {
      401: 'Sesiune expirată sau date de autentificare incorecte.',
      403: 'Acces refuzat. Verifică rolul, sesiunea și protecția cererii.',
      404: 'Înregistrarea nu există sau nu îți aparține.',
      409: 'Conflict: reîncarcă datele și verifică versiunea sau condițiile acțiunii.',
      422: 'Date invalide. Verifică toate câmpurile și folosește valori zecimale exacte.',
      429: 'Prea multe încercări. Reîncearcă mai târziu; nu presupunem un interval de așteptare.',
      503:
        options.method && options.method !== 'GET'
          ? 'Nu putem confirma solicitarea. Verifică activitatea înainte de a trimite din nou.'
          : 'Serviciul necesar nu răspunde. Păstrează draftul și reîncarcă informațiile.',
    };
    const detail = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    if (revision !== authRevision()) throw obsolete();
    const code =
      authCode(response.headers.get('X-Auth-Error'), detail?.detail) ||
      (path.startsWith('/ai/') &&
      typeof detail?.detail === 'string' &&
      [
        'AI_CONTEXT_BUDGET_EXCEEDED',
        'AI_CONTEXT_BUDGET_UNVERIFIED',
        'AI_INPUT_BYTE_LIMIT',
        'AI_CONTEXT_TIER_UNAVAILABLE',
        'AI_REQUEST_BYTE_LIMIT',
      ].includes(detail.detail)
        ? detail.detail
        : '') ||
      (response.status === 401
        ? path === '/auth/login'
          ? 'LOGIN_INVALID'
          : 'SESSION_EXPIRED'
        : '');
    let detailCode = '';
    // Only the explicitly classified capacity/size failures replace the generic 422 heading.
    const aiMessage = Object.hasOwn(aiErrors, code) ? aiErrors[code] : '';
    const budget =
      code.startsWith('AI_CONTEXT_BUDGET_') || code === 'AI_CONTEXT_TIER_UNAVAILABLE'
        ? parseBudgetDiagnostics(response.headers.get('X-AI-Context-Budget'))
        : undefined;
    const messages = path.startsWith('/campaigns')
      ? campaignErrors
      : path.startsWith('/ai/')
        ? aiErrors
        : researchErrors;
    if (path.startsWith('/research/') || path.startsWith('/ai/') || path.startsWith('/campaigns')) {
      if (typeof detail?.detail === 'string' && Object.hasOwn(messages, detail.detail))
        detailCode = (aiMessage ? '' : ' ' + messages[detail.detail]) + ' [' + detail.detail + ']';
    }
    if (typeof window !== 'undefined') {
      const event =
        code === 'SESSION_EXPIRED' || code === 'LOGIN_REQUIRED'
          ? 'research-session-expired'
          : code === 'MFA_RECENT_REQUIRED'
            ? 'research-mfa-required'
            : code === 'CSRF_FAILED' || code === 'MFA_REQUIRED'
              ? 'research-session-refresh'
              : null;
      if (event) window.dispatchEvent(new CustomEvent(event, { detail: code }));
    }
    throw new ApiError(
      response.status,
      (code === 'MFA_INVALID' && path === '/auth/reauthenticate'
        ? 'Parola sau codul MFA nu sunt valide. Dacă ai folosit deja codul, așteaptă următorul cod din autentificator.'
        : (authMessages[code] ??
          (aiMessage || labels[response.status]) ??
          'Cererea nu a putut fi finalizată.')) +
        detailCode +
        (budget ? budgetExplanation(budget) : ''),
      code,
      budget,
    );
  }
  if (options.method === 'POST' && rotatesSession(path)) revision = advanceAuthRevision();
  if (response.status === 204) return undefined as T;
  const result = (await response.json()) as T;
  if (revision !== authRevision()) throw obsolete();
  return result;
}

export function parseSession(value: unknown): Session {
  return sessionSchema.parse(value);
}

export function safeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof SyntaxError)
    return 'Configurația JSON nu este validă. Verifică formatul; nu executăm cod din acest câmp.';
  const known = [
    'Configurează și verifică mai întâi contextul de risc al șablonului.',
    'Selectează un fișier CSV sau Parquet.',
    'Reîncarcă starea contului.',
    'Setul și șablonul trebuie să aibă același instrument. Pentru portofolii folosește configurația JSON avansată.',
    'Catalogul nu a putut fi citit complet. Nu presupunem că înregistrările lipsă sunt sigure sau inexistente.',
  ];
  return error instanceof Error && known.includes(error.message)
    ? error.message
    : 'Operațiunea nu a putut fi verificată. Păstrează setările neconfidențiale și verifică starea înainte de a retrimite.';
}
