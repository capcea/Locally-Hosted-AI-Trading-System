/** Response headers contain sizes only. Never reflect arbitrary header strings in product errors. */
const fields = [
  'message_content_bytes',
  'schema_bytes',
  'input_upper_bound',
  'framing_tokens',
  'output_tokens',
  'requested_context_tokens',
  'registered_context_tokens',
  'verified_context_tokens',
  'effective_context_tokens',
  'required_context_upper_bound',
] as const;
const extraFields = [
  'selected_context_tokens',
  'remaining_context_tokens',
  'platform_context_ceiling',
  'minimum_fitting_tier',
] as const;
export type BudgetDiagnostics = Record<(typeof fields)[number], number> &
  Partial<Record<(typeof extraFields)[number], number>>;
export function parseBudgetDiagnostics(raw: string | null): BudgetDiagnostics | undefined {
  if (!raw || raw.length > 4096) return;
  try {
    const value = JSON.parse(raw);
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;
    const clean = {} as BudgetDiagnostics;
    for (const field of fields) {
      if (
        typeof value[field] !== 'number' ||
        !Number.isSafeInteger(value[field]) ||
        value[field] < 0 ||
        value[field] > 1000000
      )
        return;
      clean[field] = value[field];
    }
    for (const field of extraFields) {
      if (value[field] === undefined) continue;
      if (
        typeof value[field] !== 'number' ||
        !Number.isSafeInteger(value[field]) ||
        value[field] < 0 ||
        value[field] > 1000000
      )
        return;
      clean[field] = value[field];
    }
    return clean;
  } catch {
    return;
  }
}
export function budgetExplanation(b: BudgetDiagnostics) {
  return ` Text: ${b.message_content_bytes} octeți; schemă: ${b.schema_bytes} octeți; rezervă format: ${b.framing_tokens}; răspuns rezervat: ${b.output_tokens} tokeni. Limită necesară conservatoare: ${b.required_context_upper_bound}; buget efectiv: ${b.effective_context_tokens}; capacitate verificată: ${b.verified_context_tokens}. Nivel minim configurat care încape: ${b.minimum_fitting_tier || 'niciunul'}. Estimare conservatoare pe octeți, nu tokenizare exactă.`;
}
