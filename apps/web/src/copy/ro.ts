export const jobLabels: Record<string, string> = {
  QUEUED: 'În așteptare',
  RUNNING: 'În lucru',
  RETRY: 'Se reia după întrerupere',
  SUCCEEDED: 'Test finalizat',
  FAILED: 'Test oprit din cauza unei probleme',
  CANCELLED: 'Anulare confirmată',
};
export const strategyLabels: Record<string, string> = {
  EMA_TREND: 'Urmărirea tendinței',
  MA_CROSS: 'Încrucișarea mediilor',
  DONCHIAN: 'Depășirea intervalului recent',
  BOLLINGER: 'Revenire spre media prețului',
  RSI: 'Revenire după mișcări accentuate',
  ATR_BREAKOUT: 'Mișcare peste variația recentă',
  OPENING_RANGE: 'Depășirea intervalului de deschidere',
  SESSION_MOMENTUM: 'Direcția prețului în sesiune',
};
export const phaseLabels: Record<string, string> = {
  DISCOVERY: 'Descoperire · date folosite la explorare',
  CALIBRATION: 'Calibrare · date folosite la alegerea setărilor',
  VALIDATION: 'Evaluare ulterioară conform protocolului',
  FINAL_HOLDOUT: 'Evaluare finală autorizată separat',
};
export const sourceLabels: Record<string, string> = {
  SYNTHETIC_TEST_FIXTURE: 'Date sintetice',
  USER_SUPPLIED: 'Fișier furnizat de tine · istoric declarat',
  PUBLIC_PROVIDER: 'Date din sursă publică',
  SIMULATED: 'Execuție simulată',
  DEMO_READ_ONLY: 'Observație demo · numai citire',
};
export const researchErrors: Record<string, string> = {
  DATASET_ACCOUNT_SCOPE_MISMATCH:
    'Datele și configurația nu aparțin aceluiași cont permis. Alege date compatibile.',
  DATASET_NOT_VALID_OR_PIN_CHANGED:
    'Datele nu mai corespund versiunii admise. Verifică setul și versiunea.',
  DATASET_MANIFEST_REGISTRY_MISMATCH:
    'Integritatea datelor nu poate fi confirmată. Testul nu poate continua.',
  FUTURE_OR_UNAVAILABLE_MARKET_OBSERVATION:
    'Datele nu erau disponibile la momentul deciziei. Nu le folosim pentru a produce un rezultat favorabil.',
  BAR_HIGH_LOW_NOT_YET_AVAILABLE: 'Bara de preț nu era încă disponibilă la momentul deciziei.',
  INSUFFICIENT_ADMITTED_WARMUP:
    'Lipsesc observații anterioare necesare strategiei. Alege o perioadă cu pregătire suficientă.',
  RESEARCH_MARGIN_UNVERIFIED:
    'Marja necesară nu este verificată. Revizuiește configurația contului.',
  REPLAY_SYMBOL_OR_CALENDAR_UNVERIFIED: 'Simbolul sau calendarul nu corespunde datelor admise.',
  AUTOMATED_RESEARCH_REQUIRES_EXPLICIT_VERIFIED_POLICY_PERMISSION:
    'Politica verificată nu permite explicit strategia automatizată. Revizuiește politica; nu o declarăm manuală.',
  SOURCE_POLICY_VERSION_CHANGED:
    'Politica revizuită s-a schimbat. Pregătește un test nou cu versiunea curentă.',
  SOURCE_RISK_PROFILES_CHANGED: 'Limitele revizuite s-au schimbat. Verifică noua configurație.',
  SOURCE_RISK_APPROVAL_REVOKED:
    'Aprobarea configurației a fost retrasă. Revizuiește siguranța contului.',
  RESEARCH_SOFTWARE_VERSION_CHANGED: 'Versiunea software s-a schimbat. Revizuiește o rulare nouă.',
  FINAL_HOLDOUT_ACCESS_DENIED:
    'Perioada este protejată pentru evaluarea finală. Folosește fluxul separat de autorizare.',
  REVIEW_SOURCE_RISK_CONFIGURATION_AND_STOP:
    'Contul are o oprire sau o configurație incompletă. Revizuiește starea, fără deblocare automată.',
};
