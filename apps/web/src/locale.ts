// Central vocabulary; Romanian is the default locale. Add a matching English catalog later.
export const ro = {
  management: 'Cont & administrare',
  market: 'Date de piață',
  broker: 'Broker & simulator',
  riskCenter: 'Centru de risc',
  research: 'Laborator de strategii',
  overview: 'Prezentare generală',
  infrastructure: 'Infrastructură',
  governance: 'Siguranță & guvernanță',
  roadmap: 'Plan de implementare',
  statuses: {
    HEALTHY: 'Disponibil',
    UNAVAILABLE: 'Indisponibil',
    NOT_CONFIGURED: 'Neconfigurat',
    DISABLED: 'Dezactivat',
    PENDING_IMPLEMENTATION: 'Planificat',
  },
} as const;
export const locale = 'ro-RO';
