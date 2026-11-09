import { z } from 'zod';
import { aiErrors } from './copy';

const diagnostic = z.strictObject({
  http_status: z.number().int().min(100).max(599),
  operation: z.enum(['MODEL_CATALOG', 'MODEL_METADATA', 'COMPLETION', 'PROVIDER_REQUEST']),
});
const operations = {
  MODEL_CATALOG: 'Citirea catalogului de modele',
  MODEL_METADATA: 'Citirea detaliilor modelului',
  COMPLETION: 'Solicitarea de generare',
  PROVIDER_REQUEST: 'Solicitarea către furnizor',
};

export function ProviderError({ error, metadata }: { error: string; metadata: unknown }) {
  const record = metadata && typeof metadata === 'object' ? metadata : {};
  const parsed = diagnostic.safeParse(
    'provider_diagnostic' in record ? record.provider_diagnostic : null,
  );
  const code = /^[A-Z_0-9]{1,80}$/.test(error) ? error : 'AI_OPERATION_FAILED';
  const transport = error.startsWith('AI_PROVIDER_');
  return (
    <div aria-label="Explicația eșecului AI">
      <p role="status">
        {aiErrors[error] ?? 'Nu putem confirma rezultatul solicitării.'} Solicitarea nu poate fi
        folosită ca rezultat. Verifică modelul, autorizarea și contextul înainte de o nouă
        solicitare. Cod diagnostic: <code>{code}</code>
      </p>
      {parsed.success ? (
        <div aria-label="Diagnostic refuz furnizor">
          <dl>
            <dt>Status HTTP primit</dt>
            <dd>{parsed.data.http_status}</dd>
            <dt>Etapa solicitării</dt>
            <dd>{operations[parsed.data.operation]}</dd>
          </dl>
          <p>
            {parsed.data.operation === 'MODEL_METADATA' && parsed.data.http_status === 404
              ? 'Adresa pentru detaliile modelului nu a fost găsită. Verifică identificatorul exact autor/model și ruta API.'
              : [400, 404, 422].includes(parsed.data.http_status)
                ? 'Furnizorul a refuzat resursa, formatul sau parametrii cererii. Aceste date nu identifică singure parametrul care a fost refuzat.'
                : 'Statusul HTTP și etapa sunt observații ale transportului, nu dovadă că modelul a executat generarea.'}
          </p>
          <p>
            {['MODEL_CATALOG', 'MODEL_METADATA'].includes(parsed.data.operation)
              ? 'Refuzul a apărut la citirea informațiilor, înaintea solicitării de generare din această etapă.'
              : parsed.data.operation === 'COMPLETION'
                ? 'Nu presupunem că un refuz înseamnă cost zero. Verifică evidența furnizorului.'
                : 'Etapa exactă nu este disponibilă; nu deducem dacă a avut loc generarea.'}{' '}
            Nu retrimitem automat solicitarea și nu schimbăm furnizorul sau politica de
            confidențialitate.
          </p>
        </div>
      ) : (
        transport && (
          <p>
            Statusul HTTP și etapa refuzului nu au fost păstrate pentru această solicitare. Motivul
            exact nu poate fi recuperat din codul generic. Nu repetăm automat o cerere cu posibile
            costuri.
          </p>
        )
      )}
    </div>
  );
}
