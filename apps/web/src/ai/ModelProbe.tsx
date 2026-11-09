import { useId } from 'react';
import type { Connection } from './api';

export function probeDisabledReason(
  busy: boolean,
  connection: Connection | undefined,
  costApproved: boolean,
): string {
  if (busy) return 'Așteaptă finalizarea operațiunii în curs.';
  if (!connection) return 'Conexiunea modelului nu poate fi confirmată. Reîncarcă registrul AI.';
  if (!connection.enabled) return 'Activează conexiunea modelului înainte de verificare.';
  if (connection.provider === 'OPENROUTER') {
    if (!connection.credential_configured)
      return 'Configurează cheia OpenRouter pe server înainte de verificare.';
    if (!costApproved) return 'Bifează aprobarea costului pentru a putea verifica acest model.';
  }
  return '';
}

export function ModelProbe({
  modelName,
  connection,
  busy,
  costApproved,
  setCostApproved,
  submit,
  standingAuthorized = false,
}: {
  modelName: string;
  connection: Connection | undefined;
  busy: boolean;
  costApproved: boolean;
  setCostApproved: (approved: boolean) => void;
  submit: () => void;
  standingAuthorized?: boolean;
}) {
  const reasonId = useId();
  const reason = probeDisabledReason(busy, connection, costApproved || standingAuthorized);
  const cloud = connection?.provider === 'OPENROUTER';
  return (
    <div role="group" aria-label={`Verificare model ${modelName}`}>
      {cloud && !standingAuthorized && (
        <label>
          <input
            type="checkbox"
            checked={costApproved}
            disabled={busy}
            onChange={(event) => setCostApproved(event.target.checked)}
          />
          Aprob o verificare OpenRouter cu o singură completare structurată, cu posibile costuri în
          limita autorizată.
        </label>
      )}
      <p id={reasonId}>
        {reason ||
          (standingAuthorized
            ? 'Verificare acoperită de autorizarea permanentă și limitele sale. Pornește numai când apeși butonul.'
            : cloud
              ? 'Solicitarea cu posibile costuri pornește numai când apeși butonul de verificare.'
              : 'Verificarea folosește conexiunea privată aprobată. Nu confirmă disponibilitatea înainte de răspuns.')}
      </p>
      <button
        type="button"
        disabled={Boolean(reason)}
        aria-describedby={reasonId}
        onClick={() => {
          if (!reason) submit();
        }}
      >
        Verifică printr-o solicitare reală
      </button>
    </div>
  );
}
