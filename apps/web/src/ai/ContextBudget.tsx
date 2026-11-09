import { useEffect, useState } from 'react';
import { api, ApiError, safeError } from '../management-api';
import type { BudgetDiagnostics } from './budget-diagnostics';
import type { Submission } from './api';

export type ContextMode = 'AUTO' | 'RAPID' | 'STANDARD' | 'COMPLEX';
export type ContextBudget = BudgetDiagnostics & {
  selected_context_tokens?: number;
  remaining_context_tokens?: number;
  platform_context_ceiling?: number;
};
type Preview = {
  budget: ContextBudget;
  financial: null | {
    available: boolean;
    reservation_usd: string;
    request_limit_usd: string;
    daily_reserved_usd: string;
    daily_remaining_usd?: string;
    monthly_remaining_usd?: string | null;
    daily_limit_usd: string;
    monthly_reserved_usd: string;
    monthly_limit_usd: string | null;
  };
};

/** Advisory server assembly only. No inference/reservation and no persisted prompt or consent. */
export function useContextPreview(body: Submission | null, csrf: string) {
  const payload = body ? JSON.stringify(body) : '';
  const [observed, setObserved] = useState<{
    payload: string;
    value?: Preview;
    error?: string;
    budget?: ContextBudget;
  } | null>(null);
  useEffect(() => {
    if (!payload) return;
    const controller = new AbortController();
    // Debounce typing, not synchronization with provider or job completion.
    const timer = window.setTimeout(() => {
      void api<Preview>('/ai/requests/preview', {
        method: 'POST',
        body: JSON.parse(payload),
        csrf,
        signal: controller.signal,
      })
        .then((value) => {
          if (!controller.signal.aborted) setObserved({ payload, value });
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted)
            setObserved({
              payload,
              error: safeError(error),
              budget: error instanceof ApiError ? error.budget : undefined,
            });
        });
    }, 400);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [payload, csrf]);
  return observed?.payload === payload ? observed : null;
}

export function ContextBudgetControl({
  mode,
  onChange,
  disabled,
  ceiling,
  preview,
}: {
  mode: ContextMode;
  onChange: (mode: ContextMode) => void;
  disabled: boolean;
  ceiling: number | null;
  preview: ReturnType<typeof useContextPreview>;
}) {
  const budget = preview?.value?.budget ?? preview?.budget;
  const financial = preview?.value?.financial;
  return (
    <div className="ai-chat-context-budget">
      <label>
        Context AI{' '}
        <select
          aria-label="Context AI"
          value={mode}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value as ContextMode)}
        >
          <option value="AUTO">AUTO</option>
          <option value="RAPID">4K</option>
          <option value="STANDARD">16K</option>
          <option value="COMPLEX">32K</option>
        </select>
      </label>
      <p className="ai-chat-hint" aria-live="polite">
        Plafon verificat disponibil:{' '}
        {ceiling === null ? 'necunoscut' : `${ceiling.toLocaleString('ro-RO')} tokeni`}.
        {budget ? (
          <>
            {' '}
            Nivel selectat:{' '}
            {(budget.selected_context_tokens ?? budget.effective_context_tokens).toLocaleString(
              'ro-RO',
            )}
            . Consum estimat conservator:{' '}
            {budget.required_context_upper_bound.toLocaleString('ro-RO')}. Marjă context:{' '}
            {(
              budget.remaining_context_tokens ??
              Math.max(0, budget.effective_context_tokens - budget.required_context_upper_bound)
            ).toLocaleString('ro-RO')}
            .
          </>
        ) : (
          ' Nivelul și consumul se calculează pe server după completarea întrebării.'
        )}{' '}
        Estimarea folosește octeți și rezerva de răspuns; nu reprezintă tokenizarea sau factura
        furnizorului.
      </p>
      {financial && (
        <p className="ai-chat-hint">
          Rezervare estimată: {financial.reservation_usd} USD · limită/cerere:{' '}
          {financial.request_limit_usd} USD. Rezervat zilnic: {financial.daily_reserved_usd}/
          {financial.daily_limit_usd} USD.{' '}
          {financial.available
            ? 'Buget disponibil la această citire.'
            : 'Buget financiar insuficient; nu trimitem automat cererea.'}{' '}
          Disponibil zilnic: {financial.daily_remaining_usd ?? 'necunoscut'} USD; lunar:{' '}
          {financial.monthly_remaining_usd ?? 'necunoscut'} USD. Serverul verifică din nou limitele
          la trimitere.
        </p>
      )}
      {preview?.error && <p className="ai-chat-error">{preview.error}</p>}
    </div>
  );
}
