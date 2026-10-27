import { useState } from 'react';
import {
  BookOpen,
  Box,
  Braces,
  ChartNoAxesCombined,
  Check,
  CircleHelp,
  Clock3,
  Database,
  Fingerprint,
  Layers3,
  LockKeyhole,
  Network,
  Search,
  Server,
  ShieldCheck,
  ShieldOff,
  Workflow,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { Overview, Service } from './api';
import { locale, ro } from './locale';
const serviceIcons: Record<string, LucideIcon> = {
  api: Braces,
  postgres: Database,
  redis: Layers3,
  storage: Box,
  mt5: ChartNoAxesCombined,
  ctrader: Network,
  ollama: Workflow,
  executor: ShieldOff,
};

function Badge({ children, tone = '' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function ServiceRow({ service, stale }: { service: Service; stale: boolean }) {
  const Icon = serviceIcons[service.id] || Server;
  return (
    <div className="service-row">
      <div className="service-icon">
        <Icon size={19} />
      </div>
      <div className="service-copy">
        <strong>{service.name}</strong>
        <span>{service.detail}</span>
      </div>
      <span className={`service-status ${stale ? 'stale' : service.status.toLowerCase()}`}>
        <i />
        {stale ? 'Neverificat' : ro.statuses[service.status]}
      </span>
    </div>
  );
}

export function InfrastructurePage({ data, stale }: { data: Overview; stale: boolean }) {
  const [filter, setFilter] = useState('');
  const services = data.services.filter((service) =>
    `${service.name} ${service.detail}`
      .toLocaleLowerCase(locale)
      .includes(filter.toLocaleLowerCase(locale)),
  );
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">DEPENDENȚE & INTEGRĂRI</span>
        <h2>
          Conexiuni explicite.
          <br />
          <span>Stare verificată.</span>
        </h2>
        <p>
          Fiecare serviciu își raportează starea. O dependență indisponibilă blochează verificarea
          de pregătire.
        </p>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Servicii</h2>
          <label className="search-box">
            <Search size={16} />
            <input
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Caută un serviciu…"
              aria-label="Caută un serviciu"
            />
          </label>
        </div>
        <div className="full-service-list">
          {services.map((service) => (
            <ServiceRow key={service.id} service={service} stale={stale} />
          ))}
          {services.length === 0 && <p className="no-results">Niciun serviciu găsit.</p>}
        </div>
        <div className="panel-bottom">
          <span>
            <Clock3 size={14} /> Actualizare automată la 15 secunde. Starea devine neverificată la
            pierderea conexiunii.
          </span>
        </div>
      </section>
      <div className="info-callout">
        <CircleHelp size={20} />
        <div>
          <h3>Pornire locală</h3>
          <p>
            Rulează <code>make dev</code> pentru PostgreSQL, Redis, stocare și aplicație. MT5,
            cTrader și gateway-ul AI necesită implementarea etapelor următoare.
          </p>
        </div>
      </div>
    </>
  );
}

export function GovernancePage({ data }: { data: Overview }) {
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">LIMITE DE ÎNCREDERE</span>
        <h2>
          Siguranța este
          <br />
          <span>o proprietate a sistemului.</span>
        </h2>
        <p>Administrarea necesită autentificare și MFA. Nu există un flux de activare live.</p>
      </div>
      <div className="governance-grid">
        {[
          {
            icon: ShieldCheck,
            name: 'Execuție refuzată',
            value: data.safety.executor_capability,
            text: 'API-ul și contractul executorului refuză toate ordinele. Variabilele de mediu nu pot activa tranzacționarea.',
          },
          {
            icon: Fingerprint,
            name: 'Aprobări umane',
            value: 'IDENTITATE & MFA · FAZA 1',
            text: 'Conturile și configurările sunt protejate prin autentificare, roluri și MFA. Aprobările pentru execuție live nu sunt implementate.',
          },
          {
            icon: LockKeyhole,
            name: 'Cercetare izolată',
            value: 'EXECUȚIE COD DEZACTIVATĂ',
            text: 'Nu este instalat un runner pentru cod generat. Niciun agent nu poate executa strategii în acest mediu.',
          },
          {
            icon: BookOpen,
            name: 'Politici verificate',
            value: 'NEVERIFICATE',
            text: 'FTMO, FundedNext și The5ers necesită politici versionate pentru programul și contul exact. Nicio permisiune de trading nu este presupusă.',
          },
        ].map(({ icon: Icon, name, value, text }) => (
          <section className="panel rule-card" key={name}>
            <div className="rule-icon">
              <Icon size={23} />
            </div>
            <h3>{name}</h3>
            <Badge>{value}</Badge>
            <p>{text}</p>
          </section>
        ))}
      </div>
      <section className="panel block-reasons">
        <div className="panel-heading">
          <h2>Motivele blocării execuției</h2>
          <Badge tone="amber">4 controale active</Badge>
        </div>
        {data.safety.reasons.map((reason) => (
          <div key={reason}>
            <LockKeyhole size={16} />
            <code>{reason}</code>
            <Check size={17} />
          </div>
        ))}
      </section>
    </>
  );
}

export function RoadmapPage({ data }: { data: Overview }) {
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">DEZVOLTARE ÎN ETAPE</span>
        <h2>
          Fiecare etapă are
          <br />
          <span>o condiție de trecere.</span>
        </h2>
        <p>
          Extindem platforma numai după verificarea etapei curente. Conectarea reală și rezultatele
          nu sunt presupuse.
        </p>
      </div>
      <div className="roadmap-list">
        {data.roadmap.map((phase) => (
          <section
            className={`panel roadmap-item ${phase.status === 'CURRENT' ? 'current' : ''}`}
            key={phase.number}
          >
            <span className="phase-number">{String(phase.number).padStart(2, '0')}</span>
            <div>
              <h3>{phase.title}</h3>
              <p>{phase.acceptance}</p>
            </div>
            <Badge tone={phase.status === 'CURRENT' ? 'green' : ''}>
              {phase.number <= 5
                ? 'Implementat · acceptare în rapoarte'
                : 'Planificat · indisponibil'}
            </Badge>
          </section>
        ))}
      </div>
    </>
  );
}
