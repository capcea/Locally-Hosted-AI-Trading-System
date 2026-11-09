import type { Role } from './api';
import { aiErrors } from './copy';

export type Readiness = {
  ready: boolean;
  reason: string | null;
  observed_at: string;
  gateway_configured: boolean;
  worker_state: string;
  worker_expires_at: string | null;
  model_id?: string | null;
  model_verified: boolean;
  standing_active: boolean;
  standing_authorization_id: string | null;
  budget: {
    available: boolean;
    daily_reserved_usd?: string;
    monthly_reserved_usd?: string;
    daily_limit_usd?: string;
    monthly_limit_usd?: string;
  } | null;
};
export type ReadinessObservation = {
  role: Role;
  category: string;
  value: Readiness;
  received: number;
};
export function observationFresh(
  observation: ReadinessObservation | null,
  role: Role,
  category: string,
  now: number,
): boolean {
  if (!observation || observation.role !== role || observation.category !== category) return false;
  const age = now - Date.parse(observation.value.observed_at);
  return (
    now >= observation.received &&
    now - observation.received < 20000 &&
    Number.isFinite(age) &&
    age >= -5000 &&
    age < 20000
  );
}
export function workerObserved(
  observation: ReadinessObservation | null,
  role: Role,
  category: string,
  now: number,
): boolean {
  return (
    observationFresh(observation, role, category, now) &&
    observation!.value.worker_state === 'OBSERVED_RECENTLY' &&
    Date.parse(observation!.value.worker_expires_at ?? '') > now
  );
}
export function inferenceUnavailable(
  observation: ReadinessObservation | null,
  role: Role,
  category: string,
  now = Date.now(),
) {
  if (
    !observation ||
    observation.role !== role ||
    observation.category !== category ||
    now < observation.received ||
    now - observation.received >= 20000
  )
    return 'Disponibilitatea AI nu poate fi confirmată. Reîncarcă starea.';
  const value = observation.value;
  const age = now - Date.parse(value.observed_at);
  if (!Number.isFinite(age) || age < -5000 || age >= 20000)
    return 'Observația AI a expirat sau ora nu poate fi confirmată. Reîncarcă starea.';
  if (!value.ready)
    return (
      aiErrors[value.reason ?? ''] ??
      'Solicitarea nu este disponibilă. Verifică autorizarea, modelul și limitele.'
    );
  if (
    !value.gateway_configured ||
    !value.standing_active ||
    !value.standing_authorization_id ||
    !value.model_verified ||
    !workerObserved(observation, role, category, now) ||
    value.budget?.available !== true
  )
    return 'Cerințele pentru inferență nu sunt confirmate. Reîncarcă starea.';
  return '';
}
