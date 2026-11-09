import { z } from 'zod';

const decimal = z.string().regex(/^\d+(\.\d+)?$/);
export const cloudPolicySchema = z.object({
  version: z.literal('openrouter-public-v1'),
  upstream_provider: z.string().regex(/^[a-z0-9][a-z0-9_/-]{1,79}$/),
  input_usd_per_million: decimal,
  output_usd_per_million: decimal,
  request_usd: decimal,
  daily_usd: decimal,
  acknowledged_public_cloud: z.literal(true),
  acknowledged_upstream_processing: z.literal(true),
  acknowledged_cost: z.literal(true),
  acknowledged_provider_policy_limits: z.literal(true),
});
export type CloudPolicy = z.infer<typeof cloudPolicySchema>;
export const cloudStatusSchema = z.object({
  operator_enabled: z.boolean(),
  provider: z.literal('OPENROUTER'),
  base_url: z.literal('https://openrouter.ai/api/v1'),
  policy_version: z.literal('openrouter-public-v1'),
  disclosure: z.string().max(2000),
  authorization: z.object({ id: z.uuid(), policy: cloudPolicySchema }).nullable(),
  billing_reservations: z.array(z.unknown()),
});
export type CloudStatus = z.infer<typeof cloudStatusSchema>;
export const cloudFields = [
  ['upstream_provider', 'upstream', 'Identificatorul exact al furnizorului din amonte'],
  ['input_usd_per_million', 'input_price', 'Preț maxim intrare · USD / milion tokenuri'],
  ['output_usd_per_million', 'output_price', 'Preț maxim ieșire · USD / milion tokenuri'],
  ['request_usd', 'request_budget', 'Rezervare maximă / solicitare · USD'],
  ['daily_usd', 'daily_budget', 'Rezervări maxime / zi UTC · USD'],
] as const;
export type CloudDraft = Pick<CloudPolicy, (typeof cloudFields)[number][0]>;
export function cloudDraft(policy: CloudPolicy | null): CloudDraft {
  return policy
    ? {
        upstream_provider: policy.upstream_provider,
        input_usd_per_million: policy.input_usd_per_million,
        output_usd_per_million: policy.output_usd_per_million,
        request_usd: policy.request_usd,
        daily_usd: policy.daily_usd,
      }
    : {
        upstream_provider: '',
        input_usd_per_million: '1',
        output_usd_per_million: '4',
        request_usd: '0.01',
        daily_usd: '0.50',
      };
}
export function cloudSubmission(data: FormData) {
  return {
    version: 'openrouter-public-v1',
    ...Object.fromEntries(
      cloudFields.map(([field, input]) => [field, String(data.get(input) ?? '')]),
    ),
    acknowledged_public_cloud: data.has('cloud'),
    acknowledged_upstream_processing: data.has('upstream_ack'),
    acknowledged_cost: data.has('cost'),
    acknowledged_provider_policy_limits: data.has('limits'),
  };
}
export function cloudSaveConfirmed(
  result: unknown,
  state: CloudStatus,
  submitted: ReturnType<typeof cloudSubmission>,
) {
  const response = z
    .object({ id: z.literal('openrouter'), authorization_id: z.uuid() })
    .safeParse(result);
  const active = state.authorization;
  return (
    response.success &&
    active !== null &&
    active.id === response.data.authorization_id &&
    Object.entries(submitted).every(
      ([key, value]) => active.policy[key as keyof CloudPolicy] === value,
    )
  );
}
