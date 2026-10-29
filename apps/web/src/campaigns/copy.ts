export const campaignErrors: Record<string, string> = {
  MODEL_UNAVAILABLE:
    'Lipsește un model Research sau Critic verificat. Configurează modelele; nu folosim automat o fixtură.',
  MODEL_UNAVAILABLE_OR_AUTHORIZATION_REVOKED:
    'Verificarea modelului sau autorizarea conexiunii nu mai este valabilă. Cercetarea se oprește.',
  CAMPAIGN_CONCURRENCY_LIMIT:
    'Există deja o campanie activă în limita permisă. Verifică activitatea înainte de a porni alta.',
  CAMPAIGN_RUNTIME_BUDGET_EXHAUSTED:
    'Timpul autorizat a expirat. Reluarea nu extinde automat bugetul.',
  CAMPAIGN_EXPERIMENT_OR_RESOURCE_BUDGET_EXHAUSTED:
    'Limita de teste, timp sau stocare a fost atinsă. Nu extindem automat campania.',
  CAMPAIGN_FINAL_HOLDOUT_PROHIBITED: 'Evaluarea finală protejată nu este accesibilă campaniilor.',
  EVALUATION_INTERVAL_ALREADY_EXPOSED_NO_RETUNING:
    'Acest interval de validare a fost deja folosit. Nu îl reutilizăm ca dovadă independentă.',
  UNTRUSTED_CAMPAIGN_MODEL_OUTPUT_REFUSED:
    'Propunerea modelului nu respectă limitele autorizate. Nu a fost transformată într-un test.',
  CAMPAIGN_NOT_ACTIVE: 'Campania nu permite lucru nou. Verifică pauza, oprirea sau autorizarea.',
};
export const campaignStates: Record<string, string> = {
  DRAFT: 'Ciornă',
  AWAITING_APPROVAL: 'Așteaptă revizuirea proprietarului',
  QUEUED: 'În așteptare',
  PLANNING: 'Pregătește planul',
  TESTING: 'Test istoric în desfășurare',
  EVALUATING: 'Verifică dovezile',
  CRITIQUING: 'Revizuire critică',
  READY_FOR_NEXT_ITERATION: 'O nouă verificare este justificată',
  COMPLETED: 'Cercetare încheiată',
  STOPPED: 'Cercetare oprită',
  FAILED: 'Cercetare eșuată',
  UNKNOWN: 'Stare neconfirmată · verifică activitatea',
};
export const decisions: Record<string, string> = {
  INSUFFICIENT_EVIDENCE: 'Dovezi insuficiente',
  REJECTED: 'Ipoteza nu îndeplinește criteriile',
  NEEDS_MORE_VALIDATION: 'Sunt necesare verificări suplimentare',
  RESEARCH_CANDIDATE: 'Merită cercetare suplimentară · fără aprobare de tranzacționare',
};
export const evaluationReasons: Record<string, string> = {
  NO_BOUNDED_CANONICAL_TRIAL_EVIDENCE: 'Nu există dovezi complete dintr-un test stocat.',
  SCREEN_OR_UNVALIDATED_RISK_RESULT: 'Rezultatul exploratoriu nu confirmă verificarea riscului.',
  CANONICAL_METRIC_MISSING: 'O măsură necesară nu este disponibilă.',
  INSUFFICIENT_TRADE_SAMPLE: 'Sunt prea puține tranzacții pentru metodologia aleasă.',
  NONPOSITIVE_NET_AFTER_MODELED_COSTS: 'Rezultatul după costurile modelate nu este pozitiv.',
  DECLARED_RESEARCH_DRAWDOWN_CRITERION_EXCEEDED:
    'Scăderea depășește criteriul declarat de cercetare.',
  EXPLORATORY_UNCERTAINTY_NOT_RESOLVED: 'Incertitudinea statistică rămâne mare sau nemăsurată.',
  COST_EVIDENCE_MISSING: 'Lipsește dovada costurilor modelate.',
  TEMPORAL_SAMPLE_TOO_SHORT_FOR_RATIOS: 'Perioada este prea scurtă pentru indicatori anualizați.',
  DATA_COVERAGE_INCOMPLETE_OR_UNKNOWN: 'Acoperirea datelor este incompletă sau necunoscută.',
  COST_STRESS_NOT_TESTED: 'Nu au fost testate costuri mai nefavorabile.',
  IN_SAMPLE_ONLY_NOT_INDEPENDENT_OOS: 'Datele sunt de descoperire, nu validare independentă.',
  CHRONOLOGICAL_STABILITY_NOT_ESTABLISHED: 'Stabilitatea în perioade succesive nu este confirmată.',
  SYNTHETIC_FIXTURE_CANNOT_ESTABLISH_REAL_RESEARCH_CANDIDACY:
    'Fixtura verifică infrastructura, nu o oportunitate reală.',
  RESEARCH_ONLY_NO_PAPER_OR_TRADING_AUTHORITY:
    'Concluzia nu autorizează paper trading sau ordine externe.',
};
