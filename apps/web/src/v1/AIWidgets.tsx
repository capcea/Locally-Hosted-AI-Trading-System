import { useState } from 'react';
import { BrainCircuit, Code, Sparkles, MessageCircle, ShieldQuestion } from 'lucide-react';
import type { Binding, Model, Status } from '../ai/api';
import { roles, roleLabels, verified } from '../ai/api';
import { offerAIQuestion } from '../ai/draft';
import { useAuth } from '../auth/AuthProvider';
import { Link, navigate } from '../navigation/history';
import { CardTitle, StatusPill } from './components';
import { useOwnedRead } from './data';

export function AIRoles({
  models,
  bindings,
  status,
}: {
  models: Model[];
  bindings: Binding[];
  status: Status | null;
}) {
  const icons = [BrainCircuit, Code, ShieldQuestion, MessageCircle];
  return (
    <aside className="panel v1-ai-roles" aria-label="Modele și roluri AI" id="ai-roles">
      <CardTitle title="Modele și roluri" icon={BrainCircuit} />
      <div className="v1-role-list">
        {roles.map((role, index) => {
          const Icon = icons[index],
            binding = bindings.find((b) => b.role === role),
            model = models.find((m) => m.id === binding?.model_id);
          const current = Boolean(model && verified(model));
          return (
            <article key={role}>
              <span className="v1-icon">
                <Icon size={19} aria-hidden="true" />
              </span>
              <div>
                <h3>{role}</h3>
                <p>{roleLabels[role]}</p>
                <strong>{model?.name ?? 'Niciun model atribuit'}</strong>
                <StatusPill tone={current ? 'positive' : 'neutral'}>
                  {current ? 'Verificare curentă' : 'Neverificat / indisponibil'}
                </StatusPill>
                {current && <small>Expiră: {model?.verified_until}</small>}
              </div>
            </article>
          );
        })}
      </div>
      <h3>Limite și consum</h3>
      <p>
        {status
          ? `${status.limits.hourly_owner} solicitări/oră · ${status.limits.hourly_role}/rol/oră · ${status.limits.global_concurrency} simultane`
          : 'UNKNOWN · limitele nu pot fi citite.'}
      </p>
      <p>
        Consumul fiecărei analize este în metadatele sale. Totalul lunar și starea GPU nu sunt
        confirmate.
      </p>
      <Link href="/setari/ai">Revizuiește configurația AI</Link>
    </aside>
  );
}

export function AIQuickCard() {
  const { session } = useAuth();
  const status = useOwnedRead<Status>('/ai/status', 10000),
    models = useOwnedRead<Model[]>('/ai/models', 10000),
    bindings = useOwnedRead<Binding[]>('/ai/routes', 10000);
  const [question, setQuestion] = useState('');
  const binding = bindings.data?.find((b) => b.role === 'RESEARCH'),
    model = models.data?.find((m) => m.id === binding?.model_id);
  const ready =
    session?.state === 'FULL' &&
    session.user.role === 'OWNER' &&
    status.data?.configured &&
    status.data.worker_state === 'OBSERVED_RECENTLY' &&
    model &&
    verified(model);
  return (
    <section className="panel v1-ai-quick">
      <CardTitle title="Asistent AI" icon={Sparkles}>
        <StatusPill>{ready ? 'Model verificat' : 'Neconfigurat / neverificat'}</StatusPill>
      </CardTitle>
      <p>Analizează dovezi, propune idei și caută puncte slabe. Răspunsurile rămân neverificate.</p>
      <div className="v1-model-summary">
        <span>Model · Research</span>
        <strong>{model?.name ?? 'Niciun model confirmat'}</strong>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (ready && session) {
            offerAIQuestion(session.user.id, question);
            navigate('/testeaza/ai');
          }
        }}
      >
        <label className="sr-only" htmlFor="home-ai-question">
          Întrebare pentru revizuire în AI Center
        </label>
        <textarea
          id="home-ai-question"
          maxLength={4000}
          minLength={3}
          required
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Întreabă despre o ipoteză sau un rezultat…"
          disabled={!ready}
        />
        <div className="v1-suggestions">
          {[
            ['Dovezi lipsă', 'Ce dovezi lipsesc?'],
            ['Idee de test', 'Propune o ipoteză testabilă'],
            ['Critică ipoteza', 'Critică o presupunere'],
            ['Explică un indicator', 'Explică un indicator'],
          ].map(([label, question]) => (
            <button
              type="button"
              className="secondary-button"
              key={label}
              disabled={!ready}
              onClick={() => setQuestion(question)}
            >
              {label}
            </button>
          ))}
        </div>
        <button className="v1-violet-button" disabled={!ready} aria-describedby="home-ai-reason">
          <Sparkles size={17} aria-hidden="true" />
          Analizează cu AI
        </button>
      </form>
      <p id="home-ai-reason">
        {ready
          ? 'Urmează revizuirea contextului și acordul explicit în AI Center. Nu trimitem automat întrebarea.'
          : 'AI indisponibil. Sunt necesare un model privat verificat, un worker observat recent și acces de proprietar cu MFA.'}
      </p>
      <Link href={session?.state === 'FULL' ? '/setari/ai' : '/autentificare'}>
        {session?.state === 'FULL'
          ? 'Configurează modele și roluri'
          : 'Autentificare pentru configurare'}
      </Link>
    </section>
  );
}
